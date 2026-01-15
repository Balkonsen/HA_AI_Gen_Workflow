# Developer Guide - HA AI Gen Workflow

## Quick Start for Developers

### Prerequisites
```bash
# System requirements
- Python 3.8+
- Git
- Bash
- pip

# Recommended
- Docker (for isolated testing)
- ShellCheck (for bash validation)
- pre-commit (for git hooks)
```

### Initial Setup
```bash
# 1. Clone repository
git clone https://github.com/Balkonsen/HA_AI_Gen_Workflow.git
cd HA_AI_Gen_Workflow

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements-test.txt

# 4. Setup pre-commit hooks
pip install pre-commit
pre-commit install

# 5. Run initial tests
pytest -v
```

## Development Environment

### Directory Structure Explained
```
HA_AI_Gen_Workflow/
├── bin/                    # Core Python modules
│   ├── ha_ai_context_gen.py
│   ├── ha_config_import.py
│   ├── ha_diagnostic_export.py
│   └── ha_export_verifier.py
│
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── test_*.py           # Unit tests
│   ├── test_bash_scripts.bats
│   └── validate_shell_scripts.sh
│
├── .github/workflows/      # CI/CD
│   └── ci-cd.yml
│
├── docs/                   # Documentation
│   ├── AGENT_INSTRUCTIONS.md
│   ├── DEVELOPER_GUIDE.md
│   └── ...
│
├── tools/                  # Development tools
│   └── setup_pre_commit.sh
│
├── .pre-commit-config.yaml # Pre-commit hooks
├── pytest.ini              # Pytest configuration
├── requirements-test.txt   # Test dependencies
└── README.md
```

### Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install in development mode
pip install -e .

# Install test dependencies
pip install -r requirements-test.txt

# Deactivate when done
deactivate
```

## Testing

### Running Tests

#### All Tests
```bash
pytest -v
```

#### Specific Test File
```bash
pytest tests/test_context_gen.py -v
```

#### Specific Test Function
```bash
pytest tests/test_context_gen.py::TestHAContextGenerator::test_init -v
```

#### With Coverage
```bash
pytest --cov=bin --cov-report=html --cov-report=term
# View HTML report: open htmlcov/index.html
```

#### Watch Mode (run tests on file changes)
```bash
pip install pytest-watch
ptw -- -v
```

### Test Categories

#### Unit Tests
```bash
pytest -v -m unit
```

#### Integration Tests
```bash
pytest -v -m integration
```

#### Security Tests
```bash
pytest -v -m security
```

### Shell Script Testing
```bash
# Validate all shell scripts
./tests/validate_shell_scripts.sh

# Install BATS (Bash Automated Testing System)
git clone https://github.com/bats-core/bats-core.git
cd bats-core
./install.sh /usr/local

# Run BATS tests
bats tests/test_bash_scripts.bats
```

## Code Quality

### Formatting

#### Python (Black)
```bash
# Check formatting
black --check bin/

# Auto-format
black bin/

# Format specific file
black bin/ha_ai_context_gen.py
```

#### Configuration
Line length: 120 characters (see `pytest.ini`)

### Linting

#### Python (Flake8)
```bash
# Check all Python files
flake8 bin/

# Specific file
flake8 bin/ha_ai_context_gen.py

# With statistics
flake8 bin/ --statistics
```

#### Bash (ShellCheck)
```bash
# Check specific script
shellcheck ha_ai_master_script.sh

# Check all scripts
find . -name "*.sh" -exec shellcheck {} \;
```

### Security Scanning

#### Python (Bandit)
```bash
# Scan for security issues
bandit -r bin/

# High severity only
bandit -r bin/ -ll

# Generate report
bandit -r bin/ -f json -o security-report.json
```

#### Secrets Detection
```bash
# Install detect-secrets
pip install detect-secrets

# Create baseline
detect-secrets scan > .secrets.baseline

# Check for new secrets
detect-secrets scan --baseline .secrets.baseline
```

## Pre-commit Hooks

### Setup
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Install commit-msg hook
pre-commit install --hook-type commit-msg
```

### Usage
```bash
# Run manually on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Skip hooks (not recommended)
git commit --no-verify

# Update hooks to latest versions
pre-commit autoupdate
```

### Hooks Configured
1. Trailing whitespace removal
2. End-of-file fixer
3. YAML/JSON validation
4. Large file check
5. Private key detection
6. Black formatting
7. Flake8 linting
8. Bandit security
9. ShellCheck
10. Pytest tests

## Git Workflow

### Branch Strategy
```
main (protected)
  ├── develop
  │   ├── feature/new-feature
  │   ├── bugfix/fix-issue
  │   └── refactor/improve-code
  └── hotfix/critical-fix
```

### Creating a Feature
```bash
# Start from develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/my-new-feature

# Make changes
# ... code ...

# Commit changes
git add .
git commit -m "feat(module): Add new feature"

# Push to remote
git push origin feature/my-new-feature

# Create Pull Request on GitHub
```

### Commit Message Convention
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or tools

**Examples:**
```
feat(context-gen): Add device statistics to AI context

Added calculation of device statistics grouped by manufacturer
and model. This provides better context for AI assistants.

Closes #42

---

fix(sanitize): Improve IP address regex pattern

The previous pattern didn't catch all IPv4 formats. Updated
regex to handle edge cases.

Fixes #38

---

docs(readme): Update installation instructions

Added Docker setup instructions and troubleshooting section.
```

