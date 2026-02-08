# Copilot Instructions for HA AI Gen Workflow

## Project Overview

**HA AI Gen Workflow** is a Home Assistant add-on that enables users to safely export their Home Assistant configurations, sanitize sensitive data, generate AI-ready context, and import AI-modified configurations back. The tool automatically detects and replaces secrets (passwords, tokens, API keys, IP addresses, etc.) with labeled placeholders, making it safe to share configurations with AI assistants.

**Key Features:**
- Automatic secret sanitization and restoration
- AI-ready export with context generation
- Safe import with secret restoration
- Web GUI via Streamlit
- SSH support for remote Home Assistant instances
- Configuration validation

## Technology Stack

- **Language**: Python 3.8+
- **Key Libraries**: PyYAML, requests, cryptography (>=42.0.4), paramiko (SSH), streamlit (GUI)
- **Testing**: pytest with coverage reporting
- **Code Quality**: black (formatter), flake8 (linter), pylint, bandit (security)
- **CI/CD**: GitHub Actions with Home Assistant builder
- **Deployment**: Docker container as Home Assistant add-on (amd64, aarch64 only — NO armv7)

## Directory Structure

```
/
├── .github/
│   ├── copilot-instructions.md   # THIS FILE
│   └── workflows/
│       └── docker-build.yml      # HA builder CI/CD
├── bin/                          # Main Python modules
│   ├── workflow_orchestrator.py  # Main entry point
│   ├── workflow_gui.py           # Streamlit web interface
│   ├── workflow_logger.py        # Centralized logging system
│   ├── ha_diagnostic_export.py   # Export HA configurations
│   ├── ha_config_import.py       # Import configurations
│   ├── ha_ai_context_gen.py      # Generate AI context
│   ├── secrets_manager.py        # Secret sanitization/encryption
│   ├── ssh_transfer.py           # Remote SSH operations
│   ├── ha_api_client.py          # HA API client
│   ├── ha_export_verifier.py     # Export validation (v1.0 + v2.0)
│   └── workflow_config.py        # Configuration management
├── ha_ai_workflow_addon/         # HA add-on (Docker build context)
│   ├── config.yaml               # VERSION SOURCE OF TRUTH
│   ├── build.yaml                # Architecture base images
│   ├── Dockerfile                # Container build
│   └── run.sh                    # Startup script (NO bashio/s6)
├── tests/                        # Test suite
│   ├── conftest.py               # Pytest fixtures
│   └── test_*.py                 # Test modules
├── tools/                        # Dev/validation tools
├── Makefile                      # Development shortcuts
├── requirements.txt              # Production deps
└── requirements-test.txt         # Dev/test deps
```

## CRITICAL RULES — Learned from Past Failures

### 1. Docker Build Context (PR #38, #40)
The HA builder sets `ha_ai_workflow_addon/` as the Docker build context. ALL Dockerfile COPY paths MUST be relative to that directory, NOT the repo root.
```dockerfile
# ✅ CORRECT — relative to ha_ai_workflow_addon/
COPY run.sh /run.sh
COPY requirements.txt /tmp/requirements.txt
COPY bin/ /app/bin/

# ❌ WRONG — repo-root paths fail in HA builder context
COPY ha_ai_workflow_addon/run.sh /run.sh
```
The CI workflow stages repo-root files (bin/, config/, templates/, requirements.txt) INTO `ha_ai_workflow_addon/` before build.

### 2. Version and CHANGELOG Synchronization (PR #36, #52)
**CRITICAL RULE:** When bumping version, ALWAYS update CHANGELOG.md in the same commit/PR.

Version MUST be identical across ALL files:
- `ha_ai_workflow_addon/config.yaml` (source of truth)
- `ha_ai_workflow_addon/build.yaml`
- Dockerfile labels

**CHANGELOG.md Update Process (worked perfectly through 1.0.6):**
1. When you bump version in `config.yaml`, immediately add a new section to `CHANGELOG.md`
2. Place it right after `## [Unreleased]`
3. Use format: `## [X.X.X] - YYYY-MM-DD`
4. Document actual changes with categories: Fixed/Added/Changed/Removed/Security
5. Include PR numbers and bold descriptions
6. See `docs/VERSION_CHANGELOG_GUIDE.md` for examples

