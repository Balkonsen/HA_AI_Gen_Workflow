# Technology Stack

**Analysis Date:** 2026-08-29

## Languages

**Primary:**
- Python 3.8+ - Core application logic, CLI tools, and workflow orchestration
- Bash/Shell - Infrastructure scripts for setup, deployment, and automation
- YAML - Configuration files and Home Assistant manifests
- Markdown - Documentation

**Secondary:**
- JSON - Data serialization (secrets, context, export/import)

## Runtime

**Environment:**
- Python 3.8, 3.9, 3.10, 3.11 (tested in CI/CD pipeline at `C:/Users/Benedikt/HA_AI_Gen_Workflow/.github/workflows/ci-cd.yml`)
- Linux/Unix environments (Docker support via Python 3.11-slim)
- Windows support via Git Bash or WSL

**Package Manager:**
- pip (Python package manager)
- Lockfile: Not present (uses version pinning in `requirements.txt`)

## Frameworks

**Core:**
- Paramiko 3.0.0+ - SSH/SFTP support for remote Home Assistant access (`bin/ssh_transfer.py`)

**GUI (Optional):**
- Streamlit 1.28.0+ - Web-based graphical interface (`bin/workflow_gui.py`)

**Testing:**
- pytest 7.4.0+ - Test runner
- pytest-cov 4.1.0+ - Coverage reporting
- pytest-mock 3.11.1+ - Mock framework
- pytest-asyncio 0.21.1+ - Async test support

**Build/Development:**
- Black 23.7.0+ - Code formatting
- Flake8 6.1.0+ - Linting
- Pylint 3.0.0+ - Code analysis
- Mypy 1.5.0+ - Type checking
- Bandit 1.7.5+ - Security scanning
- pre-commit 1.0+ - Git hooks framework
- ShellCheck (via shellcheck-py) - Bash script validation

**Code Quality Tools:**
- Coverage 7.3.0+ - Test coverage measurement
- Responses 0.23.3+ - HTTP mocking for tests
- Requests-mock 1.11.0+ - Request mocking for integration tests

## Key Dependencies

**Critical:**
- PyYAML 6.0.1+ - YAML parsing for Home Assistant configuration files (`bin/ha_ai_context_gen.py`)
- requests 2.31.0+ - HTTP library for API interactions
- python-dateutil 2.8.2+ - Date and time utilities
- cryptography 41.0.0+ - Fernet encryption for secrets management (`bin/secrets_manager.py`)

**Infrastructure:**
- paramiko 3.0.0+ - SSH/SFTP client for remote Home Assistant systems (`bin/ssh_transfer.py`)
- Streamlit 1.28.0+ - Optional web UI for workflow management (`bin/workflow_gui.py`)

## Configuration

**Environment:**
- Configuration files: `workflow_config.yaml` (main config, user-created from template)
- Template: `config/workflow_config.yaml.template`
- Locations checked: `['workflow_config.yaml', 'config/workflow_config.yaml', '.ha_workflow_config.yaml', '~/.ha_workflow_config.yaml']`
- Default configuration embedded in `WorkflowConfig` class (`bin/workflow_config.py`)

**Build:**
- Makefile: `Makefile` (development shortcuts)
- Docker test environment: `Dockerfile.test` (Python 3.11-slim base)
- Docker Compose: `docker-compose.test.yml` (test orchestration)
- Pre-commit config: `.pre-commit-config.yaml` (git hooks for quality checks)

**Environment Variables:**
- `PYTHONPATH=/workspace/bin` - Added by Docker and setup scripts
- `PYTHONDONTWRITEBYTECODE=1` - Disable .pyc generation (Docker)
- `PYTHONUNBUFFERED=1` - Unbuffered Python output (Docker)

## Platform Requirements

**Development:**
- Python 3.8+ (3.11 recommended for full compatibility)
- pip (latest)
- Git 2.20+
- 500MB+ free disk space for exports
- Optional: Docker & Docker Compose for containerized testing

**Production:**
- Home Assistant 2024+ (OS or Supervised installation)
- Python 3.8+ runtime
- SSH access to Home Assistant host (for remote mode)
- 500MB+ free space for exports/imports/backups

**CI/CD Environment:**
- GitHub Actions (Ubuntu-latest)
- Python 3.8, 3.9, 3.10, 3.11 test matrix
- Codecov integration for coverage reporting
- Trivy vulnerability scanner
- CodeQL security scanning

## Package Versions

**Production Requirements** (`requirements.txt`):
- PyYAML>=6.0.1
- requests>=2.31.0
- python-dateutil>=2.8.2
- cryptography>=41.0.0
- paramiko>=3.0.0
- streamlit>=1.28.0 (optional for GUI)

**Test Requirements** (`requirements-test.txt`):
- All production requirements
- pytest>=7.4.0
- pytest-cov>=4.1.0
- pytest-mock>=3.11.1
- pytest-asyncio>=0.21.1
- pylint>=3.0.0
- black>=23.7.0
- flake8>=6.1.0
- mypy>=1.5.0
- bandit>=1.7.5
- responses>=0.23.3
- requests-mock>=1.11.0
- coverage>=7.3.0

## Code Quality Standards

**Formatting:**
- Black: 120 character line length (`Makefile`, `.pre-commit-config.yaml`)
- Configured in: `.pre-commit-config.yaml`

**Linting:**
- Flake8: 120 character max, ignores E203 and W503
- Pylint: Optional (warnings don't block CI)
- ShellCheck: Warning severity level

**Type Checking:**
- Mypy: Configured in `pytest.ini`, Python 3.8+, ignores missing imports

**Security:**
- Bandit: Checks bin/ directory, low-level severity filter, ignores tests
- detect-secrets: Secret detection in commits
- Trivy: Filesystem vulnerability scanning in CI/CD

---

*Stack analysis: 2026-08-29*
