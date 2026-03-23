# Workspace Optimization User Guide

This is the practical, beginner-safe guide for using the workspace customizations.
If you are unsure what to do next, start with the Top-Down Walkthrough.

Quick one-page version: docs/WORKSPACE_OPERATOR_CARD.md
Print version: docs/WORKSPACE_OPERATOR_CARD_PRINT.md

## Top-Down Walkthrough (Start Here)

Follow these steps in order for every task.

1. Identify task type:
   - API/export/import/orchestrator behavior change
   - Release/version metadata change
   - Single-module bug fix
1. Route to the correct owner first:

```text
Apply module-owner-map and identify owner file, owner tests, and first 3 commands.
```

1. If behavior touches API/workflow, run smoke first:

```text
/ha-api-sandbox-smoke Validate <module.function> in <internal|external> mode.
```

And run the permanent local sandbox quality gate:

```text
Run tools/ha_local_test/manage_local_ha_test.py quality-gate and include pass/fail with exit code.
```

1. Implement minimal fix only.
1. Run targeted tests.
1. Run quality gates.
1. If release files changed, enforce version-sync-guard.
1. Request final evidence report.

## Who This Is For

1. New contributor: You want safe defaults and copy-paste prompts.
1. Regular contributor: You want faster coding with fewer regressions.
1. Release maintainer: You need strict version and changelog safety.

## What Is Installed

1. Integrated workflow guide:
   - docs/INTEGRATED_AGENT_WORKFLOW.md
1. Prompt:
   - .github/prompts/ha-api-sandbox-smoke.prompt.md
1. Instructions:
   - .github/instructions/version-sync-guard.instructions.md
   - .github/instructions/module-owner-map.instructions.md

These run on top of existing repository rules in .github/copilot-instructions.md.

## Decision Tree Playbook

Use this exact decision tree.

1. Are you changing `config.yaml`, `build.yaml`, Docker labels, or `CHANGELOG.md`?
   - Yes: Run version-sync-guard first.
   - No: Continue.
1. Are you changing API/export/import/orchestrator behavior?
   - Yes: Run /ha-api-sandbox-smoke, then module-owner-map.
   - No: Continue.
1. Is this a bug in one module?
   - Yes: Use module-owner-map and run module-targeted tests first.
   - No: Use integrated workflow.
1. Are you ready to finish?
   - Require evidence format output with commands, pass/fail, and exit codes.

## 5-Minute Quick Start

1. Open Copilot Chat in this repository.
1. Start with this prompt:

```text
/ha-api-sandbox-smoke Validate ha_api_client.get_addons in internal mode and return pass/fail evidence.
```

1. Ask for owner routing:

```text
Apply module-owner-map and identify the owner module and targeted tests before editing.
```

1. If you changed release files, run:

```text
Apply version-sync-guard and verify config/build/changelog are synchronized.
```

1. Run quality gates.

Linux/macOS:

```bash
make quick-validate
make format
make lint
make security
make test
```

Windows fallback:

```bash
python -m pyright
python -m black --check --line-length 120 bin/ tests/
python -m flake8 bin/ tests/ --max-line-length=120 --ignore=E203,W503
python -m bandit -r bin/ -ll -i
python -m pytest -v
```

## Step-by-Step Standard Workflow

Use this for almost all code changes.

1. Define scope:
   - What file/function is broken?
   - What behavior should change?
1. Route to owner:

```text
Apply module-owner-map and limit changes to owner module and direct callers only.
```

1. Run fast sandbox smoke:

```text
/ha-api-sandbox-smoke Validate <module.function> in <internal|external> mode.
```

1. Implement minimal fix.
1. Run targeted tests.
1. Run quality gates (quick -> full).
1. If release files changed, enforce version-sync-guard.
1. Request final evidence report.

## Case-by-Case Playbooks

### Case 1: API Function Fails

Use when methods in ha_api_client or API-dependent exporters fail.

1. Prompt:

```text
/ha-api-sandbox-smoke Validate HomeAssistantAPI.test_connection in external mode and provide root cause plus minimal fix.
```

1. Prompt:

