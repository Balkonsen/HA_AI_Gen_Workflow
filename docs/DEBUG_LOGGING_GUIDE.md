# Enhanced Debug Logging - Usage Examples

This document demonstrates the new debug logging features added to the HA AI Gen Workflow.

## Overview

The enhanced debug logging system provides comprehensive insights into function execution, variable values, and call stacks when DEBUG mode is enabled.

## Enabling DEBUG Mode

### Command Line

```bash
# Master script with DEBUG mode
./ha_ai_master_script.sh export --log-level DEBUG

# Or with environment variable
export HA_AI_LOG_LEVEL=DEBUG
./ha_ai_master_script.sh export
```

### Python Scripts

```python
from workflow_logger import get_logger, LogLevel

logger = get_logger()
logger.set_log_level(LogLevel.DEBUG)
```

## Full Verbose Trace Log (JSONL)

The workflow now supports a dedicated structured trace file that captures:

- Every logger call (including messages filtered by current log level)
- Function-level entry/exit traces for orchestrator workflow methods
- Integrated agent workflow phase events
- Rich metadata (timestamp, sequence, pid, thread, caller, context)

### CLI Usage

```bash
python bin/workflow_orchestrator.py full \
    --source /config \
    --log-level DEBUG \
    --trace-log \
    --trace-log-file ./exports/workflow_trace.log \
    --strict-warnings
```

### Environment Variable Usage

```bash
export HA_AI_LOG_LEVEL=DEBUG
export HA_AI_TRACE_LOG=true
export HA_AI_TRACE_FILE=./exports/workflow_trace.log
python bin/workflow_orchestrator.py validate --source ./exports/export_20260323_072631
```

### Trace Record Example

```json
{
    "timestamp": "2026-03-23T09:02:18.511",
    "sequence": 127,
    "thread": "MainThread",
    "pid": 4120,
    "level": "INFO",
    "icon": null,
    "message": "Starting remote export to /config/ai_exports/export_20260323_090218",
    "emitted": true,
    "log_level": "DEBUG",
    "context": ["Remote Export"],
    "caller": {
        "file": "bin/workflow_orchestrator.py",
        "function": "export_from_remote",
        "line": 126
    }
}
```

### Integrated Phase Event Example

```json
{
    "timestamp": "2026-03-23T09:02:18.702",
    "sequence": 132,
    "thread": "MainThread",
    "pid": 4120,
    "type": "trace_event",
    "event": "integrated_agent_workflow.phase",
    "context": [],
    "details": {
        "phase": "phase_5_quality_gate_ladder",
        "status": "passed",
        "details": {
            "gates": ["export", "sanitize", "context", "validate"]
        }
    }
}
```

## New Debug Methods

### 1. Debug Variables (`debug_var`)

Log variable names and values with automatic formatting:

```python
from workflow_logger import get_logger

logger = get_logger()

# Simple values
user_id = 12345
logger.debug_var("user_id", user_id)
# Output: Variable: user_id = 12345

# Complex types (auto-formatted as JSON)
config = {
    "host": "homeassistant.local",
    "port": 8123,
    "ssl": True
}
logger.debug_var("config", config)
# Output:
# Variable: config = {
#   "host": "homeassistant.local",
#   "port": 8123,
#   "ssl": true
# }
```

### 2. Debug Function Calls (`debug_call`)

Log function calls with their arguments:

```python
# Before calling a function
logger.debug_call("process_entities", args=(entity_list,), kwargs={"filter": "sensor"})
# Output: Calling: process_entities([...], filter='sensor')
```

### 3. Debug Return Values (`debug_return`)

Log function return values:

```python
result = some_function()
logger.debug_return("some_function", result)
# Output: Returned from some_function: {'status': 'success', 'count': 42}
```

### 4. Function Entry/Exit Tracking

Track function entry and exit with context management:

```python
def my_function(arg1, arg2):
    logger.debug_enter("my_function", args=(arg1, arg2))

    try:
        # Function logic here
        result = arg1 + arg2

        logger.debug_exit("my_function", return_value=result)
        return result
    except Exception as e:
        logger.debug_exit("my_function")
        raise
```

### 5. Call Stack Display (`debug_stack`)

Display the current call stack:

```python
def nested_function():
    logger.debug_stack()
    # Outputs full call stack showing how we got here

def parent_function():
    nested_function()

parent_function()
```

## Automatic Function Tracing Decorator

The `@trace_calls()` decorator automatically logs function entry, exit, timing, and exceptions:

```python
from workflow_logger import trace_calls, get_logger

logger = get_logger()

@trace_calls(logger)
def process_config(config_file: str, validate: bool = True):
    """Process a configuration file."""
    # Your logic here
    return {"status": "success"}

# When called with DEBUG enabled:
result = process_config("config.yaml", validate=True)

# Output:
# → Entering: __main__.process_config('config.yaml', validate=True)
# ← Exiting: __main__.process_config (took 0.045s)
# Returned from __main__.process_config: {'status': 'success'}
```

## Real-World Example

Here's how to use the enhanced debugging in a typical workflow function:

```python
from workflow_logger import get_logger, trace_calls, LogLevel

logger = get_logger()
logger.set_log_level(LogLevel.DEBUG)

@trace_calls(logger)
def export_configuration(config_dir: str, output_dir: str):
    """Export Home Assistant configuration with debug logging."""

    logger.debug_var("config_dir", config_dir)
    logger.debug_var("output_dir", output_dir)

    # Check if directory exists
    if not os.path.exists(config_dir):
        logger.error(f"Config directory not found: {config_dir}")
        logger.debug_stack()  # Show how we got here
        return False

    # Process files
    files = os.listdir(config_dir)
    logger.debug_var("files_found", files)

    # Sanitize and export
    sanitized = sanitize_secrets(files)
    logger.debug_var("sanitized_count", len(sanitized))

    return True

# Usage
success = export_configuration("/config", "/tmp/export")
```

