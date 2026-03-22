---
name: ha-ai-export-pipeline
description: 'Execute the Home Assistant AI export workflow end-to-end with safety gates and validation. Use when preparing AI-ready exports, sanitizing secrets, generating context files, and validating export integrity for local or SSH remote sources.'
---

# HA AI Export Pipeline

Use this skill to run the full export-to-AI workflow safely and consistently for team usage.

Execution policy:

- Always attempt the single-command full pipeline task first
- Fall back to stepwise tasks only if the full pipeline task fails
- Enforce strict no-warnings acceptance criteria

## When to Use This Skill

- Preparing a Home Assistant configuration package for AI assistance
- Running local or SSH-based export workflows
- Validating that secrets are sanitized before sharing
- Producing repeatable team outputs with clear quality gates

## Preconditions

- Python environment is configured and dependencies installed
- Workflow configuration exists and is valid
- For SSH mode: host/user/auth details are configured and reachable

## Workflow

### Phase A: Single-Command Path (Mandatory First Attempt)

1. Select mode (local or SSH).
2. Run the matching full pipeline task first:
	- Local: "HA Workflow: Full Pipeline (Local)"
	- SSH: "HA Workflow: Full Pipeline (SSH Remote)"
3. Evaluate result using strict policy:
	- Any error: FAIL
	- Any warning: FAIL
4. If full pipeline passes with zero warnings, continue to Phase C for import dry-run.
5. If full pipeline fails for any reason, continue to Phase B fallback.

### Phase B: Stepwise Fallback (Only After Full Pipeline Failure)

Run each step in order and stop on first failing or warning-producing step.

- Export
- Sanitize
- Generate context
- Validate export

Then continue to Phase C if all fallback steps pass with zero warnings.

## Step-by-Step Fallback Workflow

### Step 1: Select Execution Mode

Pick one mode:

- Local mode: read Home Assistant config from local source path
- SSH mode: read Home Assistant config from remote host

Decision rule:

- Choose SSH mode only if local Home Assistant config is not accessible
- If SSH settings are incomplete, stop and request missing fields

### Step 2: Run Export

- Execute export command in selected mode
- Capture output path and any warnings

Success criteria:

- Export command returns success
- Export directory exists
- Expected base files/folders are present

Failure handling:

- On export failure, stop pipeline and return actionable error summary

### Step 3: Sanitize Secrets

- Run sanitization step on exported content
- Confirm placeholders are created for sensitive values

Success criteria:

- Sanitizer returns success
- No raw secrets remain in generated AI-shareable artifacts
- Placeholder map (or equivalent secret tracking) is present

Failure handling:

- If unresolved secrets are detected, block completion
- Return a high-severity warning and remediation checklist

### Step 4: Generate AI Context

- Generate context artifacts (for example context markdown and prompt files)
- Confirm output files are created and non-empty

Success criteria:

- Context generation returns success
- Output files exist and contain usable content

### Step 5: Validate Export Package

- Run export validation against produced package
- Ensure compatibility checks pass

Success criteria:

- Export verifier reports valid package
- No fatal validation errors

Failure handling:

- Stop and return validation findings grouped by severity

### Step 6: Import Dry-Run (Required)

- Execute import in dry-run mode against the prepared package
- Confirm dry-run reports success with zero warnings

Success criteria:

- Dry-run import command succeeds
- No warning output is present
- No destructive changes are applied

Failure handling:

- If dry-run fails or emits warnings, mark overall result as FAIL
- Return blocking findings and required remediation

### Step 7: Produce Final Delivery Summary

Output a concise summary containing:

- Execution mode (local or SSH)
- Export location
- Sanitization status
- Context file paths
- Validation result
- Warnings or follow-up actions

## Quality Gates (Must Pass)

- Gate 1: Export succeeded and artifacts exist
- Gate 2: Secrets sanitized with no raw leaks in shareable files
- Gate 3: Context generated successfully
- Gate 4: Validation passes with no fatal issues
- Gate 5: Import dry-run passes with zero warnings

If any gate fails, the skill must stop and return a fail-fast report.

## Warning Policy (Strict)

- Warnings are treated as failures
- "No warnings allowed" applies to full pipeline, fallback steps, and import dry-run
- Final status is PASS only when all executed commands are warning-free

## Recommended Commands

Prefer existing project tasks when available:

- Export local: "HA Workflow: Export (Local)"
- Export remote: "HA Workflow: Export (SSH Remote)"
- Sanitize: "HA Workflow: Sanitize Export"
- Generate context: "HA Workflow: Generate AI Context"
- Validate: "HA Workflow: Validate Export"
- Full local: "HA Workflow: Full Pipeline (Local)"
- Full remote: "HA Workflow: Full Pipeline (SSH Remote)"
- Import dry-run: "HA Workflow: Import (Dry Run)"

## Reporting Format

Use this structure in outputs:

1. Result: PASS or FAIL
2. Path used: Full pipeline or Stepwise fallback
3. Gates: list each gate with pass/fail status
4. Artifacts: key paths produced
5. Risks: any residual warnings
6. Next actions: exact steps to resolve failures

## Selectable Invocation Options

Use this numbered menu to choose a run mode quickly. Respond with just the option number when selecting.

1. Local full pipeline with strict gates
Context: Use when Home Assistant config is available locally and you want fastest compliant execution via single-command path first.
Prompt: "Run option 1 for HA AI export pipeline."

2. SSH full pipeline with strict gates
Context: Use when Home Assistant config is remote and SSH access is configured.
Prompt: "Run option 2 for HA AI export pipeline."

3. Force fallback stepwise path after full-pipeline failure
Context: Use for diagnosis when full pipeline fails and you need stage-level failure isolation.
Prompt: "Run option 3 for HA AI export pipeline."

4. Validate existing export package and import dry-run only
Context: Use when export artifacts already exist and you only need safety verification and dry-run import.
Prompt: "Run option 4 for HA AI export pipeline."

5. Gate report only (no execution)
Context: Use for review meetings to assess readiness criteria and required evidence.
Prompt: "Run option 5 for HA AI export pipeline."

## Team Conventions for This Repository

- Keep workflows compatible with both local and SSH modes
- Do not expose secrets in logs, summaries, or exported artifacts
- Apply strict no-warnings policy to all pipeline stages
- Maintain backward compatibility for export validation expectations
- Favor project Makefile/tasks for consistent execution behavior
