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

## SSH Configuration and Troubleshooting

### SSH Connection Setup

The workflow supports SSH for remote Home Assistant access. Proper configuration is critical for reliable operation.

#### Configuration File

Edit `config/workflow_config.yaml`:

```yaml
ssh:
  enabled: true
  host: "192.168.1.100"      # Your HA server IP or hostname
  port: 22                    # SSH port (default: 22)
  user: "root"                # SSH username
  auth_method: "key"          # "key" or "password"
  key_path: "~/.ssh/id_rsa"  # Path to SSH private key
  remote_config_path: "/config"
  
  # Timeout settings (in seconds)
  connection_timeout: 30      # SSH connection timeout
  transfer_timeout: 600       # File transfer timeout (10 minutes)
  
  # Retry configuration
  retry_attempts: 3           # Number of retry attempts
  retry_delay: 2              # Delay between retries
```

#### CLI Overrides

Override timeout values via command line:

```bash
# Custom SSH timeout
./bin/workflow_orchestrator.py export --remote --ssh-timeout 60

# Custom transfer timeout (for large configs)
./bin/workflow_orchestrator.py export --remote --transfer-timeout 1200

# Both timeouts
./bin/workflow_orchestrator.py import --remote --source ./imports/config \
  --ssh-timeout 45 --transfer-timeout 900
```

#### Direct SSH Testing

Test SSH connection directly:

```bash
# Basic test
./bin/ssh_transfer.py --host 192.168.1.100 --test

# With custom timeout
./bin/ssh_transfer.py --host 192.168.1.100 --test --ssh-timeout 60

# With SSH key
./bin/ssh_transfer.py --host 192.168.1.100 --user root \
  --key ~/.ssh/ha_key --test
```

### Timeout Configuration Guide

#### Default Values

| Setting | Default | Description |
|---------|---------|-------------|
| `connection_timeout` | 30s | Time to establish SSH connection |
| `transfer_timeout` | 600s (10min) | Time for file transfer operations |
| `retry_attempts` | 3 | Number of retry attempts for transient failures |
| `retry_delay` | 2s | Delay between retry attempts |

#### Recommended Settings by Scenario

**Local Network (Proxmox VM / Docker on LAN)**
```yaml
connection_timeout: 15   # Fast local network
transfer_timeout: 300    # 5 minutes for typical configs
retry_attempts: 2        # Fewer retries needed
retry_delay: 1           # Short delay
```

**Remote Network (Over Internet/VPN)**
```yaml
connection_timeout: 60   # Slower connection establishment
transfer_timeout: 1200   # 20 minutes for large configs
retry_attempts: 5        # More retries for unstable connections
retry_delay: 5           # Longer delay between retries
```

**Slow/Unreliable Network**
```yaml
connection_timeout: 90
transfer_timeout: 1800   # 30 minutes
retry_attempts: 5
retry_delay: 10
```

**Large Configuration Files (>100MB)**
```yaml
connection_timeout: 30
transfer_timeout: 3600   # 60 minutes
retry_attempts: 3
retry_delay: 5
```

### Common SSH Errors and Solutions

#### Connection Refused
```
Error: Connection refused: SSH service may not be running on 192.168.1.100:22
```

**Solutions:**
1. Verify SSH service is running:
   ```bash
   # On HA host
   systemctl status sshd
   ```
2. Check firewall rules allow port 22
3. Verify correct IP address and port
4. For Home Assistant OS, ensure SSH add-on is installed and started

#### Authentication Failed
```
Error: Authentication failed: Check username, password, or SSH key
```

**Solutions:**
1. Verify SSH key is correct:
   ```bash
   # Test SSH key
   ssh -i ~/.ssh/id_rsa root@192.168.1.100
   ```
2. Check key permissions:
   ```bash
   chmod 600 ~/.ssh/id_rsa
   chmod 700 ~/.ssh
   ```
3. Verify public key is in `~/.ssh/authorized_keys` on remote host
4. Try password authentication if key fails
5. Check username is correct (usually `root` for HA OS)

#### Connection Timeout
```
Error: Connection timeout after 30s. Host may be unreachable.
```

**Solutions:**
1. Verify host is reachable:
   ```bash
   ping 192.168.1.100
   ```
2. Increase timeout for slow networks:
   ```yaml
   connection_timeout: 60
   ```
3. Check network connectivity
4. Verify VPN is active (if accessing remotely)
5. Check if host is behind firewall/NAT

#### Hostname Resolution Failed
```
Error: Cannot resolve hostname: ha.local
```

**Solutions:**
1. Use IP address instead of hostname
2. Add hostname to `/etc/hosts`:
   ```bash
   echo "192.168.1.100 ha.local" | sudo tee -a /etc/hosts
   ```
3. Verify DNS is working:
   ```bash
   nslookup ha.local
   ```
