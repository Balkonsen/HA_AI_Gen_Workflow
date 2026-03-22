---
name: ha-pr-quality-gate
description: 'Run a strict pre-PR quality gate for HA AI Gen Workflow. Use when preparing or updating pull requests to validate formatting, linting, tests, and security checks before commit or review.'
---

# HA PR Quality Gate

Use this skill to enforce a consistent, team-ready validation sequence before pull requests.

## When to Use This Skill

- Before creating a pull request
- Before requesting re-review on an updated pull request
- After significant code edits in bin, tests, scripts, or addon files

## Workflow

### Step 1: Scope and Select Tests

- Identify changed files
- Select targeted tests for changed areas

### Step 2: Run Core Checks

Execute in order:

1. Formatting
2. Linting
3. Targeted tests
4. Full tests (when required by scope)
5. Security scan

Recommended commands:

- make format
- make lint
- pytest -v <targeted tests>
- make test
- make security

### Step 3: Evaluate Against Gate Policy

- Any failing check = FAIL
- Any warning in required checks = FAIL

### Step 4: Produce PR Readiness Summary

Include:

- Checks run and outcomes
- Failing files/tests if any
- Residual risks
- Required fixes before PR

## Quality Gates

- Gate 1: Formatting complete and clean
- Gate 2: Lint checks pass
- Gate 3: Targeted tests pass
- Gate 4: Security scan passes
- Gate 5: No unresolved critical warnings in required checks

If any gate fails, do not mark PR as ready.

## Reporting Format

1. Result: READY or NOT READY
2. Checks run: list with pass/fail
3. Failing items: concise list
4. Risk summary: low/medium/high
5. Next actions: exact remediation steps

## Selectable Invocation Options

Use this numbered menu to choose a validation depth. Respond with just the option number when selecting.

1. Quick PR gate
Context: Use for small, focused changes where fast confidence is needed before pushing updates.
Prompt: "Run option 1 for HA PR quality gate."

2. Standard PR gate
Context: Use for typical feature or bugfix PRs requiring formatting, linting, targeted tests, and security scan.
Prompt: "Run option 2 for HA PR quality gate."

3. Strict full gate
Context: Use for high-risk changes and release-bound PRs requiring full test execution plus strict warning enforcement.
Prompt: "Run option 3 for HA PR quality gate."

4. Security-focused gate
Context: Use when changes touch secrets, auth, SSH, or shell execution paths.
Prompt: "Run option 4 for HA PR quality gate."

5. Readiness report only (no execution)
Context: Use during review planning to list required checks and readiness criteria without running commands.
Prompt: "Run option 5 for HA PR quality gate."