```text
Apply module-owner-map and keep changes in bin/ha_api_client.py unless a direct caller requires updates.
```

1. Run targeted tests:

```bash
python -m pytest tests/test_ha_api_client.py -v
```

### Case 2: Export/Import Pipeline Regression

Use for issues in export, sanitize, context, import, or validate flow.

1. Prompt:

```text
/ha-api-sandbox-smoke Validate export->validate->import dry-run flow and report failing stage.
```

1. Prompt:

```text
Apply module-owner-map and fix only owner module plus direct orchestrator integration points.
```

1. Runtime commands:

```bash
python tools/ha_local_test/manage_local_ha_test.py quality-gate
python bin/workflow_orchestrator.py full --source tools/ha_local_test/ha_config
python bin/workflow_orchestrator.py validate --source <latest_export_path>
python bin/workflow_orchestrator.py import --source <latest_export_path> --target imports/dry_run_target --dry-run
```

1. Token rotation and cleanup for repeated runs:

```bash
HA_TEST_TOKEN=<current_token> python tools/ha_local_test/manage_local_ha_test.py token-bootstrap
HA_TEST_TOKEN=<new_token> python tools/ha_local_test/manage_local_ha_test.py token-prune
HA_TEST_TOKEN=<new_token> python tools/ha_local_test/manage_local_ha_test.py api-smoke
```

### Case 3: Release Version Bump

Use when changing addon version.

1. Prompt:

```text
Apply version-sync-guard and bump version to <X.Y.Z>. Update build metadata and changelog in the same change set.
```

1. Validate that all required version files match.
1. Ensure changelog has concrete Fixed/Added/Changed entries.

### Case 4: Unsure Which File Owns The Bug

1. Prompt:

```text
Apply module-owner-map and identify owner module, owner tests, and minimal edit plan before coding.
```

1. Approve plan.
1. Continue with targeted edits and tests.

### Case 5: Need Highest Confidence Before PR

1. Prompt:

```text
Run integrated workflow with evidence format: owner mapping, sandbox smoke, targeted tests, full quality ladder, and residual risks.
```

1. Verify command outputs include pass/fail and exit codes.

## Compact Prompt Library

1. Quick smoke:

```text
/ha-api-sandbox-smoke Validate ha_diagnostic_export API fallback behavior in internal mode.
```

1. Owner-first bug fix:

```text
Apply module-owner-map and fix retry behavior in ssh_transfer with targeted tests first.
```

1. Release-safe update:

```text
Apply version-sync-guard while updating addon version and changelog. Block completion until all version fields are synchronized.
```

1. Full audit:

```text
Use the integrated workflow and return: scope, commands run, pass/fail per command, files changed, risks, and next recommendation.
```

1. Sandbox quality gate:

```text
Run tools/ha_local_test/manage_local_ha_test.py quality-gate and include exit code evidence.
```

## Required Evidence Format

Ask for this exact output format after each task.

1. Scope and owner file
1. Commands run
1. Pass/fail and exit code per command
1. Root cause and fix summary
1. Files changed
1. Risks and blockers
1. Next action

Prompt:

```text
Return results using the required evidence format with exact command outputs summarized.
```

## Common Mistakes and Fixes

1. Problem: Prompt command not visible.
   - Fix: Confirm file exists at .github/prompts/ha-api-sandbox-smoke.prompt.md.
   - Fix: Reload VS Code window.
1. Problem: Instruction not applied.
   - Fix: Confirm path matches applyTo scope.
   - Fix: Keep changed file inside bin/, tests/, or ha_ai_workflow_addon/ when using module-owner-map.
1. Problem: Docker sandbox unavailable.
   - Fix: Run targeted pytest and orchestrator dry-run commands as fallback.
1. Problem: validate shows failures but tooling says success.
   - Fix: Check exit code and ensure command path has non-zero on validation failure.

## Related Docs

1. docs/INTEGRATED_AGENT_WORKFLOW.md
1. docs/API_CONFIGURATION_GUIDE.md
1. docs/TESTING_GUIDE.md
1. docs/VERSION_CHANGELOG_GUIDE.md
1. .github/copilot-instructions.md
