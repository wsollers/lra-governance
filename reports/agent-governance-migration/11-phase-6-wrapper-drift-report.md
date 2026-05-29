# Phase 6: Wrapper Drift Reporting

## Reason

Phase 6 adds drift reporting between generated agent-wrapper previews and
existing downstream instruction files. The goal is to understand current
downstream state before any future write or sync mode exists.

## Tool Added

`tools/governance/report_wrapper_drift.py` compares generated preview files
against downstream repo files for:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`
- `.github/instructions/lra.instructions.md`

For each repo/file pair, it records whether the downstream file is missing,
identical, different, missing from preview, or whether the downstream repo is
missing.

## Safety

The tool opens downstream files read-only and writes only metadata reports to
the requested output directory. It does not create, modify, overwrite, or sync
files in downstream repos.

Reports contain hashes, byte counts, line counts, and small diff statistics,
not full file contents.

## Phase Placement

This sits between preview generation and any future controlled write/sync mode.
It lets reviewers inspect drift before deciding what a safe full-replace or
drift-check workflow should look like.

## Intentionally Not Implemented

- No downstream write mode.
- No downstream sync.
- No automatic remediation.
- No generated wrapper commits to downstream repos.
- No mathematical content edits.
- No changes to `DESIGN.md`, `REPOSITORY_STRUCTURE.md`, or
  `Learning-Real-Analysis/scripts/`.

