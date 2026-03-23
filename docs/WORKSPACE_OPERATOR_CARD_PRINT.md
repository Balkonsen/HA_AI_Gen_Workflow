# Workspace Operator Card (Print)

Use this as a one-page printable checklist.

## 0. Job Setup

- [ ] Task type identified:
  - [ ] API/export/import/orchestrator behavior change
  - [ ] Release/version metadata change
  - [ ] Single-module bug
- [ ] Owner routing requested:

```text
Apply module-owner-map and identify owner file, owner tests, and first 3 commands.
```

## 1. Decision Tree

- [ ] Editing `ha_ai_workflow_addon/config.yaml`, `ha_ai_workflow_addon/build.yaml`, Docker labels, or `CHANGELOG.md`?
  - [ ] Yes -> Run:

```text
Apply version-sync-guard and verify config/build/changelog are synchronized.
```

- [ ] Editing API/export/import/orchestrator behavior?
  - [ ] Yes -> Run:

```text
/ha-api-sandbox-smoke Validate <module.function> in <internal|external> mode.
```

- [ ] Single-module bug only?
  - [ ] Yes -> Keep edits to owner module + direct callers.

## 2. Execution Flow

- [ ] Scope issue in one sentence
- [ ] Run owner routing
- [ ] Run smoke validation (if behavior change)
- [ ] Implement smallest fix
- [ ] Run targeted tests
- [ ] Run quality ladder
- [ ] Run release sync guard (if release files changed)
- [ ] Request final evidence report

## 3. Prompt Shortcuts

Owner routing:

```text
Apply module-owner-map and identify owner module, owner tests, and minimal edit plan before coding.
```

API smoke:

```text
/ha-api-sandbox-smoke Validate HomeAssistantAPI.test_connection in external mode and provide root cause plus minimal fix.
```

Export/import flow:

```text
/ha-api-sandbox-smoke Validate export->validate->import dry-run flow and report failing stage.
```

Release guard:

```text
Apply version-sync-guard while updating addon version and changelog. Block completion until all version fields are synchronized.
```

Final audit:

```text
Use integrated workflow and return: scope, commands run, pass/fail with exit codes, files changed, risks, and next action.
```

## 4. Quality Ladder

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

## 5. Runtime Validation

```bash
python bin/workflow_orchestrator.py full --source tools/ha_local_test/ha_config
python bin/workflow_orchestrator.py validate --source <latest_export_path>
python bin/workflow_orchestrator.py import --source <latest_export_path> --target imports/dry_run_target --dry-run
```

## 6. Done Criteria

- [ ] Owner module and owner tests identified first
- [ ] Smoke validation executed for behavior changes
- [ ] Targeted tests passed
- [ ] Quality ladder passed
- [ ] Release sync guard passed (if applicable)
- [ ] Final evidence contains pass/fail and exit codes

## 7. Fast Troubleshooting

- [ ] Prompt missing -> check `.github/prompts/ha-api-sandbox-smoke.prompt.md`, reload VS Code
- [ ] Instruction missing -> verify changed file is in instruction `applyTo` scope
- [ ] Docker unavailable -> use targeted pytest + orchestrator dry-run fallback
- [ ] Validation mismatch -> verify command exit code and failure propagation