## Output Examples

### Normal (INFO) Mode

```
2026-02-07 16:21:23 [INFO] Starting export workflow
2026-02-07 16:21:24 [SUCCESS] Export completed
```

### DEBUG Mode

```
2026-02-07 16:21:23 [INFO] Starting export workflow
2026-02-07 16:21:23 [DEBUG] 🔍 Export configuration:
2026-02-07 16:21:23 [DEBUG] 🔍   - BIN_DIR: /usr/local/ha-ai-workflow/bin
2026-02-07 16:21:23 [DEBUG] 🔍   - CONFIG_DIR: /config
2026-02-07 16:21:23 [DEBUG] 🔍   - EXPORT_DIR: /config/ai_exports
2026-02-07 16:21:23 [DEBUG] 🔍 Variable: config_dir = '/config'
2026-02-07 16:21:23 [DEBUG] 🔍 Variable: output_dir = '/tmp/export'
2026-02-07 16:21:23 [VERBOSE] → Entering: export_configuration('/config', '/tmp/export')
2026-02-07 16:21:23 [DEBUG] 🔍 Variable: files_found = ['configuration.yaml', 'automations.yaml', ...]
2026-02-07 16:21:23 [DEBUG] 🔍 Variable: sanitized_count = 42
2026-02-07 16:21:23 [VERBOSE] ← Exiting: export_configuration (took 1.234s)
2026-02-07 16:21:23 [DEBUG] 🔍 Returned from export_configuration: True
2026-02-07 16:21:24 [SUCCESS] Export completed
```

## Best Practices

1. **Use `@trace_calls()` for key functions** - Automatically tracks entry/exit/timing
2. **Log important variables** with `debug_var()` - Helps track state changes
3. **Log function calls** with `debug_call()` before calling external functions
4. **Display call stack** with `debug_stack()` when errors occur
5. **Respect performance** - DEBUG mode adds overhead, use INFO for production
6. **Use trace log for deep diagnostics** - Enable `--trace-log` only when investigating issues or preparing PR evidence

## API Error Messages

The enhanced API client now provides detailed error messages:

### 401 Unauthorized Error

```
❌ Authentication failed (401 Unauthorized)
  SUPERVISOR_TOKEN is invalid or expired.
  Please generate a new Long-Lived Access Token:
  1. In Home Assistant: Profile → Security → Long-Lived Access Tokens
  2. Create new token and copy it
  3. Update via GUI Configuration or set SUPERVISOR_TOKEN environment variable
```

### Connection Test Output

```bash
$ python3 -c "from bin.ha_api_client import HomeAssistantAPI; \
    api = HomeAssistantAPI('your_token'); \
    success, msg = api.test_connection(); \
    print(msg)"

# Success:
✓ Connection successful

# Failure:
❌ Authentication failed (401 Unauthorized)
  SUPERVISOR_TOKEN is invalid or expired.
  [... remediation steps ...]
```

## Master Script Debug Mode

The master script now includes detailed debug logging:

```bash
$ ./ha_ai_master_script.sh export --log-level DEBUG

# Output includes:
🔍 Export configuration:
🔍   - BIN_DIR: /usr/local/ha-ai-workflow/bin
🔍   - CONFIG_DIR: /config
🔍   - EXPORT_DIR: /config/ai_exports
🔍   - Export name: ha_export_20260207_162123
🔍   - Temp directory: /tmp/ha_export_20260207_162123
🔍 Calling: python3 /usr/local/ha-ai-workflow/bin/ha_diagnostic_export.py --output-dir /tmp --name ha_export_20260207_162123 --config-dir /config
🔍 Tarball found: -rw-r--r-- 1 root root 2.4M Feb  7 16:21 /tmp/ha_export_20260207_162123.tar.gz
```

## Version Checking

Check script versions to detect old installations:

```bash
$ python3 /usr/local/ha-ai-workflow/bin/ha_diagnostic_export.py --version
ha_diagnostic_export.py 2.0.0

$ python3 /usr/local/ha-ai-workflow/bin/ha_diagnostic_export.py --help
HA Diagnostic Export v2.0.0

usage: ha_diagnostic_export.py [-h] [--version] [--output-dir OUTPUT_DIR]
                                [--name NAME] [--config-dir CONFIG_DIR] [--quiet]
```

## Troubleshooting

### If DEBUG output is not showing

1. Check log level: `echo $HA_AI_LOG_LEVEL`
2. Verify command: `./ha_ai_master_script.sh export --log-level DEBUG`
3. Check log file: `cat /config/ai_exports/workflow.log`

### If seeing version mismatch errors

1. Check installed version: `ha_diagnostic_export.py --version`
2. Re-run setup: `sudo ./setup.sh`
3. Verify symlink: `ls -la /usr/local/bin/ha-ai-workflow`

## Migration from Old Versions

If you have an old installation without `--config-dir` support:

```bash
# Check current version
python3 /usr/local/ha-ai-workflow/bin/ha_diagnostic_export.py --version

# If error "unrecognized arguments: --version", you have an old version
# Re-run setup to update:
cd /path/to/HA_AI_Gen_Workflow
sudo ./setup.sh

# Verify update
python3 /usr/local/ha-ai-workflow/bin/ha_diagnostic_export.py --version
# Should show: ha_diagnostic_export.py 2.0.0
```