**Example:**
```markdown
## [1.0.15] - 2026-02-08

### Fixed
- **Docker build issue** — Fixed context paths (PR #XX)

### Added
- **New feature** — Description of feature (PR #XX)
```

**DO NOT:**
- ❌ Bump version without updating CHANGELOG
- ❌ Use vague entries like "version bump" or "updates"
- ❌ Skip PR numbers or descriptions

The CI extracts version from config.yaml. Human-written CHANGELOG entries are mandatory.

### 3. NO bashio or s6-overlay in run.sh (PR #26, #27)
The run.sh script must use pure bash — no `bashio::` functions, no `#!/usr/bin/with-contenv bashio`. Config reading uses `jq` with `--arg` for safe parameter passing from `/data/options.json`.
```bash
# ✅ CORRECT
#!/usr/bin/env bash
get_config() { jq -r --arg key "$1" '.[$key] // empty' /data/options.json; }

# ❌ WRONG — causes PID 1 crash
#!/usr/bin/with-contenv bashio
bashio::config 'export_path'
```

### 4. Streamlit Behind HA Ingress (PR #28, #29, #30)
- Do NOT set `--server.baseUrlPath` in add-on mode — HA Ingress uses dynamic session tokens
- MUST set `--server.enableWebsocketCompression=false` for Streamlit 1.10+
- MUST set `--server.enableCORS=false` and `--server.enableXsrfProtection=false`

### 5. Architecture — 64-bit ONLY (PR #36)
- Supported: `amd64`, `aarch64`
- NOT supported: `armv7` (removed for HA 2026.2.0+ compatibility)
- Never add armv7 back to config.yaml, build.yaml, or CI workflow

### 6. Python Dependency Pins (PR #21)
- `rpds-py<0.30.0` — required for Alpine Cargo compatibility
- `cryptography>=42.0.4` — security CVE fixes
- Always check that new dependencies build on Alpine/musl

### 7. Path Resolution (PR #41)
- Always use `os.path.abspath()` after `os.path.expanduser(os.path.expandvars())`
- Never hardcode `/config/ai_exports` — only valid inside HA Docker container
- Use `os.path.abspath("./exports")` as fallback for non-container environments

### 8. Export Format Versioning (PR #37)
The export verifier supports TWO formats:
- **v2.0**: `ai_upload/` with `ha_entities.json`, `ha_config.yaml`, `ha_context.md`
- **v1.0 (legacy)**: `config/`, `diagnostics/`, `addons/`
Always maintain backward compatibility. Use `_detect_export_version()`.

### 9. API Method Signatures (PR #34)
Before calling any method, verify its ACTUAL signature in the source code.
```python
# ✅ CORRECT — generate_context_file() takes no params, returns tuple
context_file, prompt_file = generator.generate_context_file()

# ❌ WRONG — don't guess parameter signatures
generator.generate_context_file(str(context_file))
```

### 10. Shell Script Standards (PR #1, #32)
- Use `$*` (not `$@`) in echo/logging functions to avoid SC2145
- ALL `.sh` files MUST be executable (`chmod +x`)
- Redirect stderr on glob patterns AFTER the loop: `done 2>/dev/null`
- Use `shlex.quote()` in Python when constructing shell commands

## Coding Conventions

### Python Style
- **Line Length**: 120 characters maximum
- **Formatter**: `black --line-length 120`
- **Linter**: `flake8 --ignore=E203,W503`
- **Docstrings**: Triple-quoted for all functions, classes, modules
- **Type Hints**: Required on function signatures
- **Naming**: PascalCase (classes), snake_case (functions), UPPER_SNAKE_CASE (constants), _underscore (private)

### Code Organization
- **Imports**: stdlib → third-party → local
- **Error Handling**: Specific exceptions (never bare `except Exception`)
  - SSH: `subprocess.TimeoutExpired`, `FileNotFoundError`, `PermissionError` + stderr parsing
  - YAML: `yaml.YAMLError`
  - API: specific HTTP status code handling
- **Logging**: Use `workflow_logger.get_logger()` for structured logging
  - Levels: DEBUG, VERBOSE, INFO, CONDENSED, WARNING, ERROR, CRITICAL
  - Context tracking: `logger.push_context()` / `logger.pop_context()`
  - Emoji prefixes: ✓ (success), ⚠ (warning), ✗/❌ (error), → (info), ⏳ (progress)
