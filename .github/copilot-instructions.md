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
- **Key Libraries**: PyYAML, requests, cryptography, paramiko (SSH), streamlit (GUI)
- **Testing**: pytest with coverage reporting
- **Code Quality**: black (formatter), flake8 (linter), pylint, bandit (security)
- **CI/CD**: GitHub Actions
- **Deployment**: Docker container as Home Assistant add-on

## Directory Structure

```
/
├── .github/              # GitHub configuration
│   └── workflows/        # CI/CD workflows
├── bin/                  # Main Python modules (executable scripts)
│   ├── workflow_orchestrator.py    # Main entry point and orchestration
│   ├── workflow_gui.py             # Streamlit web interface
│   ├── ha_diagnostic_export.py     # Export HA configurations
│   ├── ha_config_import.py         # Import and restore configurations
│   ├── ha_ai_context_gen.py        # Generate AI context files
│   ├── secrets_manager.py          # Secret sanitization and encryption
│   ├── ssh_transfer.py             # Remote SSH operations
│   ├── ha_api_client.py            # Home Assistant API client
│   ├── ha_export_verifier.py       # Export validation
│   └── workflow_config.py          # Configuration management
├── config/               # Configuration templates
├── docs/                 # Documentation
│   ├── AGENT_INSTRUCTIONS.md       # AI agent guidelines
│   ├── DEVELOPER_GUIDE.md          # Development documentation
│   ├── TESTING_GUIDE.md            # Testing documentation
│   └── deployment_guide.md         # Deployment instructions
├── ha_ai_workflow_addon/ # Home Assistant add-on configuration
│   ├── config.yaml       # Add-on manifest
│   ├── Dockerfile        # Container build
│   └── run.sh            # Add-on startup script
├── templates/            # Template files
├── tests/                # Test suite
│   ├── conftest.py       # Pytest fixtures
│   ├── test_*.py         # Test modules
│   └── validate_shell_scripts.sh   # Shell script validation
├── tools/                # Development and validation tools
├── Makefile              # Development shortcuts
├── requirements.txt      # Production dependencies
└── requirements-test.txt # Development/test dependencies
```

## Coding Conventions

### Python Style

- **Line Length**: 120 characters maximum
- **Formatter**: black with `--line-length 120`
- **Linter**: flake8 with `--ignore=E203,W503`
- **Docstrings**: Use triple-quoted docstrings for all functions, classes, and modules
- **Type Hints**: Use type hints for function signatures (see `typing` module)
- **Naming**:
  - Classes: `PascalCase` (e.g., `WorkflowOrchestrator`, `SecretsManager`)
  - Functions/Methods: `snake_case` (e.g., `export_config`, `sanitize_secrets`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)
  - Private methods: Prefix with underscore (e.g., `_ensure_directories`)

### Code Organization

- **Imports**: Group in order: standard library, third-party, local modules
- **Error Handling**: Use try-except blocks with specific exceptions
- **Logging**: Use print statements with emoji prefixes for user feedback:
  - `✓` for success
  - `⚠` for warnings
  - `✗` or `❌` for errors
  - `→` for informational messages
  - `⏳` for progress indicators

### Configuration Management

- Use `WorkflowConfig` class for all configuration access
- Configuration files are in YAML format
- Support both local and remote (SSH) operations
- Store secrets encrypted in dedicated directory (never in version control)

## Testing Guidelines

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

- Place tests in `tests/` directory
- Name test files as `test_<module>.py`
- Use pytest fixtures in `conftest.py` for common test setup
- Mock external dependencies (file system, SSH, API calls)
- Use `tmp_path` fixture for temporary file operations

### Test Markers

- `@pytest.mark.unit` - Unit tests (fast, no external dependencies)
- `@pytest.mark.integration` - Integration tests (may use filesystem)

### Test Coverage

- Aim for >80% coverage on new code
- Run `make coverage` to generate HTML coverage report
- Review `htmlcov/index.html` for detailed coverage analysis

## Development Workflow

### Initial Setup

```bash
make install          # Install dependencies
make pre-commit       # Set up pre-commit hooks
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

### CI/CD

GitHub Actions automatically run on pull requests:
- Linting and formatting checks
- Full test suite
- Security scans
- Docker build validation

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

### File Operations

- Always use `pathlib.Path` for cross-platform compatibility
- Create parent directories with `Path.mkdir(parents=True, exist_ok=True)`
- Use context managers for file operations:
  ```python
  with open(file_path, 'r') as f:
      content = f.read()
  ```

## Important Considerations

### Security

- **Never commit secrets** - use `.gitignore` to exclude `secrets/` directories
- **Validate all user inputs** to prevent path traversal attacks
- **Use paramiko carefully** - validate SSH hosts and keys
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

## Useful Commands

```bash
# Development
make dev-setup           # Complete development environment setup
make format              # Auto-format all Python code
make lint                # Run all linting checks
make test                # Run complete test suite
make coverage            # Generate coverage report

# Validation
make validate            # Full validation suite
make quick-validate      # Quick validation (faster)
make security            # Security scans only

# Docker
make docker-build        # Build test Docker image
make docker-test         # Run tests in Docker
make docker-shell        # Interactive Docker shell

# Cleanup
make clean               # Remove temporary files and caches

# CI simulation
make ci                  # Run linting, tests, and security (like CI)
```

## Documentation

- **User Documentation**: `README.md` - for end users
- **Developer Guide**: `docs/DEVELOPER_GUIDE.md` - detailed development info
- **Testing Guide**: `docs/TESTING_GUIDE.md` - comprehensive testing docs
- **Agent Instructions**: `docs/AGENT_INSTRUCTIONS.md` - for AI agents working on this project
- **Deployment**: `docs/deployment_guide.md` - deployment and release process

## Additional Resources

- **Repository**: https://github.com/Balkonsen/HA_AI_Gen_Workflow
- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Home Assistant Add-on Store**: Add via repository URL
- **License**: MIT License (see `mit_license.txt`)

## Tips for Contributors

1. **Start small** - Focus on one issue/feature at a time
2. **Read existing code** - Follow established patterns and style
3. **Test thoroughly** - Both unit and integration tests
4. **Document changes** - Update relevant docs and docstrings
5. **Ask questions** - Use GitHub Discussions for clarification
6. **Review the guides** - Check `docs/DEVELOPER_GUIDE.md` for detailed information
7. **Use the Makefile** - It provides shortcuts for common tasks
8. **Keep dependencies minimal** - Only add new dependencies if absolutely necessary

## When Working on This Codebase

- **Check existing tests** before modifying core functionality
- **Update CHANGELOG.md** for user-facing changes
- **Maintain backward compatibility** with existing configurations
- **Consider both local and SSH modes** when adding features
- **Test with actual Home Assistant** when possible (or use docker-test)
- **Respect the minimal change philosophy** - don't refactor unnecessarily
