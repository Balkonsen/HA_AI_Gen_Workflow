# Codebase Structure

**Analysis Date:** 2026-08-29

## Directory Layout

```
HA_AI_Gen_Workflow/
├── bin/                              # Core Python modules (11 scripts)
│   ├── ha_ai_context_gen.py         # AI context generator from exports
│   ├── ha_config_import.py          # Import sanitized config back to HA
│   ├── ha_diagnostic_export.py      # Export HA configuration with sanitization
│   ├── ha_export_verifier.py        # Validate export structure and content
│   ├── secrets_manager.py           # Encryption/decryption, secret storage
│   ├── ssh_transfer.py              # Remote SSH operations for HA
│   ├── ssh_transfer_enhanced.py     # Extended SSH with password auth
│   ├── ssh_transfer_password.py     # Password-based SSH variant
│   ├── workflow_config.py           # Configuration manager (YAML)
│   ├── workflow_gui.py              # Streamlit GUI interface
│   └── workflow_orchestrator.py     # Main orchestrator (entry point)
│
├── config/                           # Configuration templates
│   └── workflow_config.yaml.template # Template for workflow configuration
│
├── docs/                             # Documentation (14 files)
│   ├── AGENT_INSTRUCTIONS.md        # AI agent development guide
│   ├── DEVELOPER_GUIDE.md           # Human developer guide
│   ├── TESTING_GUIDE.md             # Testing and validation
│   ├── SSH_DOCUMENTATION_INDEX.md   # SSH operation reference
│   ├── SSH_FINAL_REPORT.md          # SSH implementation report
│   ├── SSH_PASSWORD_SETUP.md        # SSH password authentication setup
│   ├── SSH_PASSWORD_VALIDATION.md   # SSH password validation
│   ├── SSH_QUICK_REFERENCE.md       # SSH quick reference
│   ├── SSH_VALIDATION_REPORT.md     # SSH validation results
│   ├── SSH_VALIDATION_SUMMARY.md    # SSH validation summary
│   ├── complete_readme.md           # Extended documentation
│   ├── deployment_guide.md          # Deployment instructions
│   ├── fix_summary_guide.md         # Bug fix guide
│   └── quick_reference.md           # Quick reference for users
│
├── templates/                        # Template files for documentation
│   ├── example_ai_prompts.md        # Example AI prompts for workflows
│   ├── github_issue_templates.md    # GitHub issue templates
│   └── video_demo_script.md         # Video demonstration script
│
├── tests/                            # Test suite (pytest)
│   ├── __init__.py                  # Package marker
│   ├── conftest.py                  # Pytest fixtures and setup
│   ├── test_bash_scripts.bats       # Bash script tests (BATS)
│   ├── test_config_import.py        # HAConfigImporter tests
│   ├── test_context_gen.py          # HAContextGenerator tests
│   ├── test_diagnostic_export.py    # HAConfigExporter tests
│   ├── test_export_verifier.py      # ExportVerifier tests
│   ├── test_ssh_transfer.py         # SSH operations tests
│   └── validate_shell_scripts.sh    # Shell validation script
│
├── tools/                            # Development and validation tools
│   ├── quick_validate.sh            # Quick validation script
│   ├── run_docker_tests.sh          # Docker test runner
│   ├── setup_pre_commit.sh          # Pre-commit hook setup
│   └── validate_all.sh              # Comprehensive validation suite
│
├── .github/                          # GitHub configuration
│   └── workflows/
│       └── ci-cd.yml                # GitHub Actions CI/CD pipeline
│
├── .vscode/                          # VS Code workspace configuration
│   ├── extensions.json              # Recommended VSCode extensions
│   ├── launch.json                  # Debug configurations
│   ├── settings.json                # Workspace editor settings
│   └── tasks.json                   # Predefined VS Code tasks
│
├── .planning/                        # GSD planning directory (created by tools)
│   └── codebase/                    # Codebase documentation
│       ├── ARCHITECTURE.md          # Architecture documentation
│       └── STRUCTURE.md             # This file
│
├── .gitignore                        # Git ignore rules
├── .markdown-link-check.json        # Markdown link checker configuration
├── .pre-commit-config.yaml          # Pre-commit hook configuration
├── CHANGELOG.md                      # Version history
├── Dockerfile.test                   # Docker image for testing
├── Makefile                          # Build automation (20+ commands)
├── README.md                         # Main project README
├── SETUP_COMPLETE.md               # Setup completion documentation
├── INFRASTRUCTURE_SUMMARY.md        # Infrastructure overview
├── PROJECT_STRUCTURE.md             # Project structure overview
├── QUICK_REFERENCE.md              # Quick reference guide
├── GETTING_STARTED.md              # Getting started guide
├── docker-compose.test.yml          # Docker compose for testing
├── ha_ai_master_script.sh           # Main orchestrator shell script
├── mit_license.txt                  # MIT License
├── pytest.ini                        # Pytest configuration
├── requirements.txt                 # Production dependencies
├── requirements-test.txt            # Testing dependencies
├── setup.sh                          # Installation script
└── venv/                            # Python virtual environment (excluded from git)
```