- **Configuration**: Always use `WorkflowConfig` class
- **Secrets**: Never log, never commit, encrypt at rest

### Configuration Management
- Use `WorkflowConfig` class for all configuration access
- Configuration files are in YAML format
- Support both local and remote (SSH) operations
- Store secrets encrypted in dedicated directory (never in version control)

### File Operations
- Always use `pathlib.Path` for cross-platform compatibility
- Create parent directories with `Path.mkdir(parents=True, exist_ok=True)`
- Use context managers for file operations:
  ```python
  with open(file_path, 'r') as f:
      content = f.read()
  ```

## Testing Requirements

### Before Every PR
```bash
make format     # Auto-format with black
make lint       # Linting checks
make test       # Full test suite
make security   # Bandit security scan
```

### Running Tests
```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration

# With coverage
make coverage
```

### Test Structure
- Tests in `tests/test_<module>.py`
- Use pytest fixtures from `conftest.py`
- Mock ALL external dependencies (SSH, API, filesystem)
- Use `tmp_path` for temporary files
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`
- Target: >80% coverage on new code

### Test Patterns That Work
```python
# Mock SSH operations
with mock.patch('subprocess.run') as mock_run:
    mock_run.return_value = MagicMock(returncode=0, stderr=b'')
    result = ssh_transfer.test_connection()

# Mock file operations with tmp_path
def test_export(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    # ... test with real filesystem operations

# Mock HA API
with mock.patch('requests.get') as mock_get:
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"result": "ok"}
```

## PR Checklist — MANDATORY

Before submitting ANY pull request:
1. [ ] `make format` passes (black formatting)
2. [ ] `make lint` passes (flake8 + pylint)
3. [ ] `make test` passes (all tests green)
4. [ ] `make security` passes (bandit clean)
5. [ ] New tests written for new functionality
6. [ ] CHANGELOG.md updated for user-facing changes
7. [ ] Version synchronized if config.yaml changed
8. [ ] Dockerfile COPY paths relative to addon context
9. [ ] No hardcoded container paths in non-container code
10. [ ] No armv7 references introduced
11. [ ] No bashio/s6 functions in shell scripts
12. [ ] All .sh files are executable
13. [ ] Backward compatibility maintained

## Common Pitfalls to AVOID

| Pitfall | Consequence | Prevention |
|---------|-------------|------------|
| Using `bashio::` in run.sh | PID 1 crash, addon won't start | Use pure bash + jq |
| Setting baseUrlPath for Streamlit | 404 errors via HA Ingress | Omit in addon mode |
| Repo-root COPY paths in Dockerfile | Build fails silently | Use addon-relative paths |
| Catching bare `Exception` | Hides real errors, retry logic fails | Catch specific exceptions |
| Missing `os.path.abspath()` | Files written to wrong directory | Always resolve to absolute |
| Adding armv7 architecture | HA 2026.2.0+ rejects addon | Keep amd64 + aarch64 only |
| Hardcoding `/config/ai_exports` | Breaks non-container installs | Use config-driven paths |
| Mismatched versions across files | HA won't detect updates | Sync config.yaml → all files |
| Unquoted `$@` in bash echo | ShellCheck SC2145 warnings | Use `$*` in echo statements |
| Guessing API method signatures | Runtime crashes, empty output | Read actual source first |

## Common Patterns

### Working with Secrets
```python
from secrets_manager import SecretsManager, SecretsSanitizer

# Initialize
secrets_manager = SecretsManager(secrets_dir="/path/to/secrets")

# Sanitize content
sanitizer = SecretsSanitizer(secrets_manager)
sanitized_content = sanitizer.sanitize_file_content(content, filename)

# Restore secrets
restored_content = secrets_manager.restore_secrets(sanitized_content)
```

### SSH Operations
```python
from ssh_transfer import HARemoteManager

# Initialize with SSH config
ssh_config = {
    "enabled": True,
    "host": "192.168.1.100",
    "user": "root",
    "port": 22,
    "key_path": "/path/to/key"
}
remote_manager = HARemoteManager(ssh_config)

# Export from remote
success = remote_manager.export_config("/local/export/path", exclude_patterns=[])
```

### Configuration Access
```python
from workflow_config import WorkflowConfig

