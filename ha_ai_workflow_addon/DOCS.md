# HA AI Gen Workflow Add-on

This add-on provides a web-based graphical interface for the Home Assistant AI Generation Workflow.

## Features

- 📤 **Export Configuration** - Export your Home Assistant configuration safely
- 🔐 **Secrets Sanitization** - Automatically replace sensitive data with labeled placeholders
- 🤖 **AI Context Generation** - Generate AI-ready context files for assistants
- 📥 **Import Configuration** - Import AI-modified configurations with automatic secret restoration
- 🔍 **Validation** - Verify configurations before deployment
- 📡 **SSH Support** - Connect to remote Home Assistant instances

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

- Secrets are automatically sanitized during export
- Encrypted secrets are stored separately
- Never share the secrets directory with AI assistants
- All changes are validated before deployment

## Troubleshooting

### Add-on Won't Start

1. Check the add-on logs for error messages
2. Verify the configured paths exist and are writable
3. Ensure Home Assistant API access is enabled

### SSH Connection Failed

1. Verify the SSH host is reachable
2. Check SSH credentials and key permissions
3. Ensure SSH is enabled on the target system

### Import Failed

1. Review the validation errors in the UI
2. Check the import files for syntax errors
3. Verify all required secrets are available

## Support

For issues and feature requests, visit:
https://github.com/Balkonsen/HA_AI_Gen_Workflow/issues
