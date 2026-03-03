# SOP (Standard Operating Procedure)

SOPs are distilled from daily notes and docs, and stored under the `doc/` folder. Both humans and agents should have a shared understanding of each SOP.

## Structure

Every SOP should have:

- **Start condition** — when to trigger this SOP.
- **End condition** — how to know the SOP is complete.
- **Steps** — the execution procedure.

## Why SOP Instead of Scripts?

Scripts are rigid. SOPs are executed by agents who can handle contextual problems that arise in the real execution environment.

For example, an SOP step says "clone a GitHub repo." A script would simply run `git clone` and fail if anything goes wrong. An agent executing the same SOP can:

- Detect that the network is behind a firewall and switch to a proxy or mirror.
- Notice the disk is full and free up space or alert the human.
- Handle any other unexpected environmental issue.

In short, SOPs leverage the agent's ability to reason about and adapt to context — something a static script cannot do.
