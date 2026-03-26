#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VALID_OUTCOMES = {"continue", "completed", "hard_blocked", "failed"}


class DriverError(Exception):
    pass


@dataclass
class SessionInput:
    operator: str | None
    goal_file: Path | None
    handoff_file: Path | None
    runtime_guide_file: Path | None
    open_questions_dir: Path | None
    open_answers_dir: Path | None
    additional_context_files: list[Path]
    additional_instructions: str | None
    session_result_file: Path | None


@dataclass
class SessionRunArtifacts:
    run_dir: Path
    prompt_file: Path
    events_file: Path
    last_message_file: Path
    metadata_file: Path
    session_result_file: Path
    command: list[str]


@dataclass
class HandoffReservation:
    queued_path: Path
    inflight_path: Path
    history_path: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="meta-agent",
        description="Thin driver for agent-agnostic autonomous sessions.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_session = subparsers.add_parser(
        "run-session",
        help="Run one autonomous session through an agent adapter.",
    )
    run_session.add_argument("--agent", required=True, help="Adapter name, for example: codex")
    run_session.add_argument("--repo", required=True, help="Repository root for the session")
    run_session.add_argument(
        "--operator",
        help="Human operator name for this session; overrides the value in session-input.json",
    )
    run_session.add_argument(
        "--input",
        required=True,
        help="Path to a session-input.json file",
    )
    run_session.add_argument(
        "--run-dir",
        required=True,
        help="Directory for prompt, logs, and run-specific outputs",
    )
    run_session.add_argument(
        "--dry-run",
        action="store_true",
        help="Render prompt and command without invoking the agent",
    )

    run_loop = subparsers.add_parser(
        "run-loop",
        help="Continuously run autonomous sessions until blocked or out of work.",
    )
    run_loop.add_argument("--agent", required=True, help="Adapter name, for example: codex")
    run_loop.add_argument("--repo", required=True, help="Repository root for the loop")
    run_loop.add_argument(
        "--operator",
        help="Human operator name injected into every session in the loop",
    )
    run_loop.add_argument(
        "--goal-file",
        default="GOAL.md",
        help="Repo-relative goal file used when no queued handoff exists on the first session",
    )
    run_loop.add_argument(
        "--runtime-guide-file",
        default=".meta-agent/AGENT-RUNTIME.md",
        help="Repo-relative runtime guide file",
    )
    run_loop.add_argument(
        "--questions-dir",
        default="questions",
        help="Repo-relative directory for asynchronous human questions",
    )
    run_loop.add_argument(
        "--answers-dir",
        default="answers",
        help="Repo-relative directory where humans write answers for future sessions",
    )
    run_loop.add_argument(
        "--runs-dir",
        default=".meta-agent/runs",
        help="Repo-relative directory where per-session run artifacts are stored",
    )
    run_loop.add_argument(
        "--additional-context-file",
        action="append",
        default=[],
        help="Additional repo-relative context file to include in every session",
    )
    run_loop.add_argument(
        "--additional-instructions",
        help="Extra instructions appended to every generated session prompt",
    )
    run_loop.add_argument(
        "--max-sessions",
        type=int,
        default=20,
        help="Maximum number of sessions to run before stopping",
    )
    run_loop.add_argument(
        "--dry-run",
        action="store_true",
        help="Render only the first planned session without invoking the agent",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run-session":
        try:
            return run_session(args)
        except DriverError as exc:
            print(f"meta-agent: {exc}", file=sys.stderr)
            return 1

    if args.command == "run-loop":
        try:
            return run_loop(args)
        except DriverError as exc:
            print(f"meta-agent: {exc}", file=sys.stderr)
            return 1

    parser.error(f"unsupported command: {args.command}")
    return 2


def run_session(args: argparse.Namespace) -> int:
    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        raise DriverError(f"repo does not exist: {repo}")

    input_file = Path(args.input).expanduser().resolve()
    if not input_file.is_file():
        raise DriverError(f"session input file does not exist: {input_file}")

    run_dir = Path(args.run_dir).expanduser().resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    session_input = load_session_input(input_file, repo, operator_override=args.operator)
    result, artifacts = execute_session(
        agent=args.agent,
        repo=repo,
        session_input=session_input,
        input_file=input_file,
        run_dir=run_dir,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print(f"Prompt written to {artifacts.prompt_file}")
        print(f"Driver metadata written to {artifacts.metadata_file}")
        print("Planned command:")
        print(shell_join(artifacts.command))
        return 0

    print_human_feedback(repo, result, session_input.open_answers_dir)
    print(f"Session completed. Result file: {artifacts.session_result_file}")
    return 0


def run_loop(args: argparse.Namespace) -> int:
    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        raise DriverError(f"repo does not exist: {repo}")

    if args.max_sessions <= 0:
        raise DriverError("--max-sessions must be greater than zero")

    goal_file = resolve_optional_repo_file(repo, args.goal_file)
    runtime_guide_file = resolve_optional_repo_file(repo, args.runtime_guide_file)
    questions_dir = resolve_optional_repo_dir(repo, args.questions_dir)
    answers_dir = resolve_optional_repo_dir(repo, args.answers_dir)
    additional_context_files = [
        resolve_required_repo_file(repo, item) for item in args.additional_context_file
    ]
    runs_dir = (repo / args.runs_dir).resolve()
    runs_dir.mkdir(parents=True, exist_ok=True)
    handoff_dirs = ensure_handoff_dirs(repo)
    recover_inflight_handoffs(repo, runs_dir, handoff_dirs)

    session_count = 0
    used_goal_without_handoff = False

    while session_count < args.max_sessions:
        current_handoff = select_queued_handoff(handoff_dirs["queue"])
        if current_handoff is None:
            if used_goal_without_handoff or goal_file is None:
                print("No queued handoff remains. Loop stopped.")
                return 0
            used_goal_without_handoff = True

        session_count += 1
        run_dir = allocate_run_dir(runs_dir, session_count)
        reservation: HandoffReservation | None = None
        current_session_handoff = current_handoff
        if current_handoff is not None and not args.dry_run:
            reservation = reserve_handoff(current_handoff, handoff_dirs)
            current_session_handoff = reservation.inflight_path

        session_input_payload = build_loop_session_input_payload(
            repo=repo,
            goal_file=goal_file,
            handoff_file=current_session_handoff,
            runtime_guide_file=runtime_guide_file,
            questions_dir=questions_dir,
            answers_dir=answers_dir,
            operator=args.operator,
            additional_context_files=additional_context_files,
            additional_instructions=args.additional_instructions,
            run_dir=run_dir,
        )
        input_file = run_dir / "session-input.json"
        input_file.parent.mkdir(parents=True, exist_ok=True)
        input_file.write_text(json.dumps(session_input_payload, indent=2) + "\n", encoding="utf-8")
        session_input = load_session_input(input_file, repo)

        selected = (
            display_repo_relative(repo, current_session_handoff)
            if current_session_handoff
            else "<goal-only>"
        )
        print(f"Starting session {session_count}: {selected}")

        try:
            result, artifacts = execute_session(
                agent=args.agent,
                repo=repo,
                session_input=session_input,
                input_file=input_file,
                run_dir=run_dir,
                dry_run=args.dry_run,
                extra_metadata=build_handoff_metadata(repo, reservation),
            )
        except DriverError:
            if reservation is not None:
                recover_single_inflight_handoff(repo, reservation, run_dir)
            raise

        if args.dry_run:
            print(f"Prompt written to {artifacts.prompt_file}")
            print(f"Driver metadata written to {artifacts.metadata_file}")
            print("Planned command:")
            print(shell_join(artifacts.command))
            return 0

        if reservation is not None:
            archive_reserved_handoff(reservation)

        outcome = result["outcome"]
        print(f"Session {session_count} outcome: {outcome}")
        print_human_feedback(repo, result, answers_dir)

        if outcome == "failed":
            raise DriverError(
                f"session {session_count} reported failed; see {artifacts.session_result_file}"
            )

        if outcome == "hard_blocked":
            print(f"Loop stopped: {result['block_reason']}")
            return 2

        queued_after = list_queued_handoffs(handoff_dirs["queue"])
        if outcome == "continue" and not queued_after:
            raise DriverError(
                f"session {session_count} reported continue but no queued handoff remains"
            )

        if queued_after:
            continue

        if outcome == "completed":
            print("No queued handoff remains. Loop completed.")
            return 0

    print(f"Reached session limit ({args.max_sessions}). Loop stopped.")
    return 3


def load_session_input(
    input_file: Path, repo: Path, operator_override: str | None = None
) -> SessionInput:
    try:
        raw = json.loads(input_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DriverError(f"invalid JSON in session input: {exc}") from exc

    if not isinstance(raw, dict):
        raise DriverError("session input must be a JSON object")

    def resolve_repo_path(key: str) -> Path | None:
        value = raw.get(key)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise DriverError(f"{key} must be a non-empty string when provided")
        return (repo / value).resolve()

    additional_context_files: list[Path] = []
    raw_context_files = raw.get("additional_context_files", [])
    if raw_context_files is None:
        raw_context_files = []
    if not isinstance(raw_context_files, list):
        raise DriverError("additional_context_files must be an array when provided")
    for item in raw_context_files:
        if not isinstance(item, str) or not item.strip():
            raise DriverError("additional_context_files entries must be non-empty strings")
        additional_context_files.append((repo / item).resolve())

    additional_instructions = raw.get("additional_instructions")
    if additional_instructions is not None and not isinstance(additional_instructions, str):
        raise DriverError("additional_instructions must be a string when provided")

    operator = raw.get("operator")
    if operator is not None and (not isinstance(operator, str) or not operator.strip()):
        raise DriverError("operator must be a non-empty string when provided")
    if operator is not None:
        operator = operator.strip()
    if operator_override is not None:
        if not operator_override.strip():
            raise DriverError("--operator must be a non-empty string")
        operator = operator_override.strip()

    result = SessionInput(
        operator=operator,
        goal_file=resolve_repo_path("goal_file"),
        handoff_file=resolve_repo_path("handoff_file"),
        runtime_guide_file=resolve_repo_path("runtime_guide_file"),
        open_questions_dir=resolve_repo_path("open_questions_dir"),
        open_answers_dir=resolve_repo_path("open_answers_dir"),
        additional_context_files=additional_context_files,
        additional_instructions=additional_instructions,
        session_result_file=resolve_repo_path("session_result_file"),
    )

    if result.goal_file is None and result.handoff_file is None:
        raise DriverError("session input must provide at least one of goal_file or handoff_file")

    check_optional_path(result.goal_file, "goal_file")
    check_optional_path(result.handoff_file, "handoff_file")
    check_optional_path(result.runtime_guide_file, "runtime_guide_file")
    check_optional_dir(result.open_questions_dir, "open_questions_dir")
    check_optional_dir(result.open_answers_dir, "open_answers_dir")
    for path in result.additional_context_files:
        if not path.is_file():
            raise DriverError(f"additional context file does not exist: {path}")

    return result


def check_optional_path(path: Path | None, field_name: str) -> None:
    if path is not None and not path.is_file():
        raise DriverError(f"{field_name} does not exist: {path}")


def check_optional_dir(path: Path | None, field_name: str) -> None:
    if path is not None and not path.is_dir():
        raise DriverError(f"{field_name} does not exist: {path}")


def resolve_session_result_path(session_input: SessionInput, repo: Path, run_dir: Path) -> Path:
    if session_input.session_result_file is not None:
        return session_input.session_result_file

    return (run_dir / "session-result.json").resolve()


def resolve_optional_repo_file(repo: Path, value: str | None) -> Path | None:
    if value is None:
        return None
    path = (repo / value).resolve()
    return path if path.is_file() else None


def resolve_required_repo_file(repo: Path, value: str) -> Path:
    path = (repo / value).resolve()
    if not path.is_file():
        raise DriverError(f"required file does not exist: {path}")
    return path


def resolve_optional_repo_dir(repo: Path, value: str | None) -> Path | None:
    if value is None:
        return None
    path = (repo / value).resolve()
    return path if path.is_dir() else None


def build_prompt(repo: Path, session_input: SessionInput, session_result_file: Path) -> str:
    lines = [
        "# Autonomous Session",
        "",
        "You are running one autonomous session inside this repository.",
        "",
        f"- Repository root: `{repo}`",
        f"- Session result file: `{session_result_file}`",
        "",
        "Behavior rules:",
        "- Work autonomously. Do not stop just to wait for operator confirmation.",
        "- If you need human input, create one or more files under `questions/` and keep progressing as far as you can.",
        "- Only mark the session as `hard_blocked` when there is no meaningful work left without external input or access.",
        "- If follow-up work remains, create one or more handoff files under `handoff/`.",
        "- Before ending the session, execute the repository's standard session-end SOP if one exists.",
        "- Treat `session-result.json` as the final acknowledgement to the driver, not as a substitute for session-end cleanup.",
        "- Before ending the session, write the required JSON result file.",
        "",
        "Start by reading these context files if they exist:",
    ]

    if session_input.runtime_guide_file is not None:
        lines.append(f"- Runtime guide: `{display_repo_relative(repo, session_input.runtime_guide_file)}`")
    if session_input.goal_file is not None:
        lines.append(f"- Goal: `{display_repo_relative(repo, session_input.goal_file)}`")
    if session_input.handoff_file is not None:
        lines.append(f"- Current handoff: `{display_repo_relative(repo, session_input.handoff_file)}`")
    if session_input.open_questions_dir is not None:
        lines.append(
            f"- Existing open questions directory: `{display_repo_relative(repo, session_input.open_questions_dir)}`"
        )
    if session_input.open_answers_dir is not None:
        lines.append(
            f"- Existing human answers directory: `{display_repo_relative(repo, session_input.open_answers_dir)}`"
        )
    if session_input.operator is not None:
        lines.append(f"- Operator for this session: `{session_input.operator}`")
    for path in session_input.additional_context_files:
        lines.append(f"- Additional context: `{display_repo_relative(repo, path)}`")

    lines.extend(
        [
            "",
            "Write the session result as JSON with this schema:",
            "",
            "```json",
            "{",
            '  "outcome": "continue | completed | hard_blocked | failed",',
            '  "summary": "short plain-language summary",',
            '  "handoff_files": ["handoff/optional-file.md"],',
            '  "question_files": ["questions/optional-question.md"],',
            '  "block_reason": "required when outcome is hard_blocked"',
            "}",
            "```",
            "",
            "Rules for the result file:",
            "- `outcome` is required and must be one of the listed values.",
            "- `summary` is required.",
            "- `handoff_files` and `question_files` are optional arrays of repo-relative paths.",
            "- `block_reason` is optional unless `outcome` is `hard_blocked`.",
        ]
    )

    if session_input.operator is not None:
        lines.extend(
            [
                "",
                "Operator handling:",
                f"- The driver already provided the operator for this session: `{session_input.operator}`.",
                "- Use that exact value anywhere the session-end SOP requires `operator: <name>`.",
                "- Do not open a question just to ask for operator confirmation unless a repository rule explicitly requires a different operator value and explains why.",
            ]
        )

    if session_input.open_questions_dir is not None and session_input.open_answers_dir is not None:
        lines.extend(
            [
                "",
                "Question and answer handling:",
                f"- Human questions belong under `{display_repo_relative(repo, session_input.open_questions_dir)}`.",
                f"- Human answers belong under `{display_repo_relative(repo, session_input.open_answers_dir)}`.",
                "- Before asking a new human question or declaring `hard_blocked`, first check whether a matching answer already exists.",
                "- The expected reply path for a question is the same basename under the answers directory.",
                "- Example: `questions/operator-confirmation.md` is answered by `answers/operator-confirmation.md`.",
                "- Treat matching answer files as authoritative human input for later sessions.",
            ]
        )

    if session_input.additional_instructions:
        lines.extend(
            [
                "",
                "Additional instructions:",
                session_input.additional_instructions.strip(),
            ]
        )

    lines.extend(
        [
            "",
            "Write the JSON result to:",
            f"`{session_result_file}`",
            "",
            "End the session only after that file exists.",
            "",
        ]
    )

    return "\n".join(lines)


def execute_session(
    *,
    agent: str,
    repo: Path,
    session_input: SessionInput,
    input_file: Path,
    run_dir: Path,
    dry_run: bool,
    extra_metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], SessionRunArtifacts]:
    session_result_file = resolve_session_result_path(session_input, repo, run_dir)
    prompt_file = run_dir / "prompt.md"
    events_file = run_dir / "events.jsonl"
    last_message_file = run_dir / "last-message.md"
    metadata_file = run_dir / "driver-metadata.json"

    if session_result_file.exists():
        session_result_file.unlink()

    prompt_text = build_prompt(repo, session_input, session_result_file)
    prompt_file.write_text(prompt_text, encoding="utf-8")

    command = build_agent_command(
        agent=agent,
        repo=repo,
        prompt_file=prompt_file,
        events_file=events_file,
        last_message_file=last_message_file,
    )

    metadata = {
        "agent": agent,
        "operator": session_input.operator,
        "repo": str(repo),
        "input_file": str(input_file),
        "run_dir": str(run_dir),
        "prompt_file": str(prompt_file),
        "events_file": str(events_file),
        "last_message_file": str(last_message_file),
        "session_result_file": str(session_result_file),
        "command": command,
        "dry_run": dry_run,
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    metadata_file.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    artifacts = SessionRunArtifacts(
        run_dir=run_dir,
        prompt_file=prompt_file,
        events_file=events_file,
        last_message_file=last_message_file,
        metadata_file=metadata_file,
        session_result_file=session_result_file,
        command=command,
    )

    if dry_run:
        return {}, artifacts

    exit_code = run_agent(command, prompt_file, events_file)

    if not session_result_file.is_file():
        if exit_code != 0:
            raise DriverError(
                f"agent command failed with exit code {exit_code}. See {events_file}"
            )
        raise DriverError(f"agent finished without writing session result: {session_result_file}")

    result = validate_session_result(session_result_file)
    if exit_code != 0:
        print(
            f"Agent exited with code {exit_code} after writing a valid session result; "
            "treating the session as logically complete."
        )
    return result, artifacts


def allocate_run_dir(runs_dir: Path, session_count: int) -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = runs_dir / f"{timestamp}-{session_count:03d}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def build_loop_session_input_payload(
    *,
    repo: Path,
    goal_file: Path | None,
    handoff_file: Path | None,
    runtime_guide_file: Path | None,
    questions_dir: Path | None,
    answers_dir: Path | None,
    operator: str | None,
    additional_context_files: list[Path],
    additional_instructions: str | None,
    run_dir: Path,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if operator is not None:
        payload["operator"] = operator
    if goal_file is not None:
        payload["goal_file"] = display_repo_relative(repo, goal_file)
    if handoff_file is not None:
        payload["handoff_file"] = display_repo_relative(repo, handoff_file)
    if runtime_guide_file is not None:
        payload["runtime_guide_file"] = display_repo_relative(repo, runtime_guide_file)
    if questions_dir is not None:
        payload["open_questions_dir"] = display_repo_relative(repo, questions_dir)
    if answers_dir is not None:
        payload["open_answers_dir"] = display_repo_relative(repo, answers_dir)
    if additional_context_files:
        payload["additional_context_files"] = [
            display_repo_relative(repo, item) for item in additional_context_files
        ]
    if additional_instructions:
        payload["additional_instructions"] = additional_instructions
    payload["session_result_file"] = display_repo_relative(repo, run_dir / "session-result.json")
    return payload


def ensure_handoff_dirs(repo: Path) -> dict[str, Path]:
    queue_dir = (repo / "handoff").resolve()
    inflight_dir = (repo / "handoff-run").resolve()
    history_dir = (repo / "handoff-history").resolve()
    for path in (queue_dir, inflight_dir, history_dir):
        path.mkdir(parents=True, exist_ok=True)
    return {"queue": queue_dir, "inflight": inflight_dir, "history": history_dir}


def list_queued_handoffs(queue_dir: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in queue_dir.iterdir()
            if path.is_file() and not path.name.startswith(".")
        ],
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )


def select_queued_handoff(queue_dir: Path) -> Path | None:
    queued = list_queued_handoffs(queue_dir)
    return queued[0] if queued else None


def reserve_handoff(queued_path: Path, handoff_dirs: dict[str, Path]) -> HandoffReservation:
    inflight_path = unique_destination(handoff_dirs["inflight"], queued_path.name)
    queued_path.rename(inflight_path)
    history_path = unique_destination(handoff_dirs["history"], inflight_path.name)
    return HandoffReservation(
        queued_path=queued_path,
        inflight_path=inflight_path,
        history_path=history_path,
    )


def archive_reserved_handoff(reservation: HandoffReservation) -> None:
    if reservation.inflight_path.exists():
        reservation.inflight_path.rename(reservation.history_path)


def restore_reserved_handoff(reservation: HandoffReservation) -> None:
    if reservation.inflight_path.exists():
        queued_target = unique_destination(reservation.queued_path.parent, reservation.queued_path.name)
        reservation.inflight_path.rename(queued_target)


def recover_inflight_handoffs(repo: Path, runs_dir: Path, handoff_dirs: dict[str, Path]) -> None:
    inflight_files = sorted(
        [
            path
            for path in handoff_dirs["inflight"].iterdir()
            if path.is_file() and not path.name.startswith(".")
        ],
        key=lambda path: path.name,
    )
    for inflight_path in inflight_files:
        latest_run = find_latest_run_for_inflight_handoff(runs_dir, inflight_path)
        reservation = HandoffReservation(
            queued_path=handoff_dirs["queue"] / inflight_path.name,
            inflight_path=inflight_path,
            history_path=unique_destination(handoff_dirs["history"], inflight_path.name),
        )
        if latest_run is None:
            restore_reserved_handoff(reservation)
            print(f"Recovered orphan inflight handoff back to queue: {display_repo_relative(repo, reservation.queued_path.parent / inflight_path.name)}")
            continue

        session_result_file = latest_run / "session-result.json"
        if session_result_file.is_file():
            try:
                validate_session_result(session_result_file)
            except DriverError:
                restore_reserved_handoff(reservation)
                print(f"Recovered invalid inflight handoff back to queue: {display_repo_relative(repo, reservation.queued_path.parent / inflight_path.name)}")
            else:
                archive_reserved_handoff(reservation)
                print(f"Archived recovered inflight handoff: {display_repo_relative(repo, reservation.history_path)}")
            continue

        restore_reserved_handoff(reservation)
        print(f"Re-queued interrupted handoff: {display_repo_relative(repo, reservation.queued_path.parent / inflight_path.name)}")


def recover_single_inflight_handoff(repo: Path, reservation: HandoffReservation, run_dir: Path) -> None:
    session_result_file = run_dir / "session-result.json"
    if session_result_file.is_file():
        try:
            validate_session_result(session_result_file)
        except DriverError:
            restore_reserved_handoff(reservation)
            print(f"Recovered failed handoff back to queue: {display_repo_relative(repo, reservation.queued_path.parent / reservation.queued_path.name)}")
        else:
            archive_reserved_handoff(reservation)
            print(f"Archived handoff after interrupted driver cleanup: {display_repo_relative(repo, reservation.history_path)}")
        return

    restore_reserved_handoff(reservation)
    print(f"Re-queued interrupted handoff: {display_repo_relative(repo, reservation.queued_path.parent / reservation.queued_path.name)}")


def find_latest_run_for_inflight_handoff(runs_dir: Path, inflight_path: Path) -> Path | None:
    if not runs_dir.is_dir():
        return None
    run_dirs = sorted(
        [path for path in runs_dir.iterdir() if path.is_dir()],
        key=lambda path: path.name,
        reverse=True,
    )
    for run_dir in run_dirs:
        metadata_file = run_dir / "driver-metadata.json"
        if not metadata_file.is_file():
            continue
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if metadata.get("input_handoff_file") == str(inflight_path):
            return run_dir
    return None


def build_handoff_metadata(
    repo: Path, reservation: HandoffReservation | None
) -> dict[str, Any] | None:
    if reservation is None:
        return None
    return {
        "queued_handoff_file": str(reservation.queued_path),
        "input_handoff_file": str(reservation.inflight_path),
        "history_handoff_file": str(reservation.history_path),
        "queued_handoff_file_repo_relative": display_repo_relative(repo, reservation.queued_path),
        "input_handoff_file_repo_relative": display_repo_relative(repo, reservation.inflight_path),
        "history_handoff_file_repo_relative": display_repo_relative(repo, reservation.history_path),
    }


def unique_destination(directory: Path, name: str) -> Path:
    candidate = directory / name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1
    while True:
        retry = directory / f"{stem}.{counter}{suffix}"
        if not retry.exists():
            return retry
        counter += 1


def display_repo_relative(repo: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)


def print_human_feedback(repo: Path, result: dict[str, Any], answers_dir: Path | None) -> None:
    question_files = result.get("question_files") or []
    if question_files:
        print("Human input requested:")
        for question_file in question_files:
            print(f"- Question: {question_file}")
            if answers_dir is not None:
                expected_answer = answers_dir / Path(question_file).name
                print(
                    f"  Answer by creating: {display_repo_relative(repo, expected_answer)}"
                )

    if result["outcome"] == "hard_blocked":
        print("Human attention required before the loop can continue.")


def build_agent_command(
    agent: str,
    repo: Path,
    prompt_file: Path,
    events_file: Path,
    last_message_file: Path,
) -> list[str]:
    if agent == "codex":
        return [
            "codex",
            "--dangerously-bypass-approvals-and-sandbox",
            "exec",
            "-C",
            str(repo),
            "--ephemeral",
            "--json",
            "-o",
            str(last_message_file),
            "-",
        ]

    raise DriverError(f"unsupported agent adapter: {agent}")


def run_agent(command: list[str], prompt_file: Path, events_file: Path) -> int:
    with prompt_file.open("r", encoding="utf-8") as prompt_handle:
        with events_file.open("w", encoding="utf-8") as events_handle:
            process = subprocess.Popen(
                command,
                stdin=prompt_handle,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            printed_progress = False

            assert process.stdout is not None
            for line in process.stdout:
                events_handle.write(line)
                events_handle.flush()
                print(".", end="", flush=True)
                printed_progress = True

            process.wait()

            if printed_progress:
                print("", flush=True)

    return process.returncode


def validate_session_result(session_result_file: Path) -> dict[str, Any]:
    try:
        payload = json.loads(session_result_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DriverError(f"invalid session result JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise DriverError("session result must be a JSON object")

    outcome = payload.get("outcome")
    if outcome not in VALID_OUTCOMES:
        raise DriverError(
            "session result outcome must be one of: "
            + ", ".join(sorted(VALID_OUTCOMES))
        )

    summary = payload.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise DriverError("session result summary must be a non-empty string")

    for field in ("handoff_files", "question_files"):
        value = payload.get(field)
        if value is None:
            continue
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            raise DriverError(f"session result {field} must be an array of non-empty strings")

    block_reason = payload.get("block_reason")
    if outcome == "hard_blocked":
        if not isinstance(block_reason, str) or not block_reason.strip():
            raise DriverError(
                "session result block_reason must be a non-empty string when outcome is hard_blocked"
            )

    return payload


def shell_join(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


if __name__ == "__main__":
    raise SystemExit(main())
