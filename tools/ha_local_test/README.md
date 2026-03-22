# Local Home Assistant Test Platform

This folder provides a virtual local Home Assistant platform for safe dry-run validation and workflow testing.

## What It Includes

- `docker-compose.ha-local.yml`: Home Assistant container on `http://localhost:8123`
- `ha_config/`: seeded Home Assistant test configuration
- `manage_local_ha_test.py`: helper for start/stop/reset and dry-run workflow execution

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Python environment with project dependencies installed

## Quick Start

Start the local Home Assistant sandbox:

```bash
python tools/ha_local_test/manage_local_ha_test.py up
```

Check container status:

```bash
python tools/ha_local_test/manage_local_ha_test.py status
```

Run full local dry-run validation pipeline:

```bash
python tools/ha_local_test/manage_local_ha_test.py dry-run
```

Stop sandbox:

```bash
python tools/ha_local_test/manage_local_ha_test.py down
```

Reset sandbox state:

```bash
python tools/ha_local_test/manage_local_ha_test.py reset
```

View sandbox logs:

```bash
python tools/ha_local_test/manage_local_ha_test.py logs
```

## Dry-Run Flow Executed by Helper

The `dry-run` command performs:

1. `workflow_orchestrator.py full --source tools/ha_local_test/ha_config`
2. `workflow_orchestrator.py validate --source <latest export>`
3. `workflow_orchestrator.py import --source <latest export> --target imports/dry_run_target --dry-run`

## Notes

- This is a sandbox for local workflow validation, not a production Home Assistant instance.
- Seeded secrets are fake and only used to exercise sanitization logic.
- The first Home Assistant startup can take a few minutes.
