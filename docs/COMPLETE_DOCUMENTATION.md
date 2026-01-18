# Home Assistant AI Workflow - Complete Documentation

> **Automated export, AI-powered development, and git-versioned import workflow for Home Assistant**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024+-blue.svg)](https://www.home-assistant.io/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [Usage Options](#4-usage-options)
5. [Export & Import Workflow](#5-export--import-workflow)
6. [Secrets Management](#6-secrets-management)
7. [SSH Connection Setup](#7-ssh-connection-setup)
8. [VS Code Integration](#8-vs-code-integration)
9. [GUI Interface (Streamlit)](#9-gui-interface-streamlit)
10. [Development & Testing](#10-development--testing)
11. [Troubleshooting](#11-troubleshooting)
12. [Security Best Practices](#12-security-best-practices)
13. [API Reference](#13-api-reference)

---

## 1. Overview

### What is HA AI Workflow?

A complete toolset for:

- **Exporting** Home Assistant configuration with automatic secrets sanitization
- **Generating AI-friendly context** for use with Claude, ChatGPT, Gemini
- **Importing** AI-modified configurations back to Home Assistant
- **Version control** with automatic git branching and merging

### Key Features

| Feature                       | Description                                              |
| ----------------------------- | -------------------------------------------------------- |
| 🔒 **Automated Sanitization** | Removes passwords, tokens, IPs, emails                   |
| 🔐 **Encrypted Secrets**      | AES-128 (Fernet) encryption for sensitive data           |
| 📍 **Labeled Placeholders**   | `<<HA_SECRET_PASSWORD_001>>` format for AI compatibility |
| 🤖 **AI-Ready Export**        | Optimized structure for Claude, ChatGPT, Gemini          |
| 📡 **SSH Remote Access**      | Export/import from remote HA installations               |
| 📦 **Complete Export**        | Entities, devices, configs, automations, scripts         |
| 🌳 **Git Versioning**         | Automatic branching and merging                          |
| 🖥️ **Multiple Interfaces**    | CLI, VS Code Tasks, GUI (Streamlit)                      |

### Export Structure

```
export_YYYYMMDD_HHMMSS/
├── ai_upload/                    # SAFE TO UPLOAD TO AI
│   ├── README.md                 # Upload instructions
│   ├── ha_context.md             # System overview & statistics
│   ├── ha_entities.json          # All entity IDs (compact)
│   └── ha_config.yaml            # Consolidated configuration
│
├── secrets/                      # NEVER SHARE!
│   ├── .gitignore
│   └── secrets_map.json          # Secret value mappings
│
├── README.md                     # Main documentation
└── METADATA.json                 # Export metadata
```

---

## 2. Installation

### Prerequisites

- Python 3.8 or higher
- Git installed (optional but recommended)
- SSH access (for remote HA)
- 500MB free disk space

---

### Option A: Windows 11 Automated Install (Recommended for Windows)

**Fully automated installer that handles everything:**

#### One-Click Installation

Simply **double-click `Install-Windows.bat`** in the project folder.

#### PowerShell Installation

```powershell
# Clone repository
git clone https://github.com/Balkonsen/HA_AI_Gen_Workflow.git
cd HA_AI_Gen_Workflow

# Run automated installer
.\install_windows.ps1
```

#### Installation Options

```powershell
# Install and launch GUI immediately
.\install_windows.ps1 -LaunchGUI

# Unattended mode (no prompts)
.\install_windows.ps1 -Unattended

# Full unattended with auto GUI launch
.\install_windows.ps1 -Unattended -LaunchGUI

# Skip dependency checks (if Python already installed)
.\install_windows.ps1 -SkipPythonCheck -SkipGitCheck

# Don't create desktop shortcuts
.\install_windows.ps1 -NoShortcuts
```

#### What the Windows Installer Does

| Step | Action                                                           |
| ---- | ---------------------------------------------------------------- |
| 1    | Checks Python 3.8+ (offers auto-install via winget if missing)   |
| 2    | Checks Git (optional, offers auto-install)                       |
| 3    | Creates Python virtual environment (`.venv`)                     |
| 4    | Installs all Python dependencies                                 |
| 5    | Creates directory structure (`exports/`, `imports/`, `secrets/`) |
| 6    | Generates configuration file                                     |
| 7    | Creates `Start-HA-AI-Workflow.bat` (GUI launcher)                |
| 8    | Creates `Start-HA-AI-CLI.bat` (CLI launcher)                     |
| 9    | Creates desktop shortcuts                                        |
| 10   | Verifies installation                                            |

#### After Windows Installation

- **Launch GUI**: Double-click desktop shortcut or `Start-HA-AI-Workflow.bat`
- **Use CLI**: Double-click `Start-HA-AI-CLI.bat`
- **Browser**: http://localhost:8501

📖 **Full Windows guide**: [docs/WINDOWS_INSTALLATION.md](WINDOWS_INSTALLATION.md)

---

### Option B: Quick Install (Linux/macOS)

```bash
# Clone repository
git clone https://github.com/Balkonsen/HA_AI_Gen_Workflow.git
cd HA_AI_Gen_Workflow

# Install dependencies
pip install -r requirements-test.txt

# Run setup wizard
python3 bin/workflow_orchestrator.py setup
```

### Option C: Direct Installation on HA Host

```bash
# SSH into Home Assistant
ssh root@192.168.1.100

# Clone to HA
cd /config
git clone https://github.com/Balkonsen/HA_AI_Gen_Workflow.git ha-ai-workflow

# Run setup
cd ha-ai-workflow
./setup.sh
```

### Option D: Docker Installation

```bash
# Build test image
docker build -f Dockerfile.test -t ha-ai-workflow .

# Run tests
docker-compose -f docker-compose.test.yml up
```

### Verify Installation

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Test the tool
python3 bin/workflow_orchestrator.py --help

# Run quick validation
make quick-validate
```

### Install Dependencies

```bash
# Core dependencies
pip install pyyaml paramiko cryptography

# For GUI
pip install streamlit

# For development
pip install -r requirements-test.txt
```

---

## 3. Configuration

### Configuration File

Copy the template and customize:

```bash
cp config/workflow_config.yaml.template config/workflow_config.yaml
```

### Full Configuration Reference

```yaml
# =============================================================================
# SSH Connection Settings
# =============================================================================
ssh:
  enabled: false # Enable for remote HA access
  host: "192.168.1.100" # HA server IP or hostname
  port: 22 # SSH port
  user: "root" # SSH username
  auth_method: "key" # "key" or "password"
  key_path: "~/.ssh/id_rsa" # SSH private key path
  remote_config_path: "/config" # HA config path on remote

# =============================================================================
# Local Path Configuration
# =============================================================================
paths:
  export_dir: "./exports" # Export output directory
  import_dir: "./imports" # Import source directory
  secrets_dir: "./secrets" # Encrypted secrets storage
  backup_dir: "./backups" # Backup directory
  ai_context_dir: "./ai_context" # AI context output

# =============================================================================
# Export Settings
# =============================================================================
export:
  include_patterns:
    - "*.yaml"
    - "*.yml"
    - "*.json"
    - "blueprints/**"
    - "custom_components/**"
    - ".storage/core.*"

  exclude_patterns:
    - "secrets.yaml"
    - "*.log"
    - "*.db"
    - "tts/**"
    - "deps/**"

  sensitive_fields:
    - "password"
    - "token"
    - "api_key"
    - "secret"
    - "latitude"
    - "longitude"

# =============================================================================
# Secrets Encryption
# =============================================================================
secrets:
  encryption_method: "fernet" # AES-128 encryption
  key_file: "./secrets/.encryption_key"
  label_prefix: "HA_SECRET" # Placeholder prefix
  auto_restore: true # Auto-restore on import

# =============================================================================
# AI Integration
# =============================================================================
ai:
  context:
    include_entities: true
    include_devices: true
    include_automations: true
    include_integrations: true
    max_size_kb: 500

# =============================================================================
# Validation
# =============================================================================
validation:
  check_yaml_syntax: true
  check_secrets_references: true
  check_entity_ids: true
  run_ha_check: false # Requires HA CLI
```

### Interactive Setup

```bash
python3 bin/workflow_orchestrator.py setup
```

This wizard will guide you through:

1. SSH connection configuration
2. Path setup
3. Secrets encryption
4. Validation options

---

## 4. Usage Options

### Option 1: Command Line Interface (CLI)

#### Available Commands

| Command    | Description                     |
| ---------- | ------------------------------- |
| `setup`    | Interactive configuration setup |
| `export`   | Export HA configuration         |
| `sanitize` | Sanitize secrets in export      |
| `context`  | Generate AI context             |
| `import`   | Import configuration to HA      |
| `validate` | Validate export/import          |
| `full`     | Run complete workflow           |

#### CLI Examples

```bash
# Setup configuration
python3 bin/workflow_orchestrator.py setup

# Export from local HA
python3 bin/workflow_orchestrator.py export --source /config

# Export from remote HA (SSH)
python3 bin/workflow_orchestrator.py export --remote

# Generate AI context from export
python3 bin/workflow_orchestrator.py context --source ./exports/export_latest

# Import with dry-run (preview only)
python3 bin/workflow_orchestrator.py import --source ./imports/ai_config --dry-run

# Import for real
python3 bin/workflow_orchestrator.py import --source ./imports/ai_config --target /config

# Full pipeline (export → sanitize → context)
python3 bin/workflow_orchestrator.py full --source /config

# Full pipeline with remote
python3 bin/workflow_orchestrator.py full --remote
```

#### CLI Options

```
--config, -c    Path to configuration file
--source, -s    Source path for export/import
--target, -t    Target path for import
--remote, -r    Use SSH for remote HA
--dry-run, -n   Preview changes without applying
```

### Option 2: VS Code Tasks

Run via `Terminal → Run Task` or `Ctrl+Shift+P → Tasks: Run Task`:

| Task                          | Description                |
| ----------------------------- | -------------------------- |
| 🏠 Setup Configuration        | Interactive setup wizard   |
| 📤 Export (Local)             | Export from local /config  |
| 📤 Export (SSH Remote)        | Export via SSH             |
| 🔐 Sanitize Export            | Remove secrets from export |
| 🤖 Generate AI Context        | Create AI-ready files      |
| 📥 Import (Local)             | Import to local HA         |
| 📥 Import (SSH Remote)        | Import via SSH             |
| 📥 Import (Dry Run)           | Preview import changes     |
| 🔍 Validate Export            | Validate exported files    |
| 🚀 Full Pipeline (Local)      | Complete local workflow    |
| 🚀 Full Pipeline (SSH Remote) | Complete remote workflow   |
| 🖥️ Start GUI                  | Launch Streamlit GUI       |

### Option 3: VS Code Debug Configurations

Press `F5` or use Run → Start Debugging:

| Configuration                 | Description              |
| ----------------------------- | ------------------------ |
| 🏠 HA Workflow: Setup         | Debug setup wizard       |
| 📤 HA Workflow: Export Local  | Debug local export       |
| 📤 HA Workflow: Export Remote | Debug remote export      |
| 🤖 Generate AI Context        | Debug context generation |
| 📥 HA Workflow: Import        | Debug import process     |
| 🚀 Full Pipeline              | Debug complete workflow  |
| 🧪 Pytest: Current File       | Debug current test file  |
| 🧪 Pytest: All Tests          | Debug all tests          |

### Option 4: Bash Script (HA Host)

On the Home Assistant host:

```bash
# Make executable
chmod +x ha_ai_master_script.sh

# Run export
./ha_ai_master_script.sh export

# Run import
./ha_ai_master_script.sh import

# Check status
./ha_ai_master_script.sh status

# Auto mode (no confirmations)
./ha_ai_master_script.sh export --auto
```

### Option 5: GUI (Streamlit)

```bash
# Start GUI
streamlit run bin/workflow_gui.py --server.port 8501

# Or via VS Code task
Terminal → Run Task → 🖥️ HA Workflow: Start GUI
```

Open http://localhost:8501 in your browser.

GUI Features:

- Step-by-step workflow wizard
- SSH configuration interface
- Export/Import with progress
- AI context preview
- Secrets management

---

## 5. Export & Import Workflow

### Complete Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Export    │ ──▶ │  AI Upload  │ ──▶ │   Import    │
│  from HA    │     │  to Claude  │     │   to HA     │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │
      ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Sanitized   │     │ AI modifies │     │ Secrets     │
│ Config      │     │ config      │     │ Restored    │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Step 1: Export

```bash
# Export from local HA
python3 bin/workflow_orchestrator.py export --source /config

# Export from remote HA
python3 bin/workflow_orchestrator.py export --remote
```

**Output:**

```
exports/
└── export_20260118_143022/
    ├── ai_upload/
    │   ├── ha_context.md
    │   ├── ha_entities.json
    │   └── ha_config.yaml
    └── secrets/
        └── secrets_map.json
```

### Step 2: Upload to AI

Upload files from `ai_upload/` folder to your AI assistant:

| AI Service | Max File Size          | Supported Types   |
| ---------- | ---------------------- | ----------------- |
| Claude     | 30MB/file, 100MB total | .md, .json, .yaml |
| ChatGPT    | 512MB/file             | .md, .json, .yaml |
| Gemini     | 2GB/file               | .md, .json, .yaml |

**Example AI Prompts:**

```
"Based on my ha_entities.json, create an automation that turns off all
lights when no motion is detected for 10 minutes."

"Review my automations in ha_config.yaml and suggest optimizations."

"Create a dashboard for my living room using the entities I have."
```

### Step 3: Import AI Response

Save AI-generated YAML to import directory:

```bash
# Create import directory
mkdir -p imports/ai_config

# Save AI response as YAML file
# imports/ai_config/new_automation.yaml

# Preview changes (dry-run)
python3 bin/workflow_orchestrator.py import \
  --source ./imports/ai_config \
  --target /config \
  --dry-run

# Apply changes
python3 bin/workflow_orchestrator.py import \
  --source ./imports/ai_config \
  --target /config
```

### Full Pipeline (One Command)

```bash
# Local HA
python3 bin/workflow_orchestrator.py full --source /config

# Remote HA
python3 bin/workflow_orchestrator.py full --remote
```

---

## 6. Secrets Management

### How Secrets Are Handled

1. **Detection**: Sensitive patterns are identified in config files
2. **Replacement**: Values replaced with labeled placeholders
3. **Encryption**: Actual values stored encrypted separately
4. **Restoration**: Placeholders restored on import

### Sensitive Data Patterns

| Type        | Pattern Example           | Placeholder                  |
| ----------- | ------------------------- | ---------------------------- |
| Password    | `password: secret123`     | `<<HA_SECRET_PASSWORD_001>>` |
| Token       | `token: abc123xyz`        | `<<HA_SECRET_TOKEN_001>>`    |
| API Key     | `api_key: key123`         | `<<HA_SECRET_API_KEY_001>>`  |
| IP Address  | `host: 192.168.1.100`     | `<<HA_SECRET_IP_001>>`       |
| Email       | `email: user@example.com` | `<<HA_SECRET_EMAIL_001>>`    |
| Coordinates | `latitude: 52.5200`       | `<<HA_SECRET_LATITUDE_001>>` |
| MAC Address | `mac: AA:BB:CC:DD:EE:FF`  | `<<HA_SECRET_MAC_001>>`      |

### Example Transformation

**Original:**

```yaml
mqtt:
  broker: 192.168.1.50
  username: mqttuser
  password: supersecret123
```

**Exported (sanitized):**

```yaml
mqtt:
  broker: <<HA_SECRET_IP_001>>
  username: <<HA_SECRET_USERNAME_001>>
  password: <<HA_SECRET_PASSWORD_001>>
```

**Secrets Map (encrypted):**

```json
{
  "HA_SECRET_IP_001": "192.168.1.50",
  "HA_SECRET_USERNAME_001": "mqttuser",
  "HA_SECRET_PASSWORD_001": "supersecret123"
}
```

### Manual Secrets Operations

```bash
# View secrets summary (no values shown)
python3 bin/secrets_manager.py list

# Export secrets for AI (metadata only)
python3 bin/secrets_manager.py export-ai --output ./ai_context/secrets_info.json

# Restore secrets in a file
python3 bin/secrets_manager.py restore --file ./imports/config.yaml
```

---

## 7. SSH Connection Setup

### Option A: SSH Key Authentication (Recommended)

```bash
# Generate SSH key (if needed)
ssh-keygen -t ed25519 -C "ha-ai-workflow"

# Copy key to HA server
ssh-copy-id root@192.168.1.100

# Test connection
ssh root@192.168.1.100 "echo Connected!"
```

**Configuration:**

```yaml
ssh:
  enabled: true
  host: "192.168.1.100"
  port: 22
  user: "root"
  auth_method: "key"
  key_path: "~/.ssh/id_ed25519"
```

### Option B: Password Authentication (Interactive)

**Configuration:**

```yaml
ssh:
  enabled: true
  host: "192.168.1.100"
  port: 22
  user: "root"
  auth_method: "interactive" # Prompts for password
```

**Usage:**

```bash
# Will prompt for password
python3 bin/workflow_orchestrator.py export --remote
```

### Option C: Password via Environment Variable

```bash
# Set password in environment
export SSH_PASSWORD="your_password"

# Run workflow
python3 bin/workflow_orchestrator.py export --remote
```

**Configuration:**

```yaml
ssh:
  enabled: true
  host: "192.168.1.100"
  auth_method: "paramiko"
  password: "${SSH_PASSWORD}" # From environment
```

### Option D: sshpass Utility

```bash
# Install sshpass
sudo apt install sshpass  # Debian/Ubuntu
brew install hudochenkov/sshpass/sshpass  # macOS

# Set password
export SSH_PASSWORD="your_password"
```

**Configuration:**

```yaml
ssh:
  enabled: true
  auth_method: "sshpass"
  password: "${SSH_PASSWORD}"
```

### Test SSH Connection

```bash
# Test with ssh_transfer_password.py
python3 bin/ssh_transfer_password.py \
  --host 192.168.1.100 \
  --user root \
  --method interactive \
  --test
```

### Docker Container Access

If HA runs in Docker:

```yaml
ssh:
  enabled: true
  host: "192.168.1.100"
  user: "root"

  docker:
    enabled: true
    container_name: "homeassistant"
```

---

## 8. VS Code Integration

### Recommended Extensions

Install these VS Code extensions for the best experience:

| Extension      | ID                                     | Purpose           |
| -------------- | -------------------------------------- | ----------------- |
| Python         | `ms-python.python`                     | Python support    |
| YAML           | `redhat.vscode-yaml`                   | YAML validation   |
| Home Assistant | `keesschollaart.vscode-home-assistant` | HA syntax         |
| GitLens        | `eamodio.gitlens`                      | Git visualization |
| Bash Debug     | `rogalmic.bash-debug`                  | Shell debugging   |

### Workspace Settings

The project includes `.vscode/settings.json` with:

- Python formatting (Black)
- YAML schema validation
- File associations
- Test configuration

### Tasks (tasks.json)

Run via `Ctrl+Shift+P` → `Tasks: Run Task`:

**Workflow Tasks:**

- 🏠 Setup Configuration
- 📤 Export (Local/Remote)
- 🔐 Sanitize Export
- 🤖 Generate AI Context
- 📥 Import (Local/Remote/Dry Run)
- 🚀 Full Pipeline

**Development Tasks:**

- 🧪 Run All Tests
- Run Current Test File
- Format Code (Black)
- Lint Python (Flake8)
- Security Scan (Bandit)

**Docker Tasks:**

- Docker: Build Test Image
- Docker: Run Tests

### Debug Configurations (launch.json)

Press `F5` to debug:

| Configuration           | Use Case              |
| ----------------------- | --------------------- |
| Python: Current File    | Debug any Python file |
| 🧪 Pytest: Current File | Debug current test    |
| 🧪 Pytest: All Tests    | Debug all tests       |
| 🔧 Debug SSH Transfer   | Debug SSH connection  |
| Bash: Current Script    | Debug shell scripts   |

### Keybindings

| Shortcut                 | Action          |
| ------------------------ | --------------- |
| `F5`                     | Start debugging |
| `Ctrl+Shift+B`           | Run build task  |
| `Ctrl+Shift+T`           | Run test task   |
| `Ctrl+Shift+P` → "Tasks" | Run any task    |

---

## 9. GUI Interface (Streamlit)

### Starting the GUI

```bash
# Direct start
streamlit run bin/workflow_gui.py --server.port 8501

# Via VS Code task
Terminal → Run Task → 🖥️ HA Workflow: Start GUI

# Via make
make gui
```

Access at: http://localhost:8501

### GUI Features

1. **Configuration Page**
   - SSH settings
   - Path configuration
   - Save/load config

2. **Export Page**
   - Local or remote export
   - Progress indicator
   - View exported files

3. **Sanitize Page**
   - Preview secrets found
   - One-click sanitization
   - Review placeholders

4. **AI Context Page**
   - Generate context files
   - Preview ha_context.md
   - Download for AI upload

5. **Import Page**
   - Select import source
   - Dry-run preview
   - Apply changes

---

## 10. Development & Testing

### Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements-test.txt

# Setup pre-commit hooks
make pre-commit
```

### Test Suite

```bash
# Run all tests
make test
# or
pytest -v

# Run specific test file
pytest tests/test_context_gen.py -v

# Run with coverage
make coverage
# or
pytest --cov=bin --cov-report=html

# Run specific test category
pytest -v -m unit
pytest -v -m integration
pytest -v -m security
```

### Test Files

| File                        | Coverage              |
| --------------------------- | --------------------- |
| `test_context_gen.py`       | AI context generation |
| `test_diagnostic_export.py` | Export functionality  |
| `test_config_import.py`     | Import functionality  |
| `test_export_verifier.py`   | Validation logic      |
| `test_bash_scripts.bats`    | Bash script tests     |

### Validation Tools

```bash
# Quick validation (fast, during development)
make quick-validate
# or
./tools/quick_validate.sh

# Full validation (comprehensive, before commit)
make validate
# or
./tools/validate_all.sh
```

**Quick Validation Checks:**

- Python syntax
- Shell syntax
- Quick test run

**Full Validation Checks:**

1. Environment setup
2. Code formatting (Black)
3. Code linting (Flake8)
4. Type checking (MyPy)
5. Shell script validation (ShellCheck)
6. Unit tests
7. Code coverage (>50%)
8. Security scanning (Bandit)
9. YAML/JSON validation
10. Documentation check
11. Git status
12. Large files check
13. Secrets detection

### Pre-commit Hooks

```bash
# Install hooks
make pre-commit

# Run manually
pre-commit run --all-files
```

Hooks include:

- Trailing whitespace removal
- YAML/JSON validation
- Black formatting
- Flake8 linting
- Bandit security scan
- ShellCheck
- Pytest execution

### Docker Testing

```bash
# Build test image
make docker-build
# or
docker build -f Dockerfile.test -t ha-ai-workflow-test .

# Run tests in Docker
make docker-test
# or
./tools/run_docker_tests.sh
```

### Makefile Targets

| Target                | Description             |
| --------------------- | ----------------------- |
| `make install`        | Install dependencies    |
| `make test`           | Run all tests           |
| `make coverage`       | Run tests with coverage |
| `make lint`           | Run linters             |
| `make format`         | Format code with Black  |
| `make security`       | Run security scan       |
| `make validate`       | Full validation         |
| `make quick-validate` | Quick validation        |
| `make pre-commit`     | Setup pre-commit hooks  |
| `make docker-build`   | Build Docker test image |
| `make docker-test`    | Run Docker tests        |
| `make clean`          | Clean generated files   |
| `make gui`            | Start Streamlit GUI     |

---

## 11. Troubleshooting

### Common Issues

#### "PyYAML Not Found"

```bash
pip install pyyaml
# On HA OS:
pip install pyyaml --break-system-packages
```

#### "Permission Denied"

```bash
# Run with sudo on HA host
sudo python3 bin/workflow_orchestrator.py export --source /config

# Or fix permissions
chmod +x bin/*.py
```

#### "SSH Connection Failed"

```bash
# Test SSH manually
ssh -v root@192.168.1.100

# Check SSH config
cat config/workflow_config.yaml | grep -A10 ssh:

# Test with script
python3 bin/ssh_transfer_password.py --host 192.168.1.100 --test
```

#### "No Files to Import"

```bash
# Check import directory
ls -la imports/

# Files must be in the correct location
mv ai_config.yaml imports/pending/
```

#### "Secrets File Not Found"

```bash
# Run export first to generate secrets
python3 bin/workflow_orchestrator.py export --source /config

# Check secrets location
ls -la secrets/
```

#### "Configuration Check Fails"

```bash
# Review errors
ha core check

# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('configuration.yaml'))"
```

#### "Git Conflicts"

```bash
cd /config
git status
git stash
git pull
git stash pop
```

### Debug Mode

```bash
# Enable verbose output
export DEBUG=1
python3 bin/workflow_orchestrator.py export --source /config

# Check logs
cat exports/workflow.log
```

### Getting Help

1. Check logs: `./exports/workflow.log`
2. Run validation: `make validate`
3. Generate debug report: `./tools/generate_debug_report.sh`
4. Open GitHub issue with debug report (exclude secrets!)

---

## 12. Security Best Practices

### DO ✅

- Use SSH keys instead of passwords
- Keep `secrets/` folder secure
- Use environment variables for passwords
- Review AI-generated code before import
- Use dry-run before actual import
- Keep backups before changes
- Use git for version control

### DON'T ❌

- Never upload `secrets/` folder to AI
- Never commit `secrets_map.json` to git
- Never share SSH passwords in config files
- Never run untested imports on production
- Never disable validation checks

### File Security

```bash
# Secure secrets directory
chmod 700 secrets/
chmod 600 secrets/*

# Add to .gitignore (already included)
echo "secrets/" >> .gitignore
echo "*.encryption_key" >> .gitignore
```

### Network Security

```yaml
ssh:
  # Use SSH keys
  auth_method: "key"

  # Use specific port
  port: 22222

  # Limit to local network
  host: "192.168.1.100" # Not public IP
```

---

## 13. API Reference

### Core Modules

#### workflow_orchestrator.py

Main entry point for all operations.

```python
from workflow_orchestrator import WorkflowOrchestrator

# Initialize
orchestrator = WorkflowOrchestrator(config_path="config/workflow_config.yaml")

# Export from local
export_path = orchestrator.export_local("/config")

# Export from remote
export_path = orchestrator.export_from_remote()

# Sanitize export
orchestrator.sanitize_export(export_path)

# Generate AI context
context_path = orchestrator.generate_ai_context(export_path)

# Import configuration
orchestrator.import_to_local(source_path, target_path, dry_run=False)

# Import to remote
orchestrator.import_to_remote(source_path, dry_run=False)

# Validate
orchestrator.validate_export(export_path)
```

#### ha_diagnostic_export.py

Handles configuration export with sanitization.

```python
from ha_diagnostic_export import HAConfigExporter

# Initialize
exporter = HAConfigExporter(output_dir="/tmp/exports")

# Run full export
tarball_path = exporter.run()

# Individual operations
exporter.create_export_structure()
exporter.export_config_directory()
exporter.export_entities_registry()
exporter.export_entity_states()
exporter.export_device_registry()
exporter.generate_ai_context_file()
exporter.generate_ai_entities_file()
exporter.generate_ai_config_file()
exporter.save_secrets_map()
```

#### secrets_manager.py

Manages secret detection and encryption.

```python
from secrets_manager import SecretsManager, SecretsSanitizer

# Initialize
manager = SecretsManager(secrets_dir="./secrets")

# Sanitize file
sanitizer = SecretsSanitizer(manager)
sanitizer.sanitize_file("config.yaml", "config_sanitized.yaml")

# Restore secrets
sanitizer.restore_file("config_sanitized.yaml", "config_restored.yaml")

# Get secret info (no values)
info = manager.get_secrets_info()
```

#### ssh_transfer.py

Handles SSH connections and file transfers.

```python
from ssh_transfer import SSHTransfer, HARemoteManager

# Initialize
ssh = SSHTransfer(
    host="192.168.1.100",
    user="root",
    auth_method="key",
    key_path="~/.ssh/id_rsa"
)

# Test connection
if ssh.test_connection():
    print("Connected!")

# Transfer files
ssh.download("/config/configuration.yaml", "./local_config.yaml")
ssh.upload("./new_config.yaml", "/config/new_config.yaml")

# Execute command
stdout, stderr = ssh.execute("ha core check")

# Remote manager
manager = HARemoteManager(ssh_config)
manager.export_config("./exports", exclude_patterns)
manager.import_config("./imports", "/config", dry_run=False)
```

#### workflow_config.py

Configuration management.

```python
from workflow_config import WorkflowConfig, interactive_setup

# Load config
config = WorkflowConfig("config/workflow_config.yaml")

# Get values
ssh_host = config.get("ssh.host")
export_dir = config.get("paths.export_dir")

# Set values
config.set("ssh.enabled", True)

# Save config
config.save()

# Interactive setup
interactive_setup()
```

### CLI Reference

```
python3 bin/workflow_orchestrator.py <command> [options]

Commands:
  setup         Interactive configuration setup
  export        Export HA configuration
  sanitize      Sanitize secrets in export
  context       Generate AI context
  import        Import configuration to HA
  validate      Validate export/import
  full          Run complete workflow

Options:
  --config, -c    Path to configuration file
  --source, -s    Source path for export/import
  --target, -t    Target path for import
  --remote, -r    Use SSH for remote HA
  --dry-run, -n   Preview changes without applying
```

---

## Quick Reference Card

### Export Commands

```bash
# Local export
python3 bin/workflow_orchestrator.py export --source /config

# Remote export
python3 bin/workflow_orchestrator.py export --remote

# Full pipeline
python3 bin/workflow_orchestrator.py full --source /config
```

### Import Commands

```bash
# Dry-run (preview)
python3 bin/workflow_orchestrator.py import --source ./imports --dry-run

# Actual import
python3 bin/workflow_orchestrator.py import --source ./imports --target /config
```

### AI Upload Files

```
ai_upload/
├── ha_context.md      ← System overview
├── ha_entities.json   ← All entity IDs
└── ha_config.yaml     ← Automations & config
```

### Security Reminder

```
✅ SAFE TO UPLOAD: ai_upload/ folder
❌ NEVER UPLOAD: secrets/ folder
```

---

_Documentation generated for HA AI Gen Workflow v2.0_
_Last updated: January 2026_
