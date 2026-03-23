# Workspace Operator Card

Use this as the one-page runbook for daily operations.

## 1) Start Here (30 Seconds)

1. Identify task type:
   - API/export/import/orchestrator change
   - Release/version change
   - Single module bug
1. Run owner routing first:

```text
Apply module-owner-map and identify owner file, owner tests, and first 3 commands.
```

1. If task touches behavior, run smoke first:

```text
/ha-api-sandbox-smoke Validate <module.function> in <internal|external> mode.
```

## 2) Decision Tree (Do This, Then That)

1. Editing `ha_ai_workflow_addon/config.yaml`, `ha_ai_workflow_addon/build.yaml`, Docker labels, or `CHANGELOG.md`?
   - Yes: Run version-sync-guard first.
   - Command:

```text
Apply version-sync-guard and verify config/build/changelog are synchronized.
```

1. Editing API/export/import/orchestrator behavior?
   - Yes: Run `/ha-api-sandbox-smoke`, then apply `module-owner-map`.

1. Single-module bug only?
   - Yes: Apply `module-owner-map`, keep edits in owner + direct callers only.

1. Finalization step for all tasks:
   - Require evidence format output (commands + pass/fail + exit codes).

## 3) Golden Workflow (Top-Down)

1. Scope issue in one sentence.
1. Route owner file.
1. Run smoke validation.
1. Implement smallest fix.
1. Run targeted tests.
1. Run quality ladder.
1. Enforce release sync if needed.
1. Request final evidence report.

## 4) Prompt Shortcuts (Copy/Paste)

1. Owner routing:

```text
Apply module-owner-map and identify owner module, owner tests, and minimal edit plan before coding.
```

1. API smoke:

```text
/ha-api-sandbox-smoke Validate HomeAssistantAPI.test_connection in external mode and provide root cause plus minimal fix.
```

1. Export/import flow:

```text
/ha-api-sandbox-smoke Validate export->validate->import dry-run flow and report failing stage.
```

1. Release guard:

```text
Apply version-sync-guard while updating addon version and changelog. Block completion until all version fields are synchronized.
```

1. Final audit output:

```text
Use integrated workflow and return: scope, commands run, pass/fail with exit codes, files changed, risks, and next action.
```

## 5) Quality Ladder

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

## 6) Runtime Validation Commands

```bash
python bin/workflow_orchestrator.py full --source tools/ha_local_test/ha_config
python bin/workflow_orchestrator.py validate --source <latest_export_path>
python bin/workflow_orchestrator.py import --source <latest_export_path> --target imports/dry_run_target --dry-run
```

## 7) Done Criteria (Must Be True)

1. Owner module and tests were identified first.
1. Smoke validation executed for behavior changes.
1. Targeted tests passed.
1. Quality ladder passed.
1. Release sync guard passed when release files changed.
1. Final report includes pass/fail and exit codes.

## 8) Fast Troubleshooting

1. Prompt not visible:
   - Check `.github/prompts/ha-api-sandbox-smoke.prompt.md` exists.
   - Reload VS Code window.
1. Instruction not applied:
   - Confirm file path is in instruction `applyTo` scope.
1. Docker sandbox unavailable:
   - Use targeted pytest plus orchestrator dry-run commands.
1. Validation text says fail but command returns success:
   - Verify command exit code and CLI failure propagation.
