# Quick Command Reference

## 🚀 Essential Commands

### Initial Setup (One-time)
```bash
bash make_executable.sh    # Make scripts executable
make install               # Install dependencies
make pre-commit            # Setup git hooks
make test                  # Verify installation
```

### Daily Development
```bash
make quick-validate        # Fast check (30s)
make test                  # Run tests (1min)
make validate              # Full check (3min)
```

### Code Quality
```bash
make lint                  # Check code quality
make format                # Auto-format code
make security              # Security scan
make coverage              # Coverage report
```

### Testing
```bash
make test                  # All tests
make test-unit             # Unit tests only
make test-integration      # Integration tests
make test-watch            # Watch mode
```

### Docker
```bash
make docker-build          # Build test image
make docker-test           # Run tests in Docker
make docker-shell          # Dev environment
```

### Utilities
```bash
make clean                 # Clean temp files
make help                  # Show all commands
make ci                    # Simulate CI locally
```

## 📋 Validation Levels

### Level 1: Quick (30 seconds)
```bash
make quick-validate
```
Checks: Syntax + Quick tests

### Level 2: Standard (1-2 minutes)
```bash
make test && make lint
```
Checks: Tests + Linting

### Level 3: Full (2-3 minutes)
```bash
make validate
```
Checks: Everything (15 checks)

### Level 4: CI Simulation (5-10 minutes)
```bash
make ci
```
Checks: Same as GitHub Actions

## 🎯 Common Workflows

### Before Starting Work
```bash
git pull origin main
make quick-validate
```

### After Making Changes
```bash
make quick-validate       # Fast feedback
make test                 # Full test run
```

### Before Committing
```bash
make validate            # Comprehensive check
git add .
git commit -m "feat: ..."
# Pre-commit hooks run automatically
```

### Before Creating PR
```bash
git fetch origin
git rebase origin/main
make ci                  # Full CI simulation
git push origin feature/branch
```

### Fixing Issues
```bash
make format              # Fix formatting
make lint                # Check what's wrong
make test                # Verify fixes
```

## 🔧 Direct Commands

### Pytest
```bash
pytest -v                           # All tests
pytest tests/test_file.py -v       # One file
pytest tests/test_file.py::TestClass::test_method -v  # One test
pytest --cov=bin --cov-report=html  # With coverage
pytest -x                           # Stop on first failure
pytest --pdb                        # Debug on failure
```

### Code Quality
```bash
black --check bin/                  # Check formatting
black bin/                          # Auto-format
flake8 bin/                         # Linting
pylint bin/*.py                     # Advanced linting
bandit -r bin/                      # Security scan
```

### Shell
```bash
bash -n script.sh                   # Syntax check
shellcheck script.sh                # Validation
bash -x script.sh                   # Debug mode
```

### Coverage
```bash
pytest --cov=bin --cov-report=html
open htmlcov/index.html            # View report
```

### Pre-commit
```bash
pre-commit run --all-files         # Run all hooks
pre-commit run black               # Run specific hook
pre-commit autoupdate              # Update hooks
```

### Docker
```bash
docker build -f Dockerfile.test -t ha-test .
docker run --rm ha-test
docker-compose -f docker-compose.test.yml run test
```

## 🐛 Troubleshooting Commands

### Clear Caches
```bash
make clean
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
```

### Reinstall Dependencies
```bash
pip install -r requirements-test.txt --force-reinstall
```

### Fix Import Errors
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/bin"
```

### Fix Pre-commit
```bash
pre-commit clean
pre-commit install
pre-commit run --all-files
```

### Fix Docker
```bash
docker system prune -a
make docker-build
```

## 📊 Status Commands

### Check What's Changed
```bash
git status
git diff
git diff --cached
```

### Check Coverage
```bash
pytest --cov=bin --cov-report=term
```

### Check Security
```bash
bandit -r bin/
detect-secrets scan
```

### Check Dependencies
```bash
pip list
pip check
```

## 🎓 Learning Commands

### Show Help
```bash
make help                    # Makefile commands
pytest --help                # Pytest options
black --help                 # Black options
pre-commit --help            # Pre-commit options
```

### Show Configuration
```bash
cat pytest.ini              # Pytest config
cat .pre-commit-config.yaml # Pre-commit config
cat Makefile                # Make targets
```

### Show Test Details
```bash
pytest --collect-only       # List all tests
pytest -v -s                # Verbose with output
pytest -x -vv               # Stop on fail, extra verbose
```

## 💡 Pro Tips

### Watch Mode
```bash
pip install pytest-watch
ptw -- -v                   # Tests run on file change
```

### Fast Feedback Loop
```bash
# Terminal 1: Watch tests
ptw -- -v

# Terminal 2: Make changes
vim bin/module.py

# Tests run automatically!
```

### Parallel Testing
```bash
pip install pytest-xdist
pytest -n auto              # Use all CPU cores
```

### Debug Failing Test
```bash
pytest tests/test_file.py::test_name --pdb -v
```

### Coverage for One File
```bash
pytest tests/test_file.py --cov=bin/module.py --cov-report=term
```

## 🔑 Most Important Commands

```bash
# These are your daily drivers:
make quick-validate     # Fast check
make test              # Run tests
make validate          # Before commit
make format            # Fix formatting
make help              # When stuck
```

## 📖 Documentation References

- Full commands: `make help`
- Testing: [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)
- Development: [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)
- Setup: [GETTING_STARTED.md](GETTING_STARTED.md)

## 🎯 One-Liner Workflows

```bash
# Full validation before commit
make clean && make validate && echo "✓ Ready to commit"

# Quick check during development
make quick-validate && echo "✓ Looking good"

# Complete test with coverage
make clean && make test && make coverage && open htmlcov/index.html

# Fix all auto-fixable issues
make format && make clean && make test

# Prepare for PR
make clean && make ci && echo "✓ Ready for PR"
```

## ⚡ Speed Tips

- Use `make quick-validate` during rapid development
- Use `make test` after major changes
- Use `make validate` before commits
- Use `make ci` before PRs
- Run `make clean` if things act weird

## 🆘 Emergency Commands

```bash
# Nothing works, reset everything
make clean
pip install -r requirements-test.txt --force-reinstall
pre-commit clean && pre-commit install
make test

# Git is confused
git status
git reset --hard origin/main  # CAREFUL: Loses changes!

# Docker is broken
docker system prune -a -f
make docker-build
```

---

**Keep this reference handy! 📌**
