# Integrated Agent Workflow

This document unifies the repository's agent, developer, API, testing, deployment, and versioning guidance into one execution routine.

It is designed for three outcomes:

1. Fully integrated decisions across modules and docs.
1. Faster delivery without skipping safeguards.
1. Higher quality through incremental validation and strict gates.

## Source of Truth Map

Use this document as an orchestrator, not a replacement.

- Core constraints and historical failures: [../.github/copilot-instructions.md](../.github/copilot-instructions.md)
- Agent operating baseline: [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md)
- Deep coding and debugging protocol: [CODING_AGENT_PROMPT.md](CODING_AGENT_PROMPT.md)
- API mode and token behavior: [API_CONFIGURATION_GUIDE.md](API_CONFIGURATION_GUIDE.md)
- Daily engineering workflow: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- Validation and CI checks: [TESTING_GUIDE.md](TESTING_GUIDE.md)
- Version and changelog synchronization: [VERSION_CHANGELOG_GUIDE.md](VERSION_CHANGELOG_GUIDE.md)
- Local HA sandbox operations: [../tools/ha_local_test/README.md](../tools/ha_local_test/README.md)

## Workspace Customizations

- Prompt: [../.github/prompts/ha-api-sandbox-smoke.prompt.md](../.github/prompts/ha-api-sandbox-smoke.prompt.md)
- Instruction: [../.github/instructions/version-sync-guard.instructions.md](../.github/instructions/version-sync-guard.instructions.md)
- Instruction: [../.github/instructions/module-owner-map.instructions.md](../.github/instructions/module-owner-map.instructions.md)
- User guide: [WORKSPACE_OPTIMIZATION_USER_GUIDE.md](WORKSPACE_OPTIMIZATION_USER_GUIDE.md)

## Unified Operating Model

Run this sequence for every issue or feature.

## Trace-First Observability (Required for Bugfix/Debug Work)

Before running integrated workflow phases, enable full trace capture so every decision and gate can be audited.

Recommended runtime flags:

```bash
python bin/workflow_orchestrator.py full --source <ha_config_path> --log-level DEBUG --trace-log --trace-log-file ./exports/workflow_trace.log --strict-warnings
```

Expected artifacts:

- `workflow.log`: human-readable operational log
- `workflow_trace.log`: structured JSONL trace for phase-level and function-level diagnostics

Use the trace file as the source for:

1. Phase-by-phase failure isolation
1. Skill/routine execution evidence (`ha-ai-export-pipeline`, quality gate ladder)
1. Root-cause timelines for PR summaries and regression reviews

### Phase 0: Intake and Risk Classification

1. Classify change type:
   - Module bug fix
   - Cross-module behavior change
   - Security/secrets handling
   - Add-on/runtime/deployment behavior
   - Versioned release change
1. Mark risk level:
   - High: secrets, import/export correctness, SSH transfer, add-on startup
   - Medium: API behavior, context generation, validation output
   - Low: docs or non-runtime tooling

### Phase 1: Targeted Context Bootstrap

1. Identify owning module in [../bin](../bin).
1. Read existing tests first in [../tests](../tests).
1. Confirm real method signatures in source before changing callers.
1. Confirm constraints that apply:
   - No `bashio` or `s6` in add-on startup scripts.
   - Docker COPY paths are relative to [../ha_ai_workflow_addon](../ha_ai_workflow_addon).
   - No hardcoded `/config/ai_exports` in non-container code.
   - Version bump requires synchronized changelog update.

### Phase 2: Reproduce in Smallest Safe Scope

1. Reproduce issue with a focused test or command.
1. If behavior touches HA API or workflow orchestration, run in local sandbox first.
1. Capture exact failing symptom and root cause before coding.

Recommended sandbox entry point:

```bash
python tools/ha_local_test/manage_local_ha_test.py up
python tools/ha_local_test/manage_local_ha_test.py status
```

### Phase 3: Minimal Change + Immediate Local Validation

For each code change batch, run nearest checks immediately.

1. Module-local tests (single file/class/function).
1. Syntax/format/lint only for affected scope.
1. Security scan if touching secrets, auth, subprocess, SSH, or file I/O.

Do not stack many edits before first validation pass.

### Phase 4: Iterative Function-Level HA API Sandbox Validation

Use this loop for API- and workflow-facing functionality.

1. Validate single function or module behavior in isolation.
1. Validate integration call path through orchestrator command.
1. Validate dry-run import behavior before any real import.