config = WorkflowConfig()  # Auto-loads from default location
export_dir = config.get("paths.export_dir")
ssh_enabled = config.get("ssh.enabled", default=False)
```

## Development Workflow

### Initial Setup
```bash
make dev-setup    # Install deps + pre-commit hooks
```

### Development Cycle
```bash
make format       # Auto-format with black
make lint         # Check style
make test         # Run tests
make security     # Security scan
make ci           # Full CI simulation (lint + test + security)
```

### Docker
```bash
make docker-build # Build test image
make docker-test  # Test in container
make docker-shell # Interactive shell
```

### Making Changes
1. **Create feature branch** from main
2. **Make minimal changes** focused on the specific issue
3. **Run linting**: `make lint` or `make format` to auto-fix
4. **Write/update tests** for your changes
5. **Run tests**: `make test` or `make quick-validate`
6. **Run security checks**: `make security`
7. **Commit with descriptive messages**

### Pre-commit Hooks
The project uses pre-commit hooks that automatically run:
- Code formatting (black)
- Linting (flake8)
- Security checks (bandit)
- YAML/JSON validation
- Shell script validation (shellcheck)
- Markdown linting
- Pytest tests

## Important Considerations

### Security
- **Never commit secrets** — use `.gitignore` to exclude `secrets/` directories
- **Validate all user inputs** to prevent path traversal attacks
- **Use paramiko carefully** — validate SSH hosts and keys
- **Encrypt secrets at rest** using `cryptography` library
- Run `make security` before committing changes

### Home Assistant Integration
- The add-on runs as a Docker container in Home Assistant OS
- Uses Home Assistant API for entity/state information
- Supports both local and remote HA instances via SSH
- Configuration directory is typically `/config` in container
- Web GUI is served via Ingress on port 8501

### Error Handling
- Provide clear, actionable error messages
- Use exit codes appropriately (0 = success, non-zero = failure)
- Log detailed errors but show user-friendly messages
- Always clean up temporary files, even on failure

### Performance
- Use streaming for large file operations
- Minimize SSH connections (batch operations when possible)
- Cache API responses when appropriate
- Provide progress indicators for long-running operations

## Architecture Decision Records

1. **Pure bash over bashio**: Container stability (PR #26, #27)
2. **v2.0 export format**: AI-optimized single-directory output (PR #37)
3. **Centralized logger**: Replace print() with structured logging (PR #35)
4. **HA builder over manual Docker**: Official multi-arch build pipeline (PR #40)
5. **64-bit only**: Future-proof for HA 2026.2.0+ (PR #36)
6. **sshpass via env var**: Secure password auth without process list exposure (PR #30)

## Documentation

- **User Documentation**: `README.md` — for end users
- **Developer Guide**: `docs/DEVELOPER_GUIDE.md` — detailed development info
- **Testing Guide**: `docs/TESTING_GUIDE.md` — comprehensive testing docs
- **Agent Instructions**: `docs/AGENT_INSTRUCTIONS.md` — for AI agents working on this project
- **Deployment**: `docs/deployment_guide.md` — deployment and release process

## Additional Resources

- **Repository**: https://github.com/Balkonsen/HA_AI_Gen_Workflow
- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Home Assistant Add-on Store**: Add via repository URL
- **License**: MIT License (see `mit_license.txt`)

## Tips for Contributors

1. **Start small** — Focus on one issue/feature at a time
2. **Read existing code** — Follow established patterns and style
3. **Test thoroughly** — Both unit and integration tests
4. **Document changes** — Update relevant docs and docstrings
5. **Ask questions** — Use GitHub Discussions for clarification
6. **Review the guides** — Check `docs/DEVELOPER_GUIDE.md` for detailed information
7. **Use the Makefile** — It provides shortcuts for common tasks
8. **Keep dependencies minimal** — Only add new dependencies if absolutely necessary

## When Working on This Codebase

- **Check existing tests** before modifying core functionality
- **Update CHANGELOG.md** for user-facing changes
- **Maintain backward compatibility** with existing configurations
- **Consider both local and SSH modes** when adding features
- **Test with actual Home Assistant** when possible (or use docker-test)
- **Respect the minimal change philosophy** — don't refactor unnecessarily
