# Home Assistant AI Workflow Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024+-blue.svg)](https://www.home-assistant.io/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/Balkonsen/HA_AI_Gen_Workflow)
[![Coverage](https://img.shields.io/badge/coverage-80%25-green.svg)](https://github.com/Balkonsen/HA_AI_Gen_Workflow)

> **Automated export, AI-powered development, and git-versioned import workflow for Home Assistant**

Transform your Home Assistant configuration management with AI assistance while maintaining complete control through git versioning and automated validation.

## 🏠 **Home Assistant Add-on Installation (Recommended)**

Install this workflow directly in Home Assistant with a graphical interface:

### Quick Installation

1. **Add Repository to Home Assistant:**
   - Navigate to **Settings** → **Add-ons** → **Add-on Store**
   - Click the **⋮** menu (top right) → **Repositories**
   - Add this repository URL:
     ```
     https://github.com/Balkonsen/HA_AI_Gen_Workflow
     ```
   - Click **Add** → **Close**

2. **Install the Add-on:**
   - Find **"HA AI Gen Workflow"** in the Add-on Store
   - Click **Install**
   - Wait for installation to complete

3. **Start and Access:**
   - Go to the add-on page and click **Start**
   - Enable **"Show in sidebar"** for easy access
   - Click **"Open Web UI"** or use the sidebar link

### Add-on Features

- 🖥️ **Web-based GUI** - Full Streamlit interface integrated into Home Assistant
- 📤 **One-click Export** - Export and sanitize your configuration
- 🤖 **AI Context Generation** - Generate AI-ready files automatically
- 📥 **Safe Import** - Import AI-modified configs with validation
- 🔐 **Automatic Secret Handling** - Secrets sanitized and restored automatically
- 📡 **SSH Support** - Connect to remote HA instances

---

## 🆕 **Features Overview**

This project includes:
- ✅ **SSH Remote Support** - Export/Import from/to remote HA instances
- ✅ **Encrypted Secrets Management** - Secrets stored separately with AES encryption
- ✅ **Labeled Placeholders** - AI-compatible secret labels for automatic restoration
- ✅ **VS Code Integration** - Tasks and launch configurations for full IDE workflow
- ✅ **Streamlit GUI** - Graphical interface for the complete workflow
- ✅ **Configurable Paths** - Flexible export/import directory configuration
- ✅ **Home Assistant Add-on** - Native integration with HA Supervisor

👉 **Quick Start**: See [GETTING_STARTED.md](GETTING_STARTED.md)  
👉 **For Developers**: See [docs/deployment_guide.md](docs/deployment_guide.md)  
👉 **Quick Reference**: See [docs/quick_reference.md](docs/quick_reference.md)

## ✨ Features

- 🔒 **Automated Sanitization**: Removes all sensitive data (passwords, tokens, IPs, emails)
- 🔐 **Encrypted Secrets**: Secrets stored separately with Fernet (AES-128) encryption
- 📍 **Labeled Placeholders**: `<<HA_SECRET_PASSWORD_001>>` format for AI compatibility
- 🤖 **AI-Ready Context**: Generates optimized prompts for AI assistants (Claude, ChatGPT, etc.)
- 📡 **SSH Remote Access**: Export/import from remote HA installations
- 📦 **Complete Export**: Entities, devices, configurations, automations, scripts, add-ons
- 🌳 **Git Versioning**: Full version control with automatic branching and merging
- ✅ **Validation**: Automatic configuration checking before deployment
- 🔄 **Automated Workflow**: One-command export and import
- 🖥️ **GUI Option**: Streamlit-based graphical interface
- 💻 **VS Code Integration**: Full IDE support with tasks and debugging
- 🏠 **Home Assistant Add-on**: Native Supervisor integration with sidebar panel

## 🎯 What Can AI Help You Build?

With this system, AI assistants can help you:

- ✅ Create complex automations based on your actual devices
- ✅ Design beautiful dashboards leveraging your entities
- ✅ Write helper scripts and template sensors
- ✅ Optimize existing configurations
- ✅ Debug configuration issues
- ✅ Integrate new devices and services
- ✅ Build custom components

**All while never seeing your passwords, tokens, or sensitive data!**

---

## 📋 Alternative Installation Methods

The add-on installation above is recommended for most users. For advanced users or development, see below.

### Prerequisites (for manual installation)
- Home Assistant OS or Supervised installation
- SSH access to Home Assistant host (for remote mode)
- Python 3.8 or higher
- Git (usually pre-installed)
- 500MB free space for exports

### 💻 Windows Installation

For Windows users, we provide a dedicated PowerShell installer:

1. **Download the repository** or clone it:
   ```powershell
   git clone https://github.com/Balkonsen/HA_AI_Gen_Workflow.git
   cd HA_AI_Gen_Workflow
   ```

2. **Run the installer as Administrator**:
   ```powershell
   # Right-click PowerShell -> Run as Administrator
   .\install_windows.ps1
   ```

The installer will:
- ✅ Check and validate dependencies (Python, Git)
- ✅ Create necessary directory structure
- ✅ Install Python packages (PyYAML, etc.)
- ✅ Set up the workflow scripts
- ✅ Initialize Git repository
- ✅ Add commands to PATH

After installation, restart your terminal and use:
```powershell
ha-ai-workflow.ps1 export
ha-ai-workflow.ps1 import
```

## 🚀 Quick Start

### Option 1: VS Code (Recommended)

1. Clone the repository
2. Open in VS Code
3. Run: `Terminal > Run Task > 🏠 HA Workflow: Setup Configuration`
4. Configure SSH and paths interactively
5. Run: `Terminal > Run Task > 🚀 HA Workflow: Full Pipeline`

### Option 2: Command Line

```bash
# Setup configuration
python3 bin/workflow_orchestrator.py setup

# Run full pipeline (local)
python3 bin/workflow_orchestrator.py full --source /config

# Or for remote HA
python3 bin/workflow_orchestrator.py full --remote
```

### Option 3: GUI (Streamlit)

```bash
pip install streamlit
streamlit run bin/workflow_gui.py
```

## 📡 SSH Configuration

For remote Home Assistant access, configure SSH in `workflow_config.yaml`:

```yaml
ssh:
  enabled: true
  host: "192.168.1.100"
  port: 22
  user: "root"
  auth_method: "key"
  key_path: "~/.ssh/id_rsa"
  remote_config_path: "/config"
```

## 🔐 Secrets Handling

### How It Works

1. **Export**: Sensitive data is detected and replaced with labeled placeholders
   ```yaml
   # Original
   password: my_secret_password
   
   # Exported
   password: <<HA_SECRET_PASSWORD_001>>
   ```

2. **Storage**: Actual values are encrypted and stored separately in `./secrets/`

3. **AI Context**: Labels and descriptions (no values) are included for AI
   ```json
   {
     "HA_SECRET_PASSWORD_001": {
       "type": "PASSWORD",
       "description": "Secret from password field",
       "placeholder": "<<HA_SECRET_PASSWORD_001>>"
     }
   }
   ```

4. **Import**: Labels are automatically restored to actual values

### Workflow Example

```bash
# 1. Export with sanitization
python3 bin/workflow_orchestrator.py export --source /config

# 2. AI modifies files (preserves <<HA_SECRET_*>> labels)

# 3. Import with automatic secret restoration
python3 bin/workflow_orchestrator.py import --source ./imports/ai_modified --target /config
```

## 🎯 First Export

```bash
# View the AI-ready prompt
cat /config/ai_exports/ha_export_*/AI_PROMPT.md
```

**Share with AI:**
- Upload `AI_PROMPT.md` and `AI_CONTEXT.json`
- DO NOT share the `secrets/` directory
- Ask AI to create automations, dashboards, or scripts

### 4. Import AI-Generated Configs

```bash
# 1. Place AI-generated files here:
/config/ai_imports/pending/

# 2. Run import
ha-ai-workflow import

# 3. Follow prompts:
# - Enter branch name: "ai-lighting-automation"
# - Review changes
# - Type 'DEPLOY' to confirm
```

## 📖 Detailed Usage

### Export Workflow

```bash
# Standard export
ha-ai-workflow export

# Automated mode (no prompts)
ha-ai-workflow export --auto

# Check what was exported
ha-ai-workflow status
```

**What Gets Exported:**

✅ Configuration files (YAML, JSON)
✅ Entity registry (all 245+ entities)
✅ Device registry (all 45+ devices)
✅ Automations and scripts
✅ Integration details
✅ Add-on configurations
✅ System diagnostics

❌ Databases (excluded)
❌ Log files (excluded)
❌ Secrets (sanitized, backed up separately)

### Import Workflow

```bash
# Interactive import
ha-ai-workflow import

# Automated import (CI/CD)
ha-ai-workflow import --auto
```

**Import Process:**

1. Scans `/config/ai_imports/pending/`
2. Creates new git branch
3. Restores secrets from backup
4. Validates configuration
5. Shows diff of changes
6. Merges to main branch
7. Restarts Home Assistant
8. Archives imported files

### Git Versioning

Every action is versioned:

```bash
# View history
cd /config
git log --oneline

# View changes
git diff HEAD~1

# Rollback if needed
git checkout <commit-hash>
ha core restart
```

### Status and Monitoring

```bash
# Check workflow status
ha-ai-workflow status

# View logs
tail -f /config/ai_exports/workflow.log

# Check HA logs
docker logs homeassistant -f
```

## 🔐 Security

### What Gets Sanitized

The export automatically replaces:

- 🔒 Passwords and tokens
- 🔒 API keys
- 🔒 Email addresses
- 🔒 IP addresses and MAC addresses
- 🔒 Geographic coordinates
- 🔒 Webhooks and URLs
- 🔒 Usernames and SSIDs

### Secrets Management

```
/config/ai_exports/secrets/
├── secrets_map_latest.json          # Current secrets
├── secrets_map_20260113_120000.json # Timestamped backup
└── secrets_map_20260112_150000.json # (keeps last 5)
```

**Never commit or share these files!**

### Safe Workflow

```bash
# 1. Export (sanitizes automatically)
ha-ai-workflow export

# 2. Share everything EXCEPT secrets/
tar -czf safe_to_share.tar.gz \
  --exclude='secrets' \
  /config/ai_exports/ha_export_*/

# 3. Work with AI using safe archive

# 4. Import (restores secrets automatically)
ha-ai-workflow import
```

## 🎨 Example AI Interactions

### Example 1: Smart Lighting Automation

**Prompt to AI:**
```
Based on my configuration (AI_CONTEXT.json attached), create an automation that:
- Turns on living room lights when motion detected after sunset
- Sets brightness based on time of night
- Turns off after 5 minutes of no motion
- Excludes when TV is on
```

**AI Response:**
```yaml
automation:
  - alias: "Smart Living Room Lighting"
    trigger:
      - platform: state
        entity_id: binary_sensor.living_room_motion
        to: 'on'
    condition:
      - condition: sun
        after: sunset
      - condition: state
        entity_id: media_player.living_room_tv
        state: 'off'
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room_main
        data:
          brightness_pct: >
            {% if now().hour < 22 %}
              100
            {% else %}
              30
            {% endif %}
      - wait_for_trigger:
          - platform: state
            entity_id: binary_sensor.living_room_motion
            to: 'off'
            for: "00:05:00"
      - service: light.turn_off
        target:
          entity_id: light.living_room_main
```

**Import Process:**
```bash
# 1. Save AI response as:
/config/ai_imports/pending/smart_lighting.yaml

# 2. Import
ha-ai-workflow import
# Enter branch name: feature/smart-lighting

# 3. System validates and deploys
✓ Configuration valid
✓ Merged to main
✓ Home Assistant restarted
```

### Example 2: Energy Dashboard

**Prompt to AI:**
```
I have 15 power monitoring sensors. Create a dashboard showing:
- Total home consumption
- Room-by-room breakdown
- Cost estimates ($0.15/kWh)
- Historical graphs
```

### Example 3: Debug Existing Automation

**Prompt to AI:**
```
My automation isn't triggering. Debug report attached.
[Share debug_report_*.md]
```

## 🛠️ Advanced Features

### Automated Mode (CI/CD)

```bash
# Fully automated workflow
ha-ai-workflow export --auto
ha-ai-workflow import --auto
```

**Use Cases:**
- Scheduled backups
- Testing workflows
- Bulk imports
- CI/CD pipelines

**Safety:**
- Still validates configuration
- Creates git branches
- Generates rollback points
- Logs all actions

### Debug Reports

When validation fails:

```bash
# Automatic debug report generated
/config/ai_exports/debug_report_20260113_120000.md

# Contains:
- Error details
- Configuration diff
- System state
- Rollback instructions
- AI-friendly problem description
```

**Share with AI to get help debugging!**

### Custom Workflows

```bash
# Export specific configuration
ha-ai-workflow export --name "pre-migration"

# Import to specific branch
ha-ai-workflow import --branch "test-automation"

# Skip validation (danger!)
ha-ai-workflow import --no-strict
```

## 📊 Statistics

After export, you'll see:

```
Export Statistics:
  Entities: 245 (238 active, 7 disabled)
  Devices: 45
  Integrations: 32
  Automations: 18
  Scripts: 12
  Add-ons: 8
  Secrets Replaced: 47
```

## 🐛 Troubleshooting

### Common Issues

**1. PyYAML Not Found**
```bash
python3 -m pip install pyyaml --break-system-packages
```

**2. Git Not Initialized**
```bash
ha-ai-workflow setup
```

**3. Validation Failed**
```bash
# Check the error
ha core check

# Review debug report
cat /config/ai_exports/debug_report_*.md
```

**4. Import Directory Empty**
```bash
# Files must be in correct location
ls -la /config/ai_imports/pending/
```

**5. Permission Denied**
```bash
# Run as root
sudo ha-ai-workflow export
```

### Getting Help

1. Check logs: `/config/ai_exports/workflow.log`
2. Run status: `ha-ai-workflow status`
3. Generate debug report
4. Share debug report with AI (exclude secrets!)

## 📁 Directory Structure

```
/config/
├── .git/                           # Git repository
├── .gitignore                      # Excludes secrets, logs, DBs
├── configuration.yaml              # Your HA config
├── automations.yaml
├── scripts.yaml
├── ai_exports/                     # Export location
│   ├── ha_export_TIMESTAMP/        # Each export
│   │   ├── config/                 # Sanitized configs
│   │   ├── diagnostics/            # System info
│   │   ├── addons/                 # Add-on configs
│   │   ├── AI_PROMPT.md           # AI-ready prompt
│   │   └── AI_CONTEXT.json        # Detailed context
│   ├── secrets/                    # ⚠️ KEEP SECURE
│   │   └── secrets_map_latest.json
│   ├── archives/                   # Auto-cleaned
│   └── workflow.log               # Activity log
├── ai_imports/                     # Import staging
│   └── pending/                    # Place AI files here
└── ...

/usr/local/ha-ai-workflow/         # Installation
├── bin/                            # Python scripts
├── docs/                           # Documentation
└── ha_ai_master.sh                # Master script
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

- Always review AI-generated code before deploying
- Test in a non-production environment first
- Keep backups of working configurations
- Never share your secrets files
- This tool is provided as-is without warranty

## 🙏 Acknowledgments

- Home Assistant community
- AI assistant providers (Anthropic Claude, OpenAI ChatGPT)
- All contributors and testers

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Balkonsen/HA_AI_Gen_Workflow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Balkonsen/HA_AI_Gen_Workflow/discussions)
- **Documentation**: [Wiki](https://github.com/Balkonsen/HA_AI_Gen_Workflow/wiki)

## 🗺️ Roadmap

- [x] Web UI for workflow management
- [x] Integration with HA add-on store
- [ ] Multi-instance support
- [ ] Cloud backup options
- [ ] Automated testing framework
- [ ] Pre-built automation templates
- [ ] Community automation library



*Star ⭐ this repo if you find it useful!*
