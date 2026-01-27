# 🚀 Getting Started Checklist

Complete this checklist to set up your development environment and start working with full automated validation.

## ⚙️ Initial Setup (One-time)

### 1. System Requirements
- [ ] Python 3.8 or higher installed
- [ ] Git installed and configured
- [ ] Bash shell available (Linux/Mac) or PowerShell (Windows)
- [ ] pip package manager working

**Verify (Linux/Mac):**
```bash
python3 --version  # Should show 3.8+
git --version
bash --version
pip --version
```

**Verify (Windows):**
```powershell
python --version  # Should show 3.8+
git --version
$PSVersionTable.PSVersion  # Should show 5.1+
pip --version
```

### 2. Clone Repository
- [ ] Repository cloned
- [ ] Navigated to project directory

**Linux/Mac:**
```bash
git clone https://github.com/Balkonsen/HA_AI_Gen_Workflow.git
cd HA_AI_Gen_Workflow
```

**Windows:**
```powershell
git clone https://github.com/Balkonsen/HA_AI_Gen_Workflow.git
cd HA_AI_Gen_Workflow
```

### 3. Install Dependencies

**Option A: Windows Automated Installer (Recommended for Windows)**
- [ ] Run PowerShell as Administrator
- [ ] Execute the installer script
- [ ] Verify installation completed

```powershell
# Right-click PowerShell -> Run as Administrator
.\install_windows.ps1
```

The Windows installer automatically:
- Creates directory structure
- Installs Python packages
- Sets up PATH
- Initializes Git repository
- Creates documentation

**Option B: Manual Installation (Linux/Mac/Windows)**
- [ ] Created virtual environment (optional but recommended)
- [ ] Installed test dependencies
- [ ] Verified installation

```bash
# Optional: Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install
# or: pip install -r requirements-test.txt
```

### 4. Setup Pre-commit Hooks
- [ ] Pre-commit installed
- [ ] Hooks configured
- [ ] Initial run completed

```bash
make pre-commit
# or: ./tools/setup_pre_commit.sh
```

### 5. Verify Installation
- [ ] Quick validation passes
- [ ] Tests run successfully

```bash
make quick-validate
make test
```

## 🔧 Optional Setup

### Docker (Recommended)
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Test image builds successfully

```bash
make docker-build
make docker-test
```

### VSCode (Recommended)
- [ ] VSCode installed
- [ ] Recommended extensions installed
- [ ] Workspace settings loaded

Open VSCode:
1. File → Open Folder → Select HA_AI_Gen_Workflow
2. Bottom right: "Install Recommended Extensions"
3. Reload window

### Additional Tools (Optional)
- [ ] ShellCheck installed (for shell validation)
- [ ] Act installed (for local CI testing)
- [ ] Trivy installed (for security scanning)

```bash
# Ubuntu/Debian
sudo apt install shellcheck

# macOS
brew install shellcheck act trivy
```

## 📝 Daily Development Checklist

### Before Starting Work
- [ ] Pull latest changes
- [ ] Verify environment works

```bash
git pull origin main
make quick-validate
```

### During Development
- [ ] Write code
- [ ] Write tests alongside code
- [ ] Run quick validation frequently

```bash
# After each change
make quick-validate

# Before committing
make test
make lint
```

### Before Committing
- [ ] All tests pass
- [ ] Code formatted
- [ ] No linting errors
- [ ] Full validation passes
- [ ] Documentation updated

```bash
make validate  # Runs everything
```

### Committing Changes
- [ ] Meaningful commit message
- [ ] Follows convention (feat/fix/docs/etc.)
- [ ] Pre-commit hooks pass

```bash
git add .
git commit -m "feat(module): Add feature description"
# Pre-commit hooks run automatically
```

### Before Creating PR
- [ ] Branch up to date with main
- [ ] All validations pass
- [ ] CI pipeline would pass

```bash
git fetch origin
git rebase origin/main
make ci  # Simulate CI locally
```