4. Use mDNS (.local domains) if on local network

#### Transfer Timeout
```
Error: Transfer timeout after 600s
```

**Solutions:**
1. Increase transfer timeout:
   ```yaml
   transfer_timeout: 1200  # 20 minutes
   ```
2. Check network bandwidth
3. Reduce configuration size by excluding unnecessary files
4. Use faster connection (LAN vs WiFi)
5. Check for network congestion

#### Permission Denied (File Operations)
```
Error: Permission denied: /config/configuration.yaml
```

**Solutions:**
1. Verify SSH user has read/write permissions:
   ```bash
   # On remote host
   ls -la /config
   ```
2. Use correct user (usually `root` for HA OS)
3. Check SELinux/AppArmor settings
4. Ensure target directory exists and is writable

#### No Route to Host
```
Error: Network unreachable: Cannot reach host 192.168.1.100
```

**Solutions:**
1. Verify host is on same network or routable
2. Check routing table:
   ```bash
   ip route
   ```
3. Verify network interface is up
4. Check VPN connection for remote access
5. Verify firewall allows traffic

### SSH Key Setup

#### Generate SSH Key (if needed)

```bash
# Generate new SSH key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/ha_key -C "HA AI Workflow"

# Set correct permissions
chmod 600 ~/.ssh/ha_key
chmod 644 ~/.ssh/ha_key.pub
```

#### Copy Key to Remote Host

```bash
# Option 1: Using ssh-copy-id
ssh-copy-id -i ~/.ssh/ha_key.pub root@192.168.1.100

# Option 2: Manual copy
cat ~/.ssh/ha_key.pub | ssh root@192.168.1.100 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# Option 3: For Home Assistant OS
# Add public key via SSH add-on configuration UI
```

#### Test SSH Key

```bash
# Test connection
ssh -i ~/.ssh/ha_key root@192.168.1.100 "echo 'SSH key works!'"

# Test with verbose output
ssh -vvv -i ~/.ssh/ha_key root@192.168.1.100
```

### Retry Logic

The SSH module automatically retries transient failures:

- **Retried automatically:** Network timeouts, temporary connection issues
- **Not retried:** Authentication failures, file not found, permission denied
- **Configurable:** Retry attempts and delay between retries

**Monitoring retries:**
```python
import logging
logging.basicConfig(level=logging.INFO)

# Now retries will be logged
```

### Performance Optimization

#### For Local Networks

```yaml
# Optimized for LAN (Proxmox/Docker)
ssh:
  connection_timeout: 10
  transfer_timeout: 300
  retry_attempts: 2
  retry_delay: 1
```

#### Connection Pooling

The module reuses SSH connections where possible to reduce overhead.

#### Large File Transfers

For large configuration exports/imports:
1. Use rsync (automatically preferred when available)
2. Increase `transfer_timeout`
3. Consider compression (rsync uses `-z` by default)
4. Exclude unnecessary files in config

### Debugging SSH Issues

#### Enable Verbose Logging

```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### SSH Command Line Testing

```bash
# Test with verbose output
ssh -vvv root@192.168.1.100

# Test specific command
ssh root@192.168.1.100 "echo 'test' && ls -la /config"

# Test SCP transfer
scp -v /tmp/test.txt root@192.168.1.100:/tmp/

# Test with timeout
timeout 30 ssh root@192.168.1.100 "echo 'test'"
```

#### Network Diagnostics

```bash
# Check connectivity
ping -c 4 192.168.1.100

# Check SSH port
nc -zv 192.168.1.100 22

# Trace route
traceroute 192.168.1.100

# Check DNS
nslookup ha.local
```

### Security Considerations

1. **Use SSH keys** instead of passwords when possible
2. **Restrict SSH key permissions** (600 for private key)
3. **Use non-root user** if possible (requires proper permissions)
4. **Firewall rules:** Only allow SSH from trusted IPs
5. **Change default SSH port** (update `port` in config)
6. **Disable password auth** on remote host after key setup
7. **Regular key rotation:** Generate new keys periodically
8. **Monitor failed attempts:** Check SSH logs for suspicious activity

### Example Workflows

#### Complete Export/Import with SSH

```bash
# 1. Configure SSH
vim config/workflow_config.yaml

# 2. Test connection
./bin/ssh_transfer.py --host 192.168.1.100 --test

# 3. Export from remote
./bin/workflow_orchestrator.py export --remote

# 4. Make modifications
# ... edit files ...

# 5. Import back to remote
./bin/workflow_orchestrator.py import --remote --source ./imports/modified_config
```

#### Handling Large Configurations

```bash
# Export with extended timeout
./bin/workflow_orchestrator.py export --remote --transfer-timeout 1800

# Import with progress
./bin/workflow_orchestrator.py import --remote \
  --source ./imports/large_config \
  --transfer-timeout 1800
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
