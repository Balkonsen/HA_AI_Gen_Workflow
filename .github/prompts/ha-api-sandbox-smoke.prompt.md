---
name: "HA API Sandbox Smoke"
description: "Run one-command, function-level HA API validation before full workflow checks."
argument-hint: "Provide module/function scope, HA mode (internal/external), and optional target export path."
agent: "agent"
---

Execute a focused HA API sandbox smoke validation and return a concise pass/fail report.

Primary objective:

- Validate function-level API behavior first.
- Validate orchestrator-level integration second.
- Stop before full test suite unless explicitly requested.

Input you should infer or ask for only if missing:

- Target scope: module/function (example: `ha_api_client.get_addons`, `ha_diagnostic_export` API calls)
- Mode: `internal` (add-on endpoints) or `external` (HA_URL + SUPERVISOR_TOKEN)
- Optional export directory/source path

Required execution order:

1. Environment sanity checks.
2. Start or verify local HA sandbox.
3. Run targeted function-level checks.
4. Run orchestrator dry-run validation chain.
5. Report findings and only then suggest full gates.

Preferred commands:

```bash
python tools/ha_local_test/manage_local_ha_test.py up
python tools/ha_local_test/manage_local_ha_test.py status
python tools/ha_local_test/manage_local_ha_test.py dry-run
```

If function-level scope is provided, run targeted tests/checks first, for example:

```bash
python -m pytest tests/test_<affected_module>.py -v
```

Output format:

## Scope

- Module/function: <value>
- Mode: <internal|external>

## Checks Run

- <command>: <pass/fail>
- <command>: <pass/fail>

## Findings

- <issue or "none">

## Next Gate Recommendation

- `make quick-validate` or `make test` with rationale

Constraints:

- Never print or store tokens.
- Do not claim success without command evidence.
- If sandbox fails to start, provide exact blocker and minimal fallback plan.
