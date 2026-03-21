---
name: "Diagnostics Fix PR Template"
description: "Standardize PR title and body for diagnostics-fix pull requests (Pylance/Pyright)."
argument-hint: "Provide branch, diagnostics scope, validation results, and whether auto-merge is requested."
agent: "agent"
---
Generate a complete pull request title and body for a diagnostics-fix change set.

Use this exact output structure:

Title:
fix(pyright): <short scope summary>

Body:
## Summary
- <what diagnostics were targeted>
- <high-level approach>

## Diagnostics Resolved
- <file>: <diagnostics fixed>
- <file>: <diagnostics fixed>

## Validation
- `pyright`: <pass/fail + notes>
- `pytest (targeted)`: <pass/fail + tests run>
- <other checks>: <pass/fail>

## Risk & Rollback
- Risk level: <low/medium/high>
- Rollback: <how to revert safely>

## Branch & Merge Plan
- Branch strategy: <main or feature branch>
- Auto-merge requested: <yes/no>
- Merge conditions: <required checks/reviews>

Constraints:
- Keep title under 72 chars when possible.
- Keep bullets concise and factual.
- Do not claim checks passed unless results are provided.