Reference dry-run flow:

```bash
python tools/ha_local_test/manage_local_ha_test.py dry-run
```

Permanent sandbox quality-gate flow (required for API/export/import/orchestrator changes):

```bash
python tools/ha_local_test/manage_local_ha_test.py quality-gate
```

If token-authenticated checks are required, use the rotation pattern:

```bash
HA_TEST_TOKEN=<current_token> python tools/ha_local_test/manage_local_ha_test.py token-bootstrap
HA_TEST_TOKEN=<newly_printed_token> python tools/ha_local_test/manage_local_ha_test.py api-smoke
HA_TEST_TOKEN=<newly_printed_token> python tools/ha_local_test/manage_local_ha_test.py token-prune
```

Manual staged flow:

```bash
python bin/workflow_orchestrator.py full --source tools/ha_local_test/ha_config
python bin/workflow_orchestrator.py validate --source <latest_export_path>
python bin/workflow_orchestrator.py import --source <latest_export_path> --target imports/dry_run_target --dry-run
```

### Phase 5: Quality Gate Ladder (Fast to Full)

Run checks in this order to optimize speed and confidence.

1. Fast gate:

```bash
make quick-validate
```

1. Targeted gate:

```bash
python -m pytest tests/test_<affected_module>.py -v
```

2.5. Local HA sandbox gate for workflow/API changes:

```bash
make ha-sandbox-gate
```

1. Required static + security gates:

```bash
make format
make lint
make security
```

1. Full confidence gate:

```bash
make test
```

1. Optional full pre-PR gate:

```bash
make validate
```

Strict policy for integrated mode:

- Use `--strict-warnings` to treat warnings as failures during validation and gate reporting.

## Integrated Speed + Quality Rules

1. Prefer smallest viable fix first; refactor only when blocked.
1. Validate early per function/module; do not defer all checks to the end.
1. Keep backward compatibility for export verifier v1.0 and v2.0.
1. Treat warnings in required quality gates as actionable before merge.
1. For setup scripts and add-on startup, prefer proven simple patterns over clever rewrites.

## Role/Capability Integration

Use this ownership model to reduce overlap and rework.

1. Orchestrator layer:
   - [../bin/workflow_orchestrator.py](../bin/workflow_orchestrator.py)
   - Command sequencing and workflow entry points
1. Domain modules:
   - Export: [../bin/ha_diagnostic_export.py](../bin/ha_diagnostic_export.py)
   - Import: [../bin/ha_config_import.py](../bin/ha_config_import.py)
   - Context: [../bin/ha_ai_context_gen.py](../bin/ha_ai_context_gen.py)
   - Verify: [../bin/ha_export_verifier.py](../bin/ha_export_verifier.py)
   - Secrets: [../bin/secrets_manager.py](../bin/secrets_manager.py)
   - API: [../bin/ha_api_client.py](../bin/ha_api_client.py)
   - SSH: [../bin/ssh_transfer.py](../bin/ssh_transfer.py)
1. Add-on runtime:
   - [../ha_ai_workflow_addon/run.sh](../ha_ai_workflow_addon/run.sh)
   - [../ha_ai_workflow_addon/Dockerfile](../ha_ai_workflow_addon/Dockerfile)
1. Quality and verification:
   - [../tests](../tests)
   - [../tools](../tools)
   - [../Makefile](../Makefile)

## Release-Safe Change Routine

Apply this only when versioned files change.

1. Update version in [../ha_ai_workflow_addon/config.yaml](../ha_ai_workflow_addon/config.yaml).
1. Synchronize with [../ha_ai_workflow_addon/build.yaml](../ha_ai_workflow_addon/build.yaml) and Docker labels if applicable.
1. Add a concrete entry in [../CHANGELOG.md](../CHANGELOG.md) in the same change set.

## Practical Execution Template

Use this compact, repeatable sequence:

1. Read owner module + tests.
1. Reproduce failure.
1. Implement smallest fix.
1. Run targeted test.
1. Run sandbox dry-run if API/workflow behavior is involved.
1. Run format/lint/security.
1. Run full tests.
1. Sync docs/changelog/version files if required.

## Suggested Follow-Up Customizations

1. Create a dedicated "HA API sandbox smoke" prompt that runs module-level API checks before full workflow checks.
1. Create a "version-sync guard" instruction that blocks release PRs if changelog/version drift is detected.
1. Create a "module-owner map" instruction with applyTo patterns for each key file in [../bin](../bin).