## Directory Purposes

**bin/ (Core Application):**
- Purpose: All executable Python modules for the workflow
- Contains: Export, import, sanitization, validation, configuration, SSH, GUI
- Key files: `workflow_orchestrator.py` (main entry point), `secrets_manager.py` (encryption)
- Imported by: All layers reference these modules

**config/ (Configuration Templates):**
- Purpose: Template configuration files for user setup
- Contains: `workflow_config.yaml.template` - starter configuration
- Key files: YAML template with all configuration options documented

**docs/ (Documentation):**
- Purpose: Comprehensive documentation for users and developers
- Contains: Setup guides, developer guides, SSH documentation, testing guides
- Key files: `DEVELOPER_GUIDE.md` (coding standards), `TESTING_GUIDE.md` (test patterns)

**templates/ (Markdown Templates):**
- Purpose: Reusable templates for documentation and communication
- Contains: AI prompts, GitHub issues, video scripts
- Key files: `example_ai_prompts.md` (suggested AI prompts for workflows)

**tests/ (Test Suite):**
- Purpose: Automated testing of all modules
- Contains: Unit tests (pytest), integration tests, validation scripts
- Key files: `conftest.py` (pytest fixtures), `test_*.py` (test modules)
- Patterns: Fixtures in conftest.py provide mock data; tests are isolated

**tools/ (Utility Scripts):**
- Purpose: Development and validation automation
- Contains: Validation scripts, Docker runners, pre-commit setup
- Key files: `validate_all.sh` (15+ validation checks), `setup_pre_commit.sh`

**.github/ (CI/CD Configuration):**
- Purpose: GitHub Actions workflows for automated testing and deployment
- Contains: CI/CD pipeline definition
- Key files: `workflows/ci-cd.yml` (runs tests on Python 3.8-3.11)

**.vscode/ (Editor Configuration):**
- Purpose: VS Code workspace configuration for consistent development environment
- Contains: Debug configs, task definitions, editor settings, extensions
- Key files: `tasks.json` (HA Workflow tasks), `launch.json` (debug configs)

## Key File Locations

**Entry Points:**
- `bin/workflow_orchestrator.py`: Python CLI entry point - parse args, orchestrate workflow
- `ha_ai_master_script.sh`: Shell script entry point - environment setup, logging, task orchestration
- `bin/workflow_gui.py`: Streamlit GUI entry point - interactive web interface
- `.vscode/tasks.json`: VS Code task definitions for integrated workflow execution

**Configuration:**
- `config/workflow_config.yaml.template`: Template for user configuration
- `.pre-commit-config.yaml`: Pre-commit hook definitions
- `pytest.ini`: Pytest configuration and test discovery
- `.vscode/settings.json`: Editor workspace settings

**Core Logic:**
- `bin/workflow_orchestrator.py`: WorkflowOrchestrator class (main orchestrator)
- `bin/ha_diagnostic_export.py`: HAConfigExporter class (export logic)
- `bin/ha_ai_context_gen.py`: HAContextGenerator class (AI context generation)
- `bin/ha_config_import.py`: HAConfigImporter class (import logic)
- `bin/ha_export_verifier.py`: ExportVerifier class (validation logic)
- `bin/secrets_manager.py`: SecretsManager and SecretsSanitizer classes (encryption/decryption)
- `bin/ssh_transfer.py`: HARemoteManager class (SSH operations)
- `bin/workflow_config.py`: WorkflowConfig class (configuration management)

**Testing:**
- `tests/conftest.py`: Pytest fixtures (mock_ha_config, mock_export_data, etc.)
- `tests/test_diagnostic_export.py`: Export functionality tests
- `tests/test_context_gen.py`: AI context generation tests
- `tests/test_export_verifier.py`: Validation tests
- `tests/test_config_import.py`: Import functionality tests
- `tests/test_ssh_transfer.py`: SSH operation tests

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `workflow_orchestrator.py`)
- Shell scripts: lowercase with underscores (e.g., `validate_all.sh`)
- Test files: `test_<component>.py` (e.g., `test_export_verifier.py`)
- Configuration: YAML files with `.yaml` or `.template` extension

