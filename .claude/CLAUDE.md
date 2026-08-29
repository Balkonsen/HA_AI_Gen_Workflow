<!-- GSD:project-start source:PROJECT.md -->

## Project

**HA AI Config Optimizer**

A rebuild of a prior Home Assistant tooling project that never reached a functional
state. The rewrite is a local-network tool that connects directly to a running Home
Assistant server over SSH, analyzes its full YAML configuration (including dashboards),
proposes optimizations from both deterministic rule passes and a cloud LLM, and applies
the changes the user approves — validated on a host-side staging copy first, every apply
git-committed, with one-command rollback. It replaces the old export -> sanitize ->
generate -> validate -> import file-shuffling workflow with direct access.

**Core Value:** Safely apply reviewed optimizations to a live Home Assistant config over the local
network, with one-command rollback — no import/export cycle.

### Constraints

- **Tech stack**: Python 3.12+, strict typing (pydantic v2, mypy --strict) — chosen because
  ruamel.yaml is the only mature comment/anchor-preserving YAML round-tripper, HA itself is
  Python (tag semantics, `hass --script check_config`, entity model map 1:1), and the LLM SDKs
  are Python-native. Go / Rust / TypeScript were rejected specifically on YAML round-trip fidelity.

- **YAML handling**: must preserve comments, anchors, and tag structure across read -> edit -> write.
- **Security**: no real secret material in any outbound LLM request (redact-on-send is mandatory).
- **Access**: SSH only for M1 (asyncssh, SFTP + exec); HA REST/WebSocket API is M2+.
- **Safety**: no change reaches live config without passing host-side staging validation AND
  explicit per-hunk user approval.

- **Compatibility**: HA OS / Supervised, HA Container, HA Core — path-layout differences
  abstracted behind config.

- **Distribution**: packaged via uv / pipx or a container image.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python 3.8+ - Core application logic, CLI tools, and workflow orchestration
- Bash/Shell - Infrastructure scripts for setup, deployment, and automation
- YAML - Configuration files and Home Assistant manifests
- Markdown - Documentation
- JSON - Data serialization (secrets, context, export/import)

## Runtime

- Python 3.8, 3.9, 3.10, 3.11 (tested in CI/CD pipeline at `C:/Users/Benedikt/HA_AI_Gen_Workflow/.github/workflows/ci-cd.yml`)
- Linux/Unix environments (Docker support via Python 3.11-slim)
- Windows support via Git Bash or WSL
- pip (Python package manager)
- Lockfile: Not present (uses version pinning in `requirements.txt`)

## Frameworks

- Paramiko 3.0.0+ - SSH/SFTP support for remote Home Assistant access (`bin/ssh_transfer.py`)
- Streamlit 1.28.0+ - Web-based graphical interface (`bin/workflow_gui.py`)
- pytest 7.4.0+ - Test runner
- pytest-cov 4.1.0+ - Coverage reporting
- pytest-mock 3.11.1+ - Mock framework
- pytest-asyncio 0.21.1+ - Async test support
- Black 23.7.0+ - Code formatting
- Flake8 6.1.0+ - Linting
- Pylint 3.0.0+ - Code analysis
- Mypy 1.5.0+ - Type checking
- Bandit 1.7.5+ - Security scanning
- pre-commit 1.0+ - Git hooks framework
- ShellCheck (via shellcheck-py) - Bash script validation
- Coverage 7.3.0+ - Test coverage measurement
- Responses 0.23.3+ - HTTP mocking for tests
- Requests-mock 1.11.0+ - Request mocking for integration tests

## Key Dependencies

- PyYAML 6.0.1+ - YAML parsing for Home Assistant configuration files (`bin/ha_ai_context_gen.py`)
- requests 2.31.0+ - HTTP library for API interactions
- python-dateutil 2.8.2+ - Date and time utilities
- cryptography 41.0.0+ - Fernet encryption for secrets management (`bin/secrets_manager.py`)
- paramiko 3.0.0+ - SSH/SFTP client for remote Home Assistant systems (`bin/ssh_transfer.py`)
- Streamlit 1.28.0+ - Optional web UI for workflow management (`bin/workflow_gui.py`)

## Configuration

- Configuration files: `workflow_config.yaml` (main config, user-created from template)
- Template: `config/workflow_config.yaml.template`
- Locations checked: `['workflow_config.yaml', 'config/workflow_config.yaml', '.ha_workflow_config.yaml', '~/.ha_workflow_config.yaml']`
- Default configuration embedded in `WorkflowConfig` class (`bin/workflow_config.py`)
- Makefile: `Makefile` (development shortcuts)
- Docker test environment: `Dockerfile.test` (Python 3.11-slim base)
- Docker Compose: `docker-compose.test.yml` (test orchestration)
- Pre-commit config: `.pre-commit-config.yaml` (git hooks for quality checks)
- `PYTHONPATH=/workspace/bin` - Added by Docker and setup scripts
- `PYTHONDONTWRITEBYTECODE=1` - Disable .pyc generation (Docker)
- `PYTHONUNBUFFERED=1` - Unbuffered Python output (Docker)

