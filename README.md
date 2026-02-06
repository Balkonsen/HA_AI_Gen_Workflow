# Home Assistant AI Workflow

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1+-blue.svg)](https://www.home-assistant.io/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

> **Export, sanitize, and AI-enhance your Home Assistant configuration safely**

Transform your Home Assistant configuration management with AI assistance while keeping your sensitive data secure. Export your setup, let AI help create automations and dashboards, then import the changes back—all without exposing passwords, tokens, or personal data.

## ✨ Key Features

- 🔐 **Automatic Secret Sanitization** — Passwords, tokens, API keys, and sensitive data are automatically replaced with labeled placeholders
- 🤖 **AI-Ready Export** — Generate context files optimized for AI assistants (Claude, ChatGPT, Gemini)
- 📥 **Safe Import** — Automatically restore secrets when importing AI-modified configurations
- ✅ **Validation** — Check configurations before deployment
- 🖥️ **Web GUI** — Full graphical interface via Home Assistant sidebar
- 📡 **SSH Support** — Connect to remote Home Assistant instances

## 💻 System Requirements

### Home Assistant Add-on (Recommended)
- **Home Assistant**: 2026.2.0 or later
- **Hardware**: 64-bit system
  - ✅ Intel/AMD x64 computers
  - ✅ **Raspberry Pi 4 or newer** (with 64-bit OS)
  - ✅ Raspberry Pi 3 (with 64-bit OS)
  - ✅ Home Assistant Green/Yellow
  - ❌ Raspberry Pi 4 with 32-bit OS (not supported)

**Note**: Raspberry Pi 4+ is fully supported when running 64-bit Home Assistant OS. If you're on 32-bit, you'll need to migrate to 64-bit OS first (see [add-on documentation](ha_ai_workflow_addon/DOCS.md#migration-from-32-bit-systems)).

### Manual Installation
- **Python**: 3.8 or later
- **Home Assistant**: Any version with REST API access

## 🏠 Installation (Home Assistant Add-on)

### Quick Install

1. **Add Repository**
   - Go to **Settings** → **Add-ons** → **Add-on Store**
   - Click **⋮** (top right) → **Repositories**
   - Add: `https://github.com/Balkonsen/HA_AI_Gen_Workflow`
   - Click **Add** → **Close**

2. **Install Add-on**
   - Find **"HA AI Gen Workflow"** in the store
   - Click **Install**

3. **Start & Access**
   - Click **Start** on the add-on page
   - Enable **"Show in sidebar"**
   - Click **Open Web UI**

## 🚀 Usage

### Export Your Configuration

1. Open the add-on from the sidebar
2. Go to **Export** tab
3. Click **Start Export**
4. Your configuration is exported with all secrets sanitized

### Work with AI

Share the generated files with your AI assistant:
- `AI_PROMPT.md` — Ready-to-use prompt with your setup overview
- `AI_CONTEXT.json` — Detailed entity and device information

**Ask AI to help you:**
- Create automations based on your devices
- Design dashboards using your entities
- Write scripts and template sensors
- Debug configuration issues
- Optimize existing setups

### Import AI Changes

1. Save AI-generated YAML files to the import directory
2. Go to **Import** tab
3. Enable **Dry run** to preview changes
4. Click **Start Import**
5. Secrets are automatically restored

## 🔐 How Secrets Work

During export, sensitive data is automatically detected and replaced:

```yaml
# Original configuration
api_key: sk-abc123secretkey

# Exported (safe to share)
api_key: <<HA_SECRET_API_KEY_001>>
```

Your actual secrets are encrypted and stored locally. When you import configurations, placeholders are automatically restored to real values.

**What gets sanitized:**
- Passwords and tokens
- API keys
- IP addresses and MAC addresses
- Email addresses
- Geographic coordinates
- Webhook URLs

## 📁 Directory Structure

```
/config/
├── ai_exports/              # Exported configurations
│   ├── ha_export_*/         # Each export (timestamped)
│   │   ├── config/          # Sanitized YAML files
│   │   ├── AI_PROMPT.md     # AI-ready prompt
│   │   └── AI_CONTEXT.json  # Detailed context
│   └── secrets/             # Encrypted secrets (never share!)
└── ai_imports/              # Place AI-modified files here
    └── pending/             # Files waiting to be imported
```

## 🛠️ Alternative Installation (Manual)

For advanced users who prefer command-line usage:

```bash
# Clone repository
git clone https://github.com/Balkonsen/HA_AI_Gen_Workflow.git
cd HA_AI_Gen_Workflow

# Install dependencies
pip install -r requirements.txt

# Run GUI
streamlit run bin/workflow_gui.py

# Or use CLI
python3 bin/workflow_orchestrator.py export --source /config
```

## 📡 SSH Remote Access

Connect to remote Home Assistant instances by configuring SSH in the add-on settings:

| Setting | Description |
|---------|-------------|
| `ssh_host` | IP address or hostname |
| `ssh_user` | Username (usually `root`) |
| `ssh_port` | Port number (default: 22) |
| `ssh_key_path` | Path to SSH private key |

## ⚠️ Important Notes

- **Always review AI-generated code** before deploying to production
- **Never share the `secrets/` directory** — it contains your actual credentials
- **Test changes** on a non-production system first
- **Keep backups** of working configurations

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

## 📜 License

MIT License — see [LICENSE](mit_license.txt) for details.

## 🔗 Links

- **Issues**: [GitHub Issues](https://github.com/Balkonsen/HA_AI_Gen_Workflow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Balkonsen/HA_AI_Gen_Workflow/discussions)

---

*Made for the Home Assistant community* ⭐