**Directories:**
- Package directories: lowercase, descriptive names (bin/, tests/, docs/, config/)
- Feature directories: grouped by function (ssh/ would contain SSH-related code, but currently in single bin/)

**Classes:**
- UpperCamelCase (e.g., `WorkflowOrchestrator`, `HAConfigExporter`, `SecretsManager`)
- Prefix "HA" for Home Assistant-specific classes

**Functions/Methods:**
- snake_case (e.g., `export_local()`, `sanitize_export()`, `restore_secrets_in_file()`)

**Constants:**
- UPPER_SNAKE_CASE (e.g., `MAX_AI_FILE_SIZE`, `CRYPTO_AVAILABLE`)

**Environment/Configuration:**
- CamelCase for YAML keys (e.g., `ssh`, `export_dir`, `connection_timeout`)

## Where to Add New Code

**New Feature (e.g., new export type, new import validation):**
- Primary code: `bin/new_feature.py` (create new module if major feature)
  - Or extend existing class in appropriate bin/ module
- Tests: `tests/test_new_feature.py`
- Documentation: Update `docs/DEVELOPER_GUIDE.md`
- Example: Adding Webhook export would go in `bin/workflow_orchestrator.py` as new service class

**New Component/Module (e.g., new integration type):**
- Implementation: `bin/<component>_<type>.py` (follow naming pattern)
  - Example: `bin/ha_mqtt_export.py` for MQTT-based export
- Tests: `tests/test_<component>_<type>.py`
- Integration point: Add to WorkflowOrchestrator.run_full_workflow() or as optional service

**Utilities/Helpers:**
- Shared functions: Add to appropriate existing module or create `bin/common.py` if truly cross-cutting
- Example: Utility for YAML validation should be in `bin/workflow_config.py` or reusable module

**Configuration Schema Changes:**
- Update: `config/workflow_config.yaml.template`
- Update: `bin/workflow_config.py` DEFAULT_CONFIG dictionary
- Update: `docs/QUICK_REFERENCE.md`

**Tests:**
- Location: `tests/test_<subject>.py`
- Fixtures: Add to `tests/conftest.py`
- Patterns: 
  - Use mocks from conftest (mock_ha_config, mock_secrets)
  - Test both success and failure paths
  - Include integration tests with full workflow
  - Example: `tests/test_config_import.py` tests HAConfigImporter with mocked config

**Documentation:**
- User guides: `docs/*.md` (descriptive names)
- Developer guides: `docs/DEVELOPER_GUIDE.md` or `docs/TESTING_GUIDE.md`
- API docs: Inline docstrings in Python files (follow existing pattern)

## Special Directories

**venv/ (Virtual Environment):**
- Purpose: Isolated Python environment for dependencies
- Generated: Yes (created by `setup.sh`)
- Committed: No (listed in .gitignore)
- Contents: Site-packages with all installed dependencies

**exports/ (Generated Exports):**
- Purpose: Stored HA configuration exports
- Generated: Yes (created by workflow_orchestrator.export_local/remote)
- Committed: No (listed in .gitignore)
- Structure: `export_YYYYMMDD_HHMMSS/config/` (sanitized files)

**imports/ (User Modifications):**
- Purpose: Directory where users place modified configurations for import
- Generated: No (user-created)
- Committed: No (list in .gitignore)
- Contents: YAML files ready for import back to HA

**secrets/ (Encrypted Secrets):**
- Purpose: Encrypted storage of sensitive values
- Generated: Yes (created by SecretsManager)
- Committed: No (secrets/ folder in .gitignore)
- Files: `secrets_vault.enc` (encrypted), `secrets_mapping.json` (metadata)

**ai_context/ (Generated AI Context):**
- Purpose: AI-friendly documentation generated from exports
- Generated: Yes (created by HAContextGenerator)
- Committed: No (ai_context/ in .gitignore)
- Contents: `AI_CONTEXT.md`, `AI_PROMPT.md`, `SECRETS_INFO.json`

**.planning/codebase/ (Codebase Documentation):**
- Purpose: GSD codebase mapping documents
- Generated: Yes (created by /gsd-map-codebase)
- Committed: Yes (track architecture changes)
- Contents: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, etc.

---

*Structure analysis: 2026-08-29*
