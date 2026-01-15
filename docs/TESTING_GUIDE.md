# Testing & Validation Infrastructure

Complete test and validation framework for HA AI Gen Workflow.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Test Suite](#test-suite)
- [Validation Tools](#validation-tools)
- [CI/CD Pipeline](#cicd-pipeline)
- [Development Workflow](#development-workflow)
- [Docker Testing](#docker-testing)
- [Agent Instructions](#agent-instructions)

## 🚀 Quick Start

### Initial Setup
```bash
# Install dependencies
make install

# Setup pre-commit hooks
make pre-commit

# Run quick validation
make quick-validate

# Run full test suite
make test
```

### Daily Development
```bash
# Before making changes
make quick-validate

# After making changes
make test
make lint

# Before commit
make validate
```

## 🧪 Test Suite

### Test Organization
```
tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures
├── test_context_gen.py            # Context generator tests
├── test_diagnostic_export.py      # Diagnostic export tests
├── test_config_import.py          # Config import tests
├── test_export_verifier.py        # Verifier tests
├── test_bash_scripts.bats         # Bash tests
└── validate_shell_scripts.sh      # Shell validation
```

### Running Tests

#### All Tests
```bash
pytest -v
# or
make test
```

#### Specific Test File
```bash
pytest tests/test_context_gen.py -v
```

#### Specific Test Class
```bash
pytest tests/test_context_gen.py::TestHAContextGenerator -v
```

#### Specific Test Function
```bash
pytest tests/test_context_gen.py::TestHAContextGenerator::test_init -v
```

#### With Coverage
```bash
pytest --cov=bin --cov-report=html --cov-report=term
# or
make coverage
```

#### Watch Mode
```bash
make test-watch
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

### Shell Script Tests
```bash
# Validate all shell scripts
./tests/validate_shell_scripts.sh
# or
make lint

# Run BATS tests
bats tests/test_bash_scripts.bats
```

## ✅ Validation Tools

### Quick Validation (Fast)
```bash
./tools/quick_validate.sh
# or
make quick-validate
```

Checks:
- Python syntax
- Shell syntax
- Quick test run

**Use this**: During rapid development cycles

### Full Validation (Comprehensive)
```bash
./tools/validate_all.sh
# or
make validate
```

Checks:
1. Environment setup
2. Code formatting (Black)
3. Code linting (Flake8)
4. Type checking (MyPy)
5. Shell script validation
6. Unit tests
7. Code coverage
8. Security scanning (Bandit)
9. YAML validation
10. JSON validation
11. Documentation check
12. Git status
13. Large files check
14. Secrets detection

**Use this**: Before committing/merging

### Pre-commit Hooks

Automatically run on every commit:
```bash
# Setup (one-time)
./tools/setup_pre_commit.sh
# or
make pre-commit

# Run manually
pre-commit run --all-files
# or
make pre-commit-run
```

Hooks include:
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON validation
- Large file detection
- Private key detection
- Black formatting
- Flake8 linting
- Bandit security scan
- ShellCheck
- Pytest execution

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Located in: `.github/workflows/ci-cd.yml`

#### Triggered By:
- Push to `main`, `develop`, `feature/*`
- Pull requests to `main`, `develop`
- Manual trigger

#### Jobs:

1. **lint** - Code quality checks
   - Black formatting
   - Flake8 linting
   - Pylint analysis
   - Bandit security

2. **shellcheck** - Shell validation
   - ShellCheck analysis
   - Best practices validation

3. **test-python** - Unit tests
   - Matrix: Python 3.8, 3.9, 3.10, 3.11
   - Coverage report
   - Codecov upload

4. **test-integration** - Integration tests
   - Full workflow tests

5. **security** - Security scanning
   - Trivy vulnerability scan
   - SARIF upload

6. **docs** - Documentation check
   - Markdown link validation

7. **build** - Package creation
   - Distribution package
   - Artifact upload

8. **validate** - Pre-merge validation
   - All checks summary

9. **release** - Auto-tagging (main only)
   - Version tagging

### Running CI Locally

#### Using Act (GitHub Actions locally)
```bash
# Install act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run all jobs
act push

# Run specific job
act -j test-python

# Run with secrets
act -s GITHUB_TOKEN=your_token
```

#### Simulate CI
```bash
make ci
```

## 🔨 Development Workflow

### Standard Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make Changes**
   - Edit code
   - Write tests
   - Update docs

3. **Quick Validation**
   ```bash
   make quick-validate
   ```

4. **Run Tests**
   ```bash
   make test
   ```

5. **Full Validation**
   ```bash
   make validate
   ```

6. **Commit**
   ```bash
   git add .
   git commit -m "feat(module): Add feature"
   # Pre-commit hooks run automatically
   ```

7. **Push & Create PR**
   ```bash
   git push origin feature/my-feature
   # Create PR on GitHub
   # CI pipeline runs automatically
   ```

### Using VSCode

#### Run Tests
- Press `Ctrl+Shift+P`
- Select "Tasks: Run Task"
- Choose "Run All Tests"

Or use keyboard shortcuts:
- `Ctrl+Shift+T` - Run tests
- `F5` - Debug current file

#### Debug Tests
- Set breakpoint in test file
- Press `F5`
- Select "Python: Pytest Current File"

#### Format Code
- Save file (auto-formats with Black)
- Or: `Ctrl+Shift+P` → "Format Document"

### Using Makefile

```bash
# Show all available commands
make help

# Common commands
make test              # Run tests
make lint              # Run linting
make format            # Format code
make coverage          # Generate coverage
make validate          # Full validation
make quick-validate    # Quick checks
make security          # Security scan
make clean             # Clean temp files
```

## 🐳 Docker Testing

### Why Docker?
- Isolated environment
- Reproducible tests
- No local dependency conflicts
- Same as CI environment

### Build Test Image
```bash
docker build -f Dockerfile.test -t ha-ai-workflow-test .
# or
make docker-build
```

### Run Tests in Docker
```bash
./tools/run_docker_tests.sh
# or
make docker-test
```

Runs:
1. Unit tests with coverage
2. Linting checks
3. Shell validation

### Docker Compose Services

```bash
# Run specific service
docker-compose -f docker-compose.test.yml run --rm test
docker-compose -f docker-compose.test.yml run --rm lint
docker-compose -f docker-compose.test.yml run --rm shellcheck

# Development shell
docker-compose -f docker-compose.test.yml run --rm dev
# or
make docker-shell
```

### Docker Development
```bash
# Start dev environment
make docker-shell

# Inside container:
pytest -v
black bin/
flake8 bin/
```

## 📚 Agent Instructions

### For AI Coding Agents

Complete instructions for AI agents: [docs/AGENT_INSTRUCTIONS.md](docs/AGENT_INSTRUCTIONS.md)

Key points:
- **Security First**: Never commit secrets
- **Test Everything**: Write tests for all code
- **Follow Conventions**: PEP 8, proper commit messages
- **Validate Before Commit**: Run `make validate`

### For Human Developers

Complete guide: [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)

## 📊 Coverage Reports

### Generate Coverage
```bash
pytest --cov=bin --cov-report=html --cov-report=term
# or
make coverage
```

### View HTML Report
```bash
# Report location: htmlcov/index.html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage in VSCode
1. Install "Coverage Gutters" extension
2. Run: `pytest --cov=bin --cov-report=xml`
3. Click "Watch" in status bar
4. See coverage inline in editor

### Coverage Targets
- **Minimum**: 50% (CI enforced)
- **Target**: 80%
- **Ideal**: 90%+

## 🔒 Security

### Security Scanning

#### Python (Bandit)
```bash
bandit -r bin/ -ll -i
# or
make security
```

#### Secrets Detection
```bash
detect-secrets scan > .secrets.baseline
detect-secrets scan --baseline .secrets.baseline
```

#### Vulnerability Scanning (Trivy)
```bash
trivy fs --severity HIGH,CRITICAL .
```

### Security Best Practices
- Never commit secrets
- Sanitize all sensitive data
- Validate all inputs
- Use secure coding practices
- Run security scans regularly

## 🐛 Debugging

### Python Debugging

#### Using pdb
```python
import pdb; pdb.set_trace()
```

#### Using pytest with pdb
```bash
pytest --pdb
```

#### Using VSCode Debugger
- Set breakpoint (F9)
- Press F5
- Select debug configuration

### Shell Debugging
```bash
# Debug mode
bash -x script.sh

# Check syntax
bash -n script.sh

# Validate with ShellCheck
shellcheck script.sh
```

## 📝 Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Build/tools

**Example**:
```
feat(context-gen): Add device statistics

Added device statistics grouped by manufacturer.
Improves AI context understanding.

Closes #42
```

## 🔧 Troubleshooting

### Tests Failing

```bash
# Clear cache
make clean

# Reinstall dependencies
pip install -r requirements-test.txt --force-reinstall

# Run with verbose output
pytest -vv
```

### Pre-commit Hooks Failing

```bash
# Update hooks
pre-commit autoupdate

# Clean and reinstall
pre-commit clean
pre-commit install

# Run manually
pre-commit run --all-files
```

### Import Errors

```bash
# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/bin"

# Or install in dev mode
pip install -e .
```

## 📖 Additional Resources

### Documentation
- [AGENT_INSTRUCTIONS.md](docs/AGENT_INSTRUCTIONS.md) - For AI agents
- [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) - For developers
- [README.md](README.md) - Project overview

### External Resources
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Rules](https://flake8.pycqa.org/)
- [Bandit Checks](https://bandit.readthedocs.io/)
- [ShellCheck Wiki](https://www.shellcheck.net/wiki/)

## 🎯 Quick Reference

```bash
# Development cycle
make quick-validate  # Fast checks
make test           # Run tests
make lint           # Check linting
make format         # Auto-format
make validate       # Full validation

# Before commit
make validate

# Before PR
make ci

# Docker testing
make docker-test

# View coverage
make coverage
open htmlcov/index.html

# Clean up
make clean
```

## ✨ Summary

This infrastructure provides:

✅ Comprehensive test coverage  
✅ Automated code quality checks  
✅ Security scanning  
✅ Pre-commit validation  
✅ CI/CD pipeline  
✅ Docker-based testing  
✅ VSCode integration  
✅ Agent instructions  
✅ Developer guides  

Everything needed for professional, secure development! 🚀