## Debugging

### Python Debugging

#### Using pdb
```python
import pdb

def problematic_function():
    x = compute_something()
    pdb.set_trace()  # Debugger will stop here
    return process(x)
```

#### Using pytest with pdb
```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure, then exit
pytest -x --pdb
```

#### Using VSCode Debugger
Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        },
        {
            "name": "Python: Pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["-v", "${file}"]
        }
    ]
}
```

### Bash Debugging
```bash
# Run with debug output
bash -x script.sh

# Debug specific section
set -x  # Enable debugging
command_to_debug
set +x  # Disable debugging

# Validate syntax without running
bash -n script.sh
```

### Logging

#### Python Logging
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Use in code
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.exception("Exception occurred")  # Includes traceback
```

## CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline runs on:
- Push to `main`, `develop`, or `feature/*` branches
- Pull requests to `main` or `develop`
- Manual trigger via GitHub UI

### Pipeline Stages

1. **Lint** (Code quality)
   - Black formatting check
   - Flake8 linting
   - Pylint analysis
   - Bandit security scan

2. **ShellCheck** (Shell validation)
   - Syntax validation
   - Best practices check

3. **Test** (Python tests)
   - Unit tests on Python 3.8, 3.9, 3.10, 3.11
   - Coverage report
   - Codecov upload

4. **Integration** (Integration tests)
   - End-to-end workflows

5. **Security** (Security scanning)
   - Trivy vulnerability scan
   - SARIF upload to GitHub Security

6. **Docs** (Documentation)
   - Markdown link validation

7. **Build** (Package creation)
   - Distribution package
   - Artifact upload

8. **Validate** (Pre-merge checks)
   - Summary of all checks

### Running CI Locally

#### Using Act
```bash
# Install act (GitHub Actions local runner)
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run CI locally
act push

# Run specific job
act -j test-python

# Run with secrets
act -s GITHUB_TOKEN=your_token
```

#### Manual Validation
```bash
# Run all validations
./tools/run_all_validations.sh
```

## Performance Profiling

### Python Profiling
```bash
# Install profiling tools
pip install line_profiler memory_profiler

# Profile function execution time
python -m cProfile -s cumtime bin/ha_ai_context_gen.py

# Profile memory usage
python -m memory_profiler bin/ha_ai_context_gen.py
```

### Bash Profiling
```bash
# Measure execution time
time ./ha_ai_master_script.sh export

# Detailed profiling
PS4='+ $(date "+%s.%N")\011 ' bash -x script.sh
```

## Documentation

### Updating Documentation
```bash
# Check documentation
./docs/

# Generate API documentation (if using sphinx)
pip install sphinx
cd docs
make html
```

### Documentation Standards
- Use Markdown for all documentation
- Include code examples
- Keep docs in sync with code
- Add diagrams for complex flows

## Release Process

### Version Numbering
Format: `YYYY.MM.DD-HASH`
Example: `2026.01.15-a1b2c3d4`

### Creating a Release
```bash
# 1. Ensure all tests pass
pytest -v
./tests/validate_shell_scripts.sh

# 2. Update changelog
# Edit CHANGELOG.md

# 3. Commit changes
git add CHANGELOG.md
git commit -m "chore: Prepare release v2026.01.15"

# 4. Merge to main
git checkout main
git merge develop

# 5. Tag release (automated by CI)
# or manually:
git tag -a v2026.01.15 -m "Release v2026.01.15"
git push origin v2026.01.15

# 6. CI will create GitHub release automatically
```

## Troubleshooting

### Common Issues

#### Tests Failing Locally
```bash
# Clear pytest cache
rm -rf .pytest_cache
find . -name "__pycache__" -exec rm -rf {} +

# Reinstall dependencies
pip install -r requirements-test.txt --force-reinstall

# Run with verbose output
pytest -vv
```

#### Import Errors
```bash
# Ensure PYTHONPATH includes bin/
export PYTHONPATH="${PYTHONPATH}:$(pwd)/bin"

# Or install in development mode
pip install -e .
```

#### Pre-commit Hook Failures
```bash
# Update hooks
pre-commit autoupdate

# Clean and reinstall
pre-commit clean
pre-commit install

# Run manually to see errors
pre-commit run --all-files
```

## Best Practices

### Code Style
- Follow PEP 8 for Python
- Use type hints
- Write docstrings for all public functions
- Keep functions small and focused
- Prefer explicit over implicit

### Testing
- Write tests before/with code (TDD)
- Aim for >80% code coverage
- Test edge cases and error conditions
- Use fixtures for common setup
- Mock external dependencies

### Security
- Never commit secrets
- Always sanitize user input
- Validate all external data
- Use secure coding practices
- Run security scans regularly

### Performance
- Profile before optimizing
- Avoid premature optimization
- Use appropriate data structures
- Consider memory usage
- Cache expensive operations

## Additional Resources

- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

## Getting Help

1. Check existing documentation in `docs/`
2. Review test cases for examples
3. Search GitHub issues
4. Create detailed issue with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Error messages/logs