## 🧪 Testing Checklist

### Unit Tests
- [ ] All existing tests pass
- [ ] New tests written for new code
- [ ] Edge cases covered
- [ ] Error handling tested

```bash
pytest tests/ -v
```

### Coverage
- [ ] Coverage >50% (minimum)
- [ ] New code covered
- [ ] Coverage report reviewed

```bash
make coverage
open htmlcov/index.html
```

### Security
- [ ] No secrets in code
- [ ] Security scan passes
- [ ] Input validation present

```bash
make security
```

## 📋 Pre-Merge Checklist

### Code Quality
- [ ] All tests pass
- [ ] Coverage meets minimum
- [ ] No linting errors
- [ ] Code formatted
- [ ] No security issues

### Documentation
- [ ] README updated (if needed)
- [ ] API docs updated (if needed)
- [ ] CHANGELOG updated
- [ ] Comments added for complex logic

### Git
- [ ] Meaningful commits
- [ ] Branch naming correct
- [ ] No merge conflicts
- [ ] PR description complete

### CI/CD
- [ ] GitHub Actions passing
- [ ] All jobs green
- [ ] No warnings

## 🔍 Troubleshooting Checklist

### Tests Failing
- [ ] Cache cleared (`make clean`)
- [ ] Dependencies reinstalled
- [ ] PYTHONPATH set correctly
- [ ] Ran with verbose output (`pytest -vv`)

### Linting Errors
- [ ] Code formatted (`make format`)
- [ ] Imports organized
- [ ] No unused imports
- [ ] Line length <120 chars

### Pre-commit Failing
- [ ] Hooks updated (`pre-commit autoupdate`)
- [ ] Hooks reinstalled
- [ ] Specific hook identified
- [ ] Issue fixed

### Docker Issues
- [ ] Docker daemon running
- [ ] Image rebuilt (`make docker-build`)
- [ ] Containers cleaned (`docker system prune`)
- [ ] Volumes reset

## 📚 Learning Checklist

### Documentation Read
- [ ] README.md
- [ ] SETUP_COMPLETE.md
- [ ] docs/DEVELOPER_GUIDE.md
- [ ] docs/TESTING_GUIDE.md
- [ ] docs/AGENT_INSTRUCTIONS.md (if AI agent)

### Commands Learned
- [ ] `make help` - See all commands
- [ ] `make test` - Run tests
- [ ] `make validate` - Full validation
- [ ] `make quick-validate` - Fast checks
- [ ] `make lint` - Linting
- [ ] `make format` - Auto-format
- [ ] `make coverage` - Coverage report
- [ ] `make clean` - Cleanup

### Workflows Understood
- [ ] Development workflow
- [ ] Testing workflow
- [ ] Commit workflow
- [ ] PR workflow
- [ ] CI/CD pipeline

## ✅ All Set!

When all initial setup items are checked:

```bash
# Verify everything works
make validate

# Start developing!
git checkout -b feature/my-awesome-feature
```

## 🎯 Quick Reference Card

### Most Used Commands
```bash
# Daily workflow
make quick-validate    # Quick check (30s)
make test             # Run tests (1min)
make validate         # Full check (3min)

# Before commit
make lint             # Check style
make format           # Fix formatting
make security         # Security scan

# Utilities
make help             # Show all commands
make clean            # Clean temp files
make coverage         # Coverage report
```

### Common Issues

**Import errors:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/bin"
```

**Tests fail:**
```bash
make clean
pip install -r requirements-test.txt --force-reinstall
```

**Pre-commit issues:**
```bash
pre-commit clean
pre-commit install
```

## 🆘 Need Help?

1. Check [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)
2. Review [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)
3. Search GitHub issues
4. Create new issue with details

## 🎉 Success!

You're now ready to develop with:
- ✅ Automated testing
- ✅ Continuous validation
- ✅ Security scanning
- ✅ Code quality checks
- ✅ Professional workflow

Happy coding! 🚀
