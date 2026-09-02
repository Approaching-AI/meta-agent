# Doc

A **doc** is a snapshot-style document that captures the overall understanding of a project at a given point in time.

Within `meta-agent`, `doc/` is one of the only two core persistent folders. The other is `meta-log/`.

`doc/roadmap/` is an optional content area inside `doc/` for future feature ideas and plans that have been designed but are not yet scheduled for implementation. It does not create a third persistence layer or an automatic work queue.

## Contrast with Daily Notes

- **Daily notes** are incremental — they accumulate entries over time.
- **Doc** is a snapshot — it represents a holistic view of the project as understood at roughly a certain moment.

## Principles

- The snapshot timestamp does not need to be precise; an approximate time frame is fine.
- A doc should reflect the current state of understanding, not a changelog.
- Humans may also place relevant reference materials into the doc folder directly.
- Roadmap entries are kept in the host project’s own `doc/roadmap/` directory; agents decide when to create, inspect, or implement them.
