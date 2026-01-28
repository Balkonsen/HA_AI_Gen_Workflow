# s6-overlay-suexec Error - Complete Fix Guide

## Problem Explanation

### What is the s6-overlay-suexec error?

The error message `s6-overlay-suexec: fatal: can only run as pid 1` occurs when:

1. **s6-overlay** is an init system used in many Docker containers, particularly in Home Assistant add-ons
2. The add-on's configuration had `init: false` which tells Home Assistant NOT to inject s6-overlay
3. However, the startup script was still trying to USE s6-overlay tools (specifically `bashio`)
4. This created a conflict: the script expected s6-overlay to be available, but it was disabled

### Why does this happen?

When a Docker container starts:
- The first process (PID 1) has special responsibilities for managing child processes
- s6-overlay is designed to run as PID 1 and manage other processes
- When `init: false` is set, Home Assistant runs your script directly as PID 1
- If the script then tries to call s6-overlay tools, they fail because s6-overlay isn't running

### The Original Problem

```bash
#!/usr/bin/with-contenv bashio  # ← This requires s6-overlay!
# ... rest of script using bashio:: functions
```

But in `config.yaml`:
```yaml
init: false  # ← This DISABLES s6-overlay!
```

Result: **ERROR** - Script can't run because s6-overlay isn't available.

## The Complete Solution

### What We Changed

#### 1. Removed s6-overlay Dependency

**Before:**
```bash
#!/usr/bin/with-contenv bashio
EXPORT_PATH=$(bashio::config 'export_path')
bashio::log.info "Starting..."
```

**After:**
```bash
#!/usr/bin/env bash
EXPORT_PATH=$(get_config 'export_path' '/config/ai_exports')
log_info "Starting..."
```

#### 2. Implemented Native Bash Configuration Reading

Created a `get_config()` function that:
- Reads JSON config files directly using `jq`
- Has TWO fallback locations for config files
- Provides default values if config is missing
- Works without any s6-overlay dependencies

```bash
get_config() {
    local key="$1"
    local default="$2"
    
    # Try primary config file
    if [[ -f "/data/options.json" ]]; then
        value=$(jq -r ".${key}" /data/options.json)
    fi
    
    # Fallback to secondary location
    if [[ -z "${value}" ]] && [[ -f "/config/options.json" ]]; then
        value=$(jq -r ".${key}" /config/options.json)
    fi
    
    # Use default if still empty
    if [[ -z "${value}" ]]; then
        value="${default}"
    fi
    
    echo "${value}"
}
```

#### 3. Custom Logging System

Replaced all `bashio::log.*` functions with native bash logging:

```bash
log_info()    # Green [INFO] messages
log_warning() # Yellow [WARNING] messages  
log_error()   # Red [ERROR] messages
log_debug()   # Blue [DEBUG] messages (only if debug enabled)
```

Features:
- Color-coded output for easy reading
- Timestamps on every message
- Debug mode for detailed troubleshooting
- No external dependencies

#### 4. Multiple Failsafe Mechanisms

##### Failsafe #1: Auto-install Missing Dependencies
```bash
if ! command -v jq &> /dev/null; then
    log_error "jq is not installed - installing now..."
    apk add --no-cache jq
fi
```

##### Failsafe #2: Config File Fallbacks
```bash
CONFIG_FILE="/data/options.json"          # Primary location
CONFIG_FILE_FALLBACK="/config/options.json"  # Fallback location
# Plus default values for every option
```

##### Failsafe #3: Directory Creation with Retries
```bash
if ! mkdir -p "${dir}" 2>/dev/null; then
    log_warning "Attempting to create with elevated permissions..."
    sudo mkdir -p "${dir}"
fi
```

##### Failsafe #4: API Testing with Retries
```bash
retry_count=0
max_retries=3
while [[ ${retry_count} -lt ${max_retries} ]]; do
    # Test API connection
    # Retry with 2-second delay if failed
done
```

##### Failsafe #5: Ingress URL - 3 Detection Methods
```bash
# Method 1: Environment variable
if [[ -n "${INGRESS_ENTRY}" ]]; then
    INGRESS_URL="${INGRESS_ENTRY}"
fi

# Method 2: Supervisor API query
if [[ -z "${INGRESS_URL}" ]]; then
    INGRESS_URL=$(curl -s ... | jq -r '.data.ingress_url')
fi

# Method 3: Fallback default
if [[ -z "${INGRESS_URL}" ]]; then
    INGRESS_URL="/api/hassio_ingress/ha_ai_gen_workflow"
fi
```