## Platform Requirements

- Python 3.8+ (3.11 recommended for full compatibility)
- pip (latest)
- Git 2.20+
- 500MB+ free disk space for exports
- Optional: Docker & Docker Compose for containerized testing
- Home Assistant 2024+ (OS or Supervised installation)
- Python 3.8+ runtime
- SSH access to Home Assistant host (for remote mode)
- 500MB+ free space for exports/imports/backups
- GitHub Actions (Ubuntu-latest)
- Python 3.8, 3.9, 3.10, 3.11 test matrix
- Codecov integration for coverage reporting
- Trivy vulnerability scanner
- CodeQL security scanning

## Package Versions

- PyYAML>=6.0.1
- requests>=2.31.0
- python-dateutil>=2.8.2
- cryptography>=41.0.0
- paramiko>=3.0.0
- streamlit>=1.28.0 (optional for GUI)
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

- Black: 120 character line length (`Makefile`, `.pre-commit-config.yaml`)
- Configured in: `.pre-commit-config.yaml`
- Flake8: 120 character max, ignores E203 and W503
- Pylint: Optional (warnings don't block CI)
- ShellCheck: Warning severity level
- Mypy: Configured in `pytest.ini`, Python 3.8+, ignores missing imports
- Bandit: Checks bin/ directory, low-level severity filter, ignores tests
- detect-secrets: Secret detection in commits
- Trivy: Filesystem vulnerability scanning in CI/CD

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Language & Runtime

- All source files require Python 3.8+ type annotations
- Shebang: `#!/usr/bin/env python3` (line 1 of all executable scripts)

## Naming Patterns

- All lowercase with underscores: `ha_context_gen.py`, `ssh_transfer.py`
- Main modules in `bin/` directory: `bin/workflow_orchestrator.py`, `bin/secrets_manager.py`
- Test files: `test_*.py` prefix in `tests/` directory
- snake_case: `safe_yaml_load()`, `_ensure_directories()`, `export_from_remote()`
- Private methods: Leading underscore `_init_encryption()`, `_generate_label()`
- Public methods: No underscore prefix
- snake_case: `export_path`, `secrets_map`, `connection_timeout`
- Private attributes: Leading underscore `_secrets`, `_fernet`, `_counter`
- Constants: UPPER_CASE: `MAX_AI_FILE_SIZE`, `CRYPTO_AVAILABLE`
- PascalCase: `HAContextGenerator`, `SecretsManager`, `WorkflowOrchestrator`
- Descriptive names indicating responsibility: `HARemoteManager`, `ExportVerifier`
- Used for function parameters and return types: `def __init__(self, config_path: Optional[str] = None)`
- Common types: `Optional[str]`, `Dict[str, Any]`, `List[str]`, `Tuple[str, int]`
- File: `bin/workflow_orchestrator.py` lines 30-42 show pattern

## Code Style

- Tool: Black
- Line length: 120 characters (configured in `.pre-commit-config.yaml` line 29, `.vscode/settings.json` line 19, `pytest.ini` line 36)
- Format on save: Enabled in VSCode (`.vscode/settings.json` line 22)
- Run with: `make format` or `black --line-length 120 bin/`
- Tool: Flake8
- Max line length: 120 characters
- Ignored rules: E203 (whitespace before colon), W503 (line break before binary operator)
- Config: `.pre-commit-config.yaml` line 36, `pytest.ini` line 36
- Run with: `make lint`
- MyPy: Type checking enabled with `warn_return_any = True` (pytest.ini line 48)
- Bandit: Security scanning enabled (`.pre-commit-config.yaml` line 42)
- Pylint: Optional additional checks (Makefile line 59)

## Import Organization

- Add bin directory to path: `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`
- Use `Path` from pathlib: `from pathlib import Path`
- File: `bin/workflow_orchestrator.py` line 16

## Docstrings

- Use triple quotes with description
- Example: `bin/ha_diagnostic_export.py` lines 2-15
- Triple quotes with one-line description
- Example: `class HAContextGenerator:` followed by docstring explaining purpose
- Triple quotes with description, Args, and Returns sections
- Args: List parameter name and type
- Returns: Describe return type and value
- Example from `bin/workflow_orchestrator.py` lines 36-42:

## Error Handling

- Use try-except blocks with specific exception types
- Catch narrowly: avoid bare `except:`
- Log warnings for recoverable errors
- Return None or False for graceful failures
- Example from `bin/ha_ai_context_gen.py` lines 61-78:
- Optional fallback imports: `try: import X except ImportError: X_AVAILABLE = False` (secrets_manager.py line 18)
- Graceful degradation: Return status booleans or error dicts
- Always provide user feedback via print statements or logging

## Logging & Output

- Success: `print("✓ message")` or `print(f"✓ Loaded {count} items")`
- Warning: `print("⚠ message")`
- Error: `print("✗ message")`
- Info: `print("→ message")` or plain `print("message")`
- Example from `bin/secrets_manager.py` lines 67, 80, 82, 91, 93
- Every major operation start/completion
- Non-fatal errors and warnings
- Data counts and progress

## Comments

- Complex algorithms or non-obvious logic
- HA-specific behavior (YAML tags, config directives)
- Important assumptions or constraints
- Workarounds for known issues
- Obvious comments restating code
- Outdated comments after code changes

## Function Design

- Use type hints for all parameters
- Use Optional[] for nullable parameters
- Provide default values for optional parameters
- Example: `def __init__(self, secrets_dir: str = "./secrets", label_prefix: str = "HA_SECRET")` (secrets_manager.py line 31)
- Always specify return type hint
- Return tuples for multiple values: `Tuple[bool, str]`
- Return None for optional operations
- Use booleans for success/failure: `success, message = operation()` (workflow_orchestrator.py line 66-69)
- Prefix with underscore: `_init_encryption()`, `_load_existing()`
- Call from within class only

## Module Design

- Classes are main exports (no underscore prefix)
- Functions typically internal to classes
- Exception classes for specific errors
- Class initialization via `__init__` with clear docstring
- Private initialization methods for setup: `_init_encryption()`, `_ensure_directories()`
- Minimize mutable class state
- Use attributes for configuration and results
- Example: `self.export_path`, `self.secrets_map`, `self.context`
- Private: attributes and methods with leading underscore
- Public: everything else
- Docstring documents public interface

## Whitespace & Formatting

- Unix line endings (LF)
- Final newline at end of file
- No trailing whitespace (enforced by pre-commit hook)
- 4 spaces per indent level (Black standard)
- Never use tabs
- Two blank lines between class definitions
- One blank line between method definitions
- One blank line before block-level comments

## Conditional Imports

## Pre-Commit Hooks

- Trailing whitespace
- End of file fixer
- YAML, JSON validation
- Detect private keys
- Mixed line endings
- Black formatting
- Flake8 linting
- Bandit security
- ShellCheck (shell scripts)
- YAMLLint
- MarkdownLint
- Pytest (all tests must pass)
- Run: `make pre-commit` or `pre-commit install`
- Bypass (not recommended): `git commit --no-verify`

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| WorkflowOrchestrator | Coordinates complete workflow pipeline, manages state, handles errors | `bin/workflow_orchestrator.py` |
| HAConfigExporter | Exports HA configuration from local or remote, handles file collection | `bin/ha_diagnostic_export.py` |
| SecretsSanitizer | Identifies and removes sensitive data, replaces with labeled placeholders | `bin/secrets_manager.py` |
| SecretsManager | Encrypts/decrypts secrets, manages encryption keys, stores mappings | `bin/secrets_manager.py` |
| HAContextGenerator | Analyzes configuration, generates AI-friendly documentation | `bin/ha_ai_context_gen.py` |
| HAConfigImporter | Imports sanitized configuration back to HA, restores secrets | `bin/ha_config_import.py` |
| ExportVerifier | Validates export structure, checks YAML syntax, verifies entity references | `bin/ha_export_verifier.py` |
| HARemoteManager | Handles SSH connections, transfers files, manages remote operations | `bin/ssh_transfer.py` |
| WorkflowConfig | Loads and manages configuration from YAML, provides defaults | `bin/workflow_config.py` |

## Pattern Overview

- **Sequential workflow**: Export → Sanitize → Generate → Validate → Import
- **Clear separation of concerns**: Each component has a single responsibility
- **Configuration-driven**: All behavior controlled by YAML configuration
- **Error handling**: Each step can fail independently with recovery options
- **Reversible operations**: Exports and backups allow rollback capability

## Layers

- Purpose: User interfaces and entry points
- Location: `bin/workflow_orchestrator.py`, `bin/workflow_gui.py`, `ha_ai_master_script.sh`
- Contains: CLI arguments parsing, GUI forms, shell script command handling
- Depends on: Orchestrator layer
- Used by: End users, CI/CD systems, VS Code tasks
- Purpose: Coordinates workflow stages and manages overall execution flow
- Location: `bin/workflow_orchestrator.py` (WorkflowOrchestrator class)
- Contains: run_full_workflow(), export_from_remote(), import_local(), etc.
- Depends on: Service layer, Configuration layer
- Used by: Presentation layer
- Purpose: Individual workflow services for export, import, validation
- Location: `bin/ha_diagnostic_export.py`, `bin/ha_config_import.py`, `bin/ha_export_verifier.py`, `bin/ha_ai_context_gen.py`
- Contains: Core business logic for each workflow step
- Depends on: Support layer (configuration, secrets, SSH)
- Used by: Orchestration layer
- Purpose: Cross-cutting concerns (configuration, secrets, SSH, validation)
- Location: `bin/workflow_config.py`, `bin/secrets_manager.py`, `bin/ssh_transfer.py`
- Contains: Configuration management, encryption/decryption, SSH operations
- Depends on: External libraries (PyYAML, cryptography, paramiko)
- Used by: Service layer, Orchestration layer
- Purpose: External system integration (Home Assistant, SSH remotes, file system)
- Location: Various (embedded in service classes)
- Contains: Home Assistant communication, SSH connections, file I/O
- Depends on: External libraries and network/file system
- Used by: Service layer

## Data Flow

### Primary Request Path: Full Workflow Export

### Secondary Flow: Configuration Import

### Configuration Loading Flow

- Minimal state: Each component is largely stateless
- Configuration object passed between components
- Secrets manager maintains in-memory cache of decrypted secrets
- Orchestrator tracks paths and timestamps for workflow stages

## Key Abstractions

- Purpose: Abstract the identification and replacement of sensitive data
- Examples: `bin/secrets_manager.py` (SecretsSanitizer class)
- Pattern: Visitor pattern - iterates files/fields, sanitizes in-place
- Purpose: Handle Home Assistant-specific YAML tags gracefully
- Examples: `bin/ha_ai_context_gen.py:15` (custom loader with tag constructors)
- Pattern: Adapter pattern - wraps PyYAML to handle HA extensions
- Purpose: Represent discrete, chainable workflow steps
- Examples: export, sanitize, context, validate, import
- Pattern: Pipeline pattern - each stage consumes output of previous

## Entry Points

- Location: `bin/workflow_orchestrator.py`
- Triggers: `python3 bin/workflow_orchestrator.py <command>`
- Responsibilities: Parse arguments, create orchestrator, execute command
- Commands: setup, export, sanitize, context, import, validate, full
- Location: `ha_ai_master_script.sh`
- Triggers: `./ha_ai_master_script.sh <command>`
- Responsibilities: Environment setup, dependency checking, logging, orchestration
- Commands: export, context, import, validate, full
- Location: `bin/workflow_gui.py`
- Triggers: `streamlit run bin/workflow_gui.py`
- Responsibilities: Web UI, interactive workflows, visualization
- Location: `tests/conftest.py`, `tests/test_*.py`
- Triggers: `pytest` or `python -m pytest`
- Responsibilities: Unit and integration testing

## Architectural Constraints

- **Threading:** Single-threaded event model; no concurrent operations (SSH and file I/O are sequential)
- **Global state:** 
- **Circular imports:** None detected; imports flow unidirectionally through orchestrator
- **SSH dependencies:** SSH operations optional; codebase handles gracefully if paramiko unavailable
- **File permissions:** Encryption key file restricted to 0o600 (Unix only)
- **Configuration:** All runtime behavior determined by YAML config; no hardcoded business logic

## Anti-Patterns

### Mixing Responsibilities in Services

### Hardcoded Paths in Components

### Secret Values in Logs

## Error Handling

- Try-except blocks in service methods catch specific exceptions
- Errors propagate up with context; orchestrator decides recovery
- YAML parsing errors fall back to raw text extraction (`bin/ha_ai_context_gen.py:61`)
- SSH failures don't block local operations (`bin/workflow_orchestrator.py:71`)
- Validation produces detailed reports rather than boolean pass/fail

## Cross-Cutting Concerns

- bash: Color-coded terminal output with `log()`, `info()`, `success()`, `warn()`, `error()` in `ha_ai_master_script.sh`
- Python: Uses print() with status indicators (✓, ✗, ⚠, 🤖); no centralized logger configured
- YAML syntax via PyYAML parser
- Entity ID format checking in `bin/ha_export_verifier.py`
- Secret placeholder consistency verification
- Path existence and accessibility checks
- SSH: Key-based (default) or password-based via paramiko (`bin/ssh_transfer.py`)
- Local: File system permissions
- HA API: Token-based (if needed for future enhancements)

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
