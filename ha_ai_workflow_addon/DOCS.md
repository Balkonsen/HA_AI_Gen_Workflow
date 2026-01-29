# HA AI Gen Workflow Add-on

This add-on provides a web-based graphical interface for the Home Assistant AI Generation Workflow.

## Features

- 📤 **Export Configuration** - Export your Home Assistant configuration safely
- 🔐 **Secrets Sanitization** - Automatically replace sensitive data with labeled placeholders
- 🤖 **AI Context Generation** - Generate AI-ready context files for assistants
- 📥 **Import Configuration** - Import AI-modified configurations with automatic secret restoration
- 🔍 **Validation** - Verify configurations before deployment
- 📡 **SSH Support** - Connect to remote Home Assistant instances
- 🔑 **Secure API Access** - Uses SUPERVISOR_TOKEN for authenticated HA API calls

## Configuration

### Required Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `export_path` | Directory for exported configurations | `/config/ai_exports` |
| `import_path` | Directory for configurations to import | `/config/ai_imports` |
| `secrets_path` | Directory for encrypted secrets storage | `/config/ai_secrets` |

### SSH Settings (Optional)

| Setting | Description | Default |
|---------|-------------|---------|
| `ssh_enabled` | Enable SSH for remote HA | `false` |
| `ssh_host` | SSH host address | (empty) |
| `ssh_user` | SSH username | `root` |
| `ssh_port` | SSH port | `22` |
| `ssh_key_path` | Path to SSH private key | (empty) |
| `remote_config_path` | Remote config directory | `/config` |

### Logging and Debug Settings (Optional)

| Setting | Description | Default |
|---------|-------------|---------|
| `debug_mode` | Enable detailed debug logging | `false` |
| `verbose` | Enable verbose output | `false` |

**Note**: Enable `debug_mode` or `verbose` to troubleshoot startup issues. This provides detailed logs about configuration loading, API connectivity, and initialization steps.

## Usage

### Step 1: Configure Paths

After installation, configure the export and import paths in the add-on configuration.
The default paths work for most installations.

### Step 2: Export Configuration

1. Open the add-on web UI
2. Navigate to **Export** 
3. Select your export mode (Local or SSH Remote)
4. Click **Start Export**

### Step 3: Generate AI Context

1. Navigate to **AI Context**
2. Select the export to process
3. Click **Generate AI Context**
4. Copy the generated files to your AI assistant

### Step 4: Import Modified Configuration

1. Place AI-modified files in the import directory
2. Navigate to **Import**
3. Enable **Dry run** for preview first
4. Click **Start Import**

## Security

This add-on follows Home Assistant security best practices:

### Authentication
- Uses **SUPERVISOR_TOKEN** for all Home Assistant API interactions
- Token is automatically provided by the Supervisor (never stored in files)
- All API calls use Bearer token authentication

### Permissions
- **homeassistant_api**: Enabled for configuration validation and restart
- **hassio_api**: Enabled for add-on and system information
- **hassio_role**: Set to `homeassistant` (minimum required)
- **auth_api**: Enabled for user authentication in the UI
- **panel_admin**: Only administrators can access the add-on

### Data Protection
- Secrets are automatically sanitized during export
- Encrypted secrets are stored separately from configuration
- Never share the secrets directory with AI assistants
- All configuration changes are validated before deployment

### File System Access
- `/config` - Read/Write (required for export/import)
- `/ssl` - Read-only (for SSH key access)
- `/share` - Read/Write (for file sharing)

## Troubleshooting

### s6-overlay-suexec Error (FIXED in v1.0.2)

**Error**: `s6-overlay-suexec: fatal: can only run as pid 1`

**Status**: This error has been completely resolved in version 1.0.2. The add-on no longer depends on s6-overlay and uses native bash scripts instead.

**What was changed**:
- Removed dependency on s6-overlay bashio functions
- Rewrote startup script to use standard bash
- Added comprehensive fallback mechanisms
- Implemented custom logging system

If you still see this error after upgrading to v1.0.2, please:
1. Restart the add-on
2. Enable `debug_mode: true` in the configuration
3. Check the logs for detailed information
4. Report the issue with full logs at: https://github.com/Balkonsen/HA_AI_Gen_Workflow/issues

### Add-on Won't Start

1. **Enable debug logging**: Set `debug_mode: true` and `verbose: true` in add-on configuration
2. Check the add-on logs for error messages (look for RED [ERROR] messages)
3. Verify the configured paths exist and are writable
4. Ensure Home Assistant API access is enabled
5. Check if SUPERVISOR_TOKEN is available in logs (look for "SUPERVISOR_TOKEN available" message)

### Configuration Loading Issues

The add-on has multiple fallback mechanisms:
- Primary config: `/data/options.json`
- Fallback config: `/config/options.json`
- Default values for all options

If you see warnings about missing config files:
1. This is normal if running outside Home Assistant
2. The add-on will use default values
3. Enable `debug_mode` to see which values are being used

### API Connection Issues

1. Verify add-on has `homeassistant_api: true` permission
2. Check add-on logs for "API connection verified" message
3. Restart the add-on if connection was established after startup

### SSH Connection Failed

1. Verify the SSH host is reachable
2. Check SSH credentials and key permissions
3. Ensure SSH is enabled on the target system

### Import Failed

1. Review the validation errors in the UI
2. Check the import files for syntax errors
3. Verify all required secrets are available

### Web UI Shows 404 Not Found (FIXED in v1.0.3)

**Error**: Opening the add-on web UI shows "404 Not found"

**Status**: This error has been resolved in version 1.0.3. The issue was related to Streamlit's websocket compression setting when running behind Home Assistant's Ingress proxy.

**What was changed**:
- Added `--server.enableWebsocketCompression=false` flag to Streamlit configuration
- This is required for Streamlit 1.10+ to work correctly behind reverse proxies/ingress

**Important Notes**:
- The URL shown in the logs (e.g., `http://0.0.0.0:8501/api/hassio_ingress/...`) is the **internal** container address
- **Do NOT try to access this URL directly** - it won't work from outside the container
- **Access the add-on through Home Assistant's sidebar** or the add-on's "Open Web UI" button
- The add-on uses Home Assistant's Ingress feature, which proxies requests through HA's web interface

**About SSH Server**:
- **SSH server is NOT required** for the add-on to work
- SSH is only needed if you want to export/import configurations from/to a **remote** Home Assistant instance
- For local usage (most common), the add-on accesses your config directly via `/config` mount
- Enable SSH only if you're managing a separate/remote Home Assistant installation

If you still see 404 errors after upgrading to v1.0.3:
1. Restart the add-on completely (stop, then start)
2. Clear your browser cache and reload the page
3. Try accessing from a different browser or incognito/private mode
4. Check the add-on logs for any error messages
5. Enable `debug_mode: true` for detailed logging
6. Report the issue with full logs at: https://github.com/Balkonsen/HA_AI_Gen_Workflow/issues

## Support

For issues and feature requests, visit:
https://github.com/Balkonsen/HA_AI_Gen_Workflow/issues
