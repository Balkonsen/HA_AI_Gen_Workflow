# Home Assistant API Configuration Guide

This guide explains how the HA AI Gen Workflow connects to Home Assistant's API and how to configure it for different use cases.

## Overview

The workflow supports two modes of operation when connecting to Home Assistant:

1. **Internal Mode (Add-on)** - When running as a Home Assistant add-on
2. **External Mode (Standalone)** - When running outside of Home Assistant (e.g., on your development machine)

## API Endpoints

### Internal Mode (Add-on)

When running as a Home Assistant add-on, the workflow automatically uses internal supervisor endpoints:

- **API Base URL:** `http://supervisor/core/api`
- **Supervisor Base URL:** `http://supervisor`
- **Add-ons Endpoint:** `http://supervisor/addons`
- **Supervisor Info:** `http://supervisor/supervisor/info`

**Authentication:** Uses the `SUPERVISOR_TOKEN` that is automatically injected by Home Assistant into add-on containers.

### External Mode (Standalone)

When running standalone (outside of a Home Assistant add-on), the workflow uses external API endpoints:

- **API Base URL:** `http://{HA_HOST}:{PORT}/api`
- **Supervisor Base URL:** `http://{HA_HOST}:{PORT}/api/hassio`
- **Add-ons Endpoint:** `http://{HA_HOST}:{PORT}/api/hassio/addons`
- **Supervisor Info:** `http://{HA_HOST}:{PORT}/api/hassio/supervisor/info`

**Authentication:** Uses a Long-Lived Access Token that you create in Home Assistant.

## Configuration

### Method 1: Environment Variables (Recommended for Standalone)

Set the following environment variables:

```bash
# Home Assistant URL (triggers external mode)
export HA_URL="http://192.168.1.100:8123"

# Long-Lived Access Token
export SUPERVISOR_TOKEN="your_long_lived_token_here"
```

You can also use HTTPS:

```bash
export HA_URL="https://homeassistant.local:8123"
export SUPERVISOR_TOKEN="your_long_lived_token_here"
```

### Method 2: Python API

When using the Python API directly:

```python
from bin.ha_api_client import HomeAssistantAPI
from bin.ha_diagnostic_export import HAConfigExporter

# Internal mode (add-on) - auto-detected
api = HomeAssistantAPI()
exporter = HAConfigExporter()

# External mode (standalone) - explicit ha_url
api = HomeAssistantAPI(
    token="eyJhbGc...",
    ha_url="http://192.168.1.100:8123"
)

exporter = HAConfigExporter(
    ha_url="http://192.168.1.100:8123"
)
```

### Method 3: .env File (For CLI Usage)

Create a `.env` file in your installation directory (default: `/usr/local/ha-ai-workflow/`):

```bash
# .env file
HA_URL=http://192.168.1.100:8123
SUPERVISOR_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

The CLI scripts will automatically load these variables.

## Creating a Long-Lived Access Token

For external mode, you need to create a Long-Lived Access Token in Home Assistant:

1. Open Home Assistant web interface
2. Click on your profile (bottom left)
3. Scroll down to "**Long-Lived Access Tokens**" section
4. Click "**Create Token**"
5. Give it a name (e.g., "HA AI Workflow")
6. Copy the token (it will only be shown once!)
7. Use this token in your configuration

**Important:** Store the token securely. Never commit it to version control.

## Auto-Detection Logic

The system automatically detects which mode to use:

```python
# Decision flow:
if ha_url is provided (via parameter or HA_URL env var):
    → Use External Mode
    → Connect to http://{ha_url}/api/hassio/...
else:
    → Use Internal Mode
    → Connect to http://supervisor/...
```

## Comparison with Example Script

The implementation matches the working example script pattern:

### Example Script (External Mode)

```bash
HA_URL="http://192.168.178.22:8123"
HA_TOKEN="eyJhbGc..."

curl -H "Authorization: Bearer ${HA_TOKEN}" \
     "${HA_URL}/api/hassio/addons"
```

### This Workflow (External Mode)

```python
api = HomeAssistantAPI(
    token="eyJhbGc...",
    ha_url="http://192.168.178.22:8123"
)
api.get_addons()  # Calls: http://192.168.178.22:8123/api/hassio/addons
```

Both use the same endpoint format: `{HA_URL}/api/hassio/addons`

## Troubleshooting

### 401 Unauthorized Error

**Problem:** API returns 401 status code

**Solutions:**

1. Verify token is valid (check it hasn't expired)
2. Create a new Long-Lived Access Token
3. Update your configuration with the new token

### Connection Timeout

**Problem:** Cannot connect to Home Assistant

**Solutions:**

1. Verify Home Assistant is running
2. Check the URL/port are correct
3. Ensure firewall allows connection
4. Try using IP address instead of hostname

### 404 Not Found for /api/hassio/

**Problem:** Supervisor endpoints return 404

**Solutions:**

1. Verify you're running Home Assistant OS (not Container/Core)
2. Supervisor API is only available in Home Assistant OS
3. Some features require supervisor - they won't work in Container/Core installations

### No Addons Listed

**Problem:** `get_addons()` returns empty list

**Possible Causes:**

1. No add-ons are installed
2. Using Core/Container (no supervisor)
3. Token lacks required permissions

## API Reference

### HomeAssistantAPI Class

```python
class HomeAssistantAPI:
    def __init__(self, token: str | None = None, ha_url: str | None = None)

    # Core API Methods
    def get_config() -> dict | None
    def get_states() -> list[dict] | None
    def get_state(entity_id: str) -> dict | None
    def call_service(domain: str, service: str, data: dict = None) -> bool
    def check_config() -> dict | None
    def restart_core() -> bool

    # Supervisor API Methods
    def get_supervisor_info() -> dict | None
    def get_core_info() -> dict | None
    def get_addons() -> dict | None
    def get_addon_info(slug: str) -> dict | None

    # Utility Methods
    def test_connection() -> tuple[bool, str]
    @property
    def is_available() -> bool
```

### HAConfigExporter Class

```python
class HAConfigExporter:
    def __init__(
        self,
        output_dir: str = "/tmp/ha_export",
        config_dir: str | None = None,
        ha_url: str | None = None
    )

    # Uses same dual-mode logic as HomeAssistantAPI
    # Internal methods automatically use correct endpoints
```

## Security Best Practices

1. **Never commit tokens** to version control
2. **Use environment variables** or `.env` files for tokens
3. **Rotate tokens regularly** (create new, delete old)
4. **Limit token scope** if possible (though HA doesn't currently support scoped tokens)
5. **Use HTTPS** when connecting remotely
6. **Store tokens encrypted** when persisting to disk

## Migration from Old Implementation

If you were using the old implementation that only supported internal mode:

**Before:**

```python
# Only worked as add-on
exporter = HAConfigExporter()
```

**After:**

```python
# Still works as add-on (backward compatible)
exporter = HAConfigExporter()

# Now also works standalone!
exporter = HAConfigExporter(ha_url="http://192.168.1.100:8123")
```

No changes needed to existing add-on usage - it remains fully backward compatible.

## Support

For issues or questions:

- GitHub Issues: <https://github.com/Balkonsen/HA_AI_Gen_Workflow/issues>
- Documentation: <https://github.com/Balkonsen/HA_AI_Gen_Workflow/tree/main/docs>