##### Failsafe #6: Application Checks Before Start
```bash
# Check if Streamlit is installed
if ! command -v streamlit &> /dev/null; then
    pip3 install --no-cache-dir streamlit
fi

# Check if main script exists
if [[ ! -f "/app/bin/workflow_gui.py" ]]; then
    log_error "workflow_gui.py not found"
    exit 1
fi
```

### 5. Debug and Verbose Mode

Added two new configuration options:

```yaml
options:
  debug_mode: false  # Detailed debug logs
  verbose: false     # Verbose output
```

Enable these to get detailed information about:
- Configuration loading process
- Which config file is being used
- Default values being applied
- API connection attempts
- Ingress URL detection methods
- Environment variable values
- Command arguments

Example debug output:
```
[DEBUG] 2026-01-28 11:35:21 - Reading config key: export_path
[DEBUG] 2026-01-28 11:35:21 - Reading from primary config: /data/options.json
[DEBUG] 2026-01-28 11:35:21 - Config file: /data/options.json
[INFO]  2026-01-28 11:35:21 - Configuration loaded successfully:
[INFO]  2026-01-28 11:35:21 -   Export path: /config/ai_exports
```

## How to Use

### For Regular Users

**Nothing to do!** The fix is automatic. Just:
1. Update to version 1.0.2 or later
2. Restart the add-on
3. Everything should work

### For Troubleshooting

If you encounter issues, enable debug mode:

1. Go to the add-on configuration page
2. Add these options:
   ```yaml
   debug_mode: true
   verbose: true
   ```
3. Save and restart the add-on
4. Check the logs for detailed information

### Log Reading Guide

**Green [INFO]** - Normal operation, everything is working
```
[INFO] 2026-01-28 11:35:21 - HA AI Gen Workflow Add-on Starting
```

**Yellow [WARNING]** - Something unexpected but not critical
```
[WARNING] 2026-01-28 11:35:21 - API test failed, continuing anyway...
```

**Red [ERROR]** - Critical issue that needs attention
```
[ERROR] 2026-01-28 11:35:21 - Failed to write workflow configuration file
```

**Blue [DEBUG]** - Detailed info (only visible when debug enabled)
```
[DEBUG] 2026-01-28 11:35:21 - Using default value for ssh_enabled: false
```

## Technical Details

### Why We Keep `init: false`

We maintain `init: false` in the configuration because:

1. **Simpler Process Management**: The add-on runs a single main process (Streamlit), so we don't need s6-overlay's process supervision
2. **Faster Startup**: No overhead from initializing s6-overlay
3. **Less Complexity**: Fewer moving parts means fewer things that can go wrong
4. **Standard Docker Practice**: Many modern Docker containers run without init systems

### Configuration Reading Logic

```
1. Check /data/options.json (Home Assistant's standard location)
   ├─ Found? Use it
   └─ Not found? Continue

2. Check /config/options.json (fallback location)
   ├─ Found? Use it
   └─ Not found? Continue

3. Use hardcoded default value
   └─ Always succeeds
```

### Dependencies

The fixed script requires:
- **bash** (always available)
- **jq** (auto-installed if missing)
- **curl** (included in Home Assistant base images)
- **streamlit** (installed via Dockerfile, fallback in script)

No s6-overlay or bashio required!

## Verification

To verify the fix is working:

1. Check the add-on logs - should see:
   ```
   [INFO] HA AI Gen Workflow Add-on Starting
   [INFO] Configuration loaded successfully
   [INFO] SUPERVISOR_TOKEN available - HA API access enabled
   [INFO] Home Assistant API connection verified
   [INFO] Starting Streamlit GUI...
   ```

2. No errors about "s6-overlay-suexec" or "can only run as pid 1"

3. The web UI should be accessible

## Support

If you still encounter the s6-overlay error after this fix:

1. Enable debug mode: `debug_mode: true` and `verbose: true`
2. Copy the full logs
3. Create an issue at: https://github.com/Balkonsen/HA_AI_Gen_Workflow/issues
4. Include:
   - Add-on version
   - Home Assistant version
   - Full logs with debug enabled
   - Steps to reproduce

## Summary

✅ **Removed**: s6-overlay dependency  
✅ **Added**: Native bash configuration reading  
✅ **Added**: Custom logging system  
✅ **Added**: Multiple failsafe mechanisms  
✅ **Added**: Debug and verbose modes  
✅ **Added**: Comprehensive error handling  
✅ **Result**: Fully functional add-on without s6-overlay conflicts
