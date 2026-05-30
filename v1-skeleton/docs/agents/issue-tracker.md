# Issue tracker: Local Markdown

Issues and PRDs for this repo live as markdown files in `issues/`.

## Conventions

- One issue per file: `issues/<NN>-<slug>.md`, numbered from `01`
- Each file starts with a status header: `**Type**` (AFK/HITL) and `**Labels**`
- Triage state is recorded as `Labels:` line (see `triage-labels.md` for the role strings)
- Issues are ordered by dependency (blockers first)

## When a skill says "publish to the issue tracker"

Create a new file under `issues/` with the naming pattern `<NN>-<slug>.md`.

## When a skill says "fetch the relevant ticket"

Read the file at `issues/<NN>-<slug>.md`. The user will normally pass the path or the issue number directly.
