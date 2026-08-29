# External Integrations

**Analysis Date:** 2026-08-29

## APIs & External Services

**Home Assistant:**
- SSH/SFTP connection to Home Assistant instances for remote configuration export/import
  - SDK/Client: Paramiko 3.0.0+
  - Auth: SSH key-based or password-based authentication
  - Configuration: `bin/ssh_transfer.py`, `bin/ssh_transfer_enhanced.py`

**AI Assistants (Target Integration):**
- The system is designed to generate AI-ready context files for interaction with AI assistants (Claude, ChatGPT, etc.)
- No direct API calls to AI services - generates context for manual AI interaction
- Planned for future: Direct API integration to AI services
- Context includes: Integrations, entities, devices, automations, scripts, add-ons analysis
- Location: `bin/ha_ai_context_gen.py`

## Data Storage

**File-Based Storage:**
- Local filesystem only for exports/imports/backups
- Directory structure:
  - Exports: `./exports/export_YYYYMMDD_HHMMSS/` (configured in `workflow_config.yaml`)
  - Imports: `./imports/` (user-provided AI-modified configs)
  - Backups: `./backups/` (rollback capability)
  - AI Context: `./ai_context/` (generated analysis files)
  - Secrets: `./secrets/` (encrypted storage)

**Databases:**
- None - project does not use persistent database storage
- Home Assistant YAML configuration files are parsed and analyzed
- Storage is file-based (YAML, JSON, encrypted binary)

**File Storage:**
- Local filesystem only
- Encrypted secrets vault: `secrets/secrets_vault.enc` (Fernet encryption)
- Secret mapping metadata: `secrets/secrets_mapping.json` (plaintext labels and metadata)
- Encryption key: `secrets/.encryption_key` (file permissions: 0o600)

**Caching:**
- None configured

## Authentication & Identity

**SSH Authentication:**
- Type: Key-based (primary) or password-based (fallback)
- Configuration location: `workflow_config.yaml` (ssh section)
- Default key path: `~/.ssh/id_rsa`
- Implemented in: `bin/ssh_transfer.py`, `bin/ssh_transfer_enhanced.py`
- Features:
  - `StrictHostKeyChecking=accept-new` policy
  - Batch mode for non-interactive operation
  - Connection timeout: 30 seconds (configurable)
  - Transfer timeout: 600 seconds = 10 minutes (configurable)
  - Retry logic: 3 attempts with 2-second delay

**Secrets Management:**
- Encryption method: Fernet (symmetric AES-128)
- Fallback: Base64 encoding (if cryptography not installed)
- Key generation: Automatic on first run
- Key storage: `./secrets/.encryption_key`
- Sensitive fields tracked:
  - password, token, api_key, secret, latitude, longitude, email, phone
- Labeled placeholders: `<<HA_SECRET_TYPE_NNN>>` format
- Implementation: `bin/secrets_manager.py`

**No API Keys Required:**
- Project does not require external API keys for core functionality
- SSH credentials are environment-specific (not in codebase)
- Secrets are user-provided and encrypted locally

## Monitoring & Observability

**Error Tracking:**
- None configured

**Logs:**
- Console-based logging during execution
- Log files can be excluded from exports (configured in `export.exclude_patterns`)
- Structured output with emoji status indicators (✓, ✗, ⚠, ℹ)
- Python logging module for internal logging (`bin/ssh_transfer.py`)

**No External Monitoring:**
- Project includes no telemetry or external monitoring integration
- All data remains on local system or remote Home Assistant server

## CI/CD & Deployment

**Hosting:**
- Self-hosted on user's machine or server
- Home Assistant instance (remote or local)
- Docker support for testing

**CI Pipeline:**
- GitHub Actions (`.github/workflows/ci-cd.yml`)
- Runs on: Ubuntu-latest
- Triggers: Push to main/develop/feature/* branches, PRs, manual dispatch

**CI/CD Jobs:**
1. Linting: Black, Flake8, Pylint, Bandit
2. Shell Script Validation: ShellCheck
3. Python Unit Tests: pytest matrix (3.8, 3.9, 3.10, 3.11)
4. Integration Tests: pytest with integration marker
5. Security Scanning: Trivy vulnerability scanner with SARIF upload
6. Documentation Check: Markdown link validation
7. Build & Package: Creates distribution tarball
8. Pre-Merge Validation: Aggregates all quality checks
9. Release: Auto-tags on merge to main

**External CI/CD Services:**
- Codecov: Code coverage reporting (integration via GitHub Actions)
- GitHub Security (SARIF upload): CodeQL and Trivy results
- Trivy: Aqua Security vulnerability scanner

## Environment Configuration

**Required Configuration:**
```yaml
ssh:
  enabled: true/false
  host: "IP or hostname"
  port: 22
  user: "root"
  auth_method: "key" or "password"
  key_path: "~/.ssh/id_rsa"
  connection_timeout: 30
  transfer_timeout: 600
```

**Optional Configuration:**
- All settings in `workflow_config.yaml` with defaults provided
- VS Code integration: notifications, auto-open files, integrated terminal

**No Environment Variables Required:**
- Project does not require pre-set environment variables
- Docker/CI/CD sets PYTHONPATH, PYTHONDONTWRITEBYTECODE, PYTHONUNBUFFERED internally

## Webhooks & Callbacks

**Incoming Webhooks:**
- None configured

**Outgoing Webhooks:**
- None configured

**Git Integration:**
- Git versioning support (automatic branching/merging mentioned in README)
- Pre-commit hooks configured in `.pre-commit-config.yaml`:
  - pytest execution before commit
  - Shell script validation
  - YAML/JSON/Markdown linting
  - Black formatting check
  - Security scanning (Bandit)

## Home Assistant Integration Details

**Export Process** (`bin/ha_diagnostic_export.py`):
- Copies configuration files from Home Assistant via SSH/local access
- Parses YAML with custom Home Assistant tags:
  - `!include`, `!include_dir_list`, `!include_dir_named`, `!include_dir_merge_list`, `!include_dir_merge_named`
  - `!secret`, `!input`, `!env_var`
- Extracts metadata:
  - System overview (unit system, timezone, external URL)
  - Integration list (configured platforms)
  - Entity analysis
  - Device information
  - Automation definitions
  - Script definitions
  - Add-on status
  - YAML blueprint analysis
  - Custom component detection

**Import Process** (`bin/ha_config_import.py`):
- Validates modified configurations
- Restores encrypted secrets automatically
- Performs syntax checking
- Handles entity ID validation
- Creates backups before import
- Supports rollback to previous versions

**Context Generation** (`bin/ha_ai_context_gen.py`):
- Analyzes Home Assistant configuration structure
- Generates AI-optimized markdown context
- Includes integration details, entity relationships, automation logic
- File: `templates/example_ai_prompts.md` (example AI prompts)

## Workflow Orchestration

**Main Entry Point:** `bin/workflow_orchestrator.py`

**Workflow Steps:**
1. Export: Export HA config from local or remote
2. Context Generation: Generate AI-ready analysis
3. AI Modification: (Manual) User feeds context to AI assistant
4. Import: Import modified config back to HA
5. Validation: Automated checks before deployment
6. Optional: Git versioning and rollback capability

**Supported Modes:**
- Local: Direct filesystem access to HA config
- Remote: SSH/SFTP access to remote HA instance
- Manual: Step-by-step CLI execution
- GUI: Streamlit web interface
- VS Code: Integrated IDE tasks

---

*Integration audit: 2026-08-29*
