# Logging System Documentation

## Overview

The HA AI Gen Workflow now includes a comprehensive, centralized logging system that provides structured logging with multiple verbosity levels, file output, and diagnostic capabilities.

## Features

### 1. Multiple Log Levels

The logging system supports the following levels (from most to least verbose):

- **DEBUG**: Detailed debugging information for development
- **VERBOSE**: Detailed operational information
- **INFO**: General informational messages (default)
- **CONDENSED**: Only important messages
- **WARNING**: Warning messages only
- **ERROR**: Error messages only
- **CRITICAL**: Critical errors

### 2. File Output

All logs are written to a file with timestamps and structured formatting:
- Default location: `/config/ai_exports/workflow.log`
- Can be customized via `--log-file` option or environment variable
- Automatic directory creation
- Supports both text and JSON formats

### 3. Context Tracking

The logger maintains a context stack for better error diagnostics:
```python
logger.push_context("Export Operation")
# ... do work ...
logger.pop_context()
```

### 4. Diagnostic Reports

Generate comprehensive diagnostic reports for troubleshooting:
- Current configuration
- Context stack
- Recent log entries (last 50 lines)
- System information

## Usage

### From Shell Scripts

The master script (`ha_ai_master_script.sh`) supports logging options:

```bash
# Enable verbose logging
ha-ai-workflow export --verbose

# Set specific log level
ha-ai-workflow export --log-level DEBUG

# Use custom log file
ha-ai-workflow export --log-file /tmp/my-export.log

# Combine options
ha-ai-workflow export --verbose --log-file /custom/path.log
```

### From Python Scripts

```python
from workflow_logger import get_logger, configure_logger, LogLevel

# Get the global logger instance
logger = get_logger()

# Or configure a new logger
logger = configure_logger(
    log_level="INFO",
    log_file="/path/to/logfile.log",
    enable_console=True,
    enable_colors=True,
    log_format="text"  # or "json"
)

# Use the logger
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.success("Success message")
logger.progress("Progress update")

# With context
logger.push_context("My Operation")
try:
    # ... do work ...
    logger.info("Work completed")
except Exception as e:
    logger.log_exception(e, "Operation failed")
finally:
    logger.pop_context()

# Generate diagnostic report
logger.create_diagnostic_report("/tmp/diagnostic.md")
```

### From GUI

The Streamlit GUI includes a dedicated log viewer page:

1. Click "📋 View Logs" in the sidebar
2. Select log level to filter messages
3. View recent log entries
4. Download full log file
5. Generate diagnostic reports
6. Clear log file or view log directory

## Environment Variables

Configure logging via environment variables:

- `HA_AI_LOG_LEVEL`: Set default log level (DEBUG, VERBOSE, INFO, etc.)
- `HA_AI_LOG_FILE`: Set default log file path
- `HA_AI_LOG_DIR`: Set default log directory (defaults to `/config/ai_exports`)

Example:
```bash
export HA_AI_LOG_LEVEL=DEBUG
export HA_AI_LOG_DIR=/custom/log/path
ha-ai-workflow export
```

## Setup Script Enhancements

The enhanced `setup.sh` script now includes:

### Comprehensive Checks
1. ✅ Directory structure creation
2. ✅ System dependency verification (python3, git, pip, shellcheck)
3. ✅ Python dependency installation from requirements.txt
4. ✅ Python module import verification
5. ✅ Python script installation and permission setting
6. ✅ Shell script installation and validation
7. ✅ ShellCheck validation (if available)
8. ✅ Git repository initialization
9. ✅ Documentation creation
10. ✅ Validation tests
11. ✅ Basic functionality tests
12. ✅ Final integrity checks

### Usage

```bash
# Show help
sudo ./setup.sh --help

# Normal installation
sudo ./setup.sh

# Verbose mode (detailed output)
sudo ./setup.sh --verbose
```

### Features

- **Automatic dependency resolution**: Tries multiple installation methods
- **Validation**: Tests imports and script executability
- **Logging**: All operations logged to `/config/ai_exports/setup.log`
- **Comprehensive reporting**: Summary of installed files and any issues
- **Safe**: Checks before overwriting, validates before proceeding

## Log Output Examples

### Text Format (Default)
```
2026-02-05 07:00:00 [INFO     ] ℹ Starting export workflow
2026-02-05 07:00:01 [VERBOSE  ] → Connecting to remote host
2026-02-05 07:00:02 [INFO     ] ✓ Export completed successfully
2026-02-05 07:00:03 [WARNING  ] ⚠ Some files were skipped
2026-02-05 07:00:04 [ERROR    ] ✗ Failed to connect to host
```

### JSON Format
```json
{"timestamp": "2026-02-05 07:00:00", "level": "INFO", "message": "Starting export", "context": ["Export"]}
{"timestamp": "2026-02-05 07:00:01", "level": "ERROR", "message": "Connection failed", "context": ["Export", "SSH"]}
```

## Best Practices

1. **Use appropriate log levels**: 
   - DEBUG for development/troubleshooting
   - INFO for normal operations
   - ERROR for problems that need attention

2. **Add context for operations**:
   ```python
   logger.push_context("Export")
   # ... operations ...
   logger.pop_context()
   ```

3. **Log exceptions with context**:
   ```python
   try:
       risky_operation()
   except Exception as e:
       logger.log_exception(e, "Operation context")
   ```

4. **Generate diagnostic reports on failures**:
   ```python
   if operation_failed:
       logger.create_diagnostic_report("/tmp/debug.md")
   ```

5. **Use verbose mode for troubleshooting**:
   ```bash
   ha-ai-workflow export --verbose --log-level DEBUG
   ```

## Diagnostic Report Example

```markdown
# Diagnostic Report
Generated: 2026-02-05 07:00:00

## Configuration
- Log Level: INFO
- Log File: /config/ai_exports/workflow.log
- Console Output: True
- Colors Enabled: True
- Format: text

## Current Context
1. Export Operation
2. Remote Connection

## Recent Log Entries (Last 50 lines)
[Recent log entries displayed here...]
```

## Integration Points

The logging system is integrated throughout the workflow:

1. **setup.sh**: Logs all installation steps
2. **ha_ai_master_script.sh**: Logs workflow execution
3. **workflow_orchestrator.py**: Logs orchestration steps
4. **workflow_gui.py**: Displays and manages logs
5. **All Python modules**: Can use the global logger

## Troubleshooting

### Logs not appearing?
- Check log file path: `echo $HA_AI_LOG_FILE`
- Verify directory permissions: `ls -la /config/ai_exports/`
- Check log level: Use `--log-level DEBUG` to see all messages

### Permission denied errors?
- Run setup as root: `sudo ./setup.sh`
- Check directory ownership: `ls -la /config/`

### GUI not showing logs?
- Verify log file exists: `ls -la /config/ai_exports/workflow.log`
- Check Streamlit is running: `ps aux | grep streamlit`
- Refresh the page or restart Streamlit

## Future Enhancements

Potential future improvements:
- Log rotation (size-based or time-based)
- Remote logging (syslog, external services)
- Real-time log streaming in GUI
- Log search and filtering
- Performance metrics logging
- Alert notifications for critical errors

---

For more information, see:
- `bin/workflow_logger.py` - Logger implementation
- `tests/test_workflow_logger.py` - Comprehensive tests
- `docs/DEVELOPER_GUIDE.md` - Development documentation
