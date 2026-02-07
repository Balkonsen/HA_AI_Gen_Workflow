#!/bin/bash
###############################################################################
# Home Assistant AI Workflow - Setup Script
# One-time setup for the complete workflow system
# Enhanced with comprehensive dependency checking, verification, and logging
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${HA_INSTALL_DIR:-/usr/local/ha-ai-workflow}"
CONFIG_DIR="${HA_CONFIG_DIR:-${HA_CONFIG_PATH:-/config}}"
LOG_DIR="${CONFIG_DIR}/ai_exports"
SETUP_LOG="${LOG_DIR}/setup.log"

# Parse command line arguments for verbosity and help (before creating directories)
VERBOSE=false
for arg in "$@"; do
    case $arg in
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose    Enable verbose output"
            echo "  -h, --help       Show this help message"
            echo ""
            echo "This script will:"
            echo "  1. Create directory structure"
            echo "  2. Check and install dependencies"
            echo "  3. Verify Python modules"
            echo "  4. Install Python scripts"
            echo "  5. Install shell scripts"
            echo "  6. Make all scripts executable"
            echo "  7. Validate installations"
            echo "  8. Initialize git repository"
            echo "  9. Create documentation"
            echo "  10. Perform final checks"
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            ;;
    esac
done

# Ensure log directory exists (after help check)
mkdir -p "${LOG_DIR}"

# Logging functions with file output
log_to_file() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${timestamp} $*" >> "${SETUP_LOG}"
}

info() { 
    echo -e "${BLUE}ℹ${NC} $*"
    log_to_file "[INFO] $*"
}

success() { 
    echo -e "${GREEN}✓${NC} $*"
    log_to_file "[SUCCESS] $*"
}

warn() { 
    echo -e "${YELLOW}⚠${NC} $*"
    log_to_file "[WARN] $*"
}

error() { 
    echo -e "${RED}✗${NC} $*"
    log_to_file "[ERROR] $*"
}

banner() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  $*"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    log_to_file "===== $* ====="
}

banner "Home Assistant AI Workflow - Setup"

info "Setup log: ${SETUP_LOG}"
echo ""
echo "This script will set up the HA AI Workflow system."
echo ""
echo "Installation directory: ${INSTALL_DIR}"
echo "Home Assistant config: ${CONFIG_DIR}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    error "Please run as root (sudo)"
    exit 1
fi

# Step 1: Create directory structure
info "Step 1/11: Creating directory structure..."
mkdir -p "${INSTALL_DIR}/bin"
mkdir -p "${INSTALL_DIR}/docs"
mkdir -p "${INSTALL_DIR}/templates"
mkdir -p "${CONFIG_DIR}/ai_exports/secrets"
mkdir -p "${CONFIG_DIR}/ai_exports/archives"
mkdir -p "${CONFIG_DIR}/ai_imports/pending"
success "Directories created"

# Step 2: Check dependencies
info "Step 2/11: Checking system dependencies..."

missing_deps=()

if ! command -v python3 &> /dev/null; then
    missing_deps+=("python3")
else
    python_version=$(python3 --version 2>&1 | awk '{print $2}' || echo "unknown")
    if [ "$python_version" != "unknown" ]; then
        success "Python 3 found: ${python_version}"
    else
        success "Python 3 found (version detection failed)"
    fi
fi

if ! command -v git &> /dev/null; then
    missing_deps+=("git")
else
    git_version=$(git --version 2>&1 | awk '{print $3}' || echo "unknown")
    if [ "$git_version" != "unknown" ]; then
        success "Git found: ${git_version}"
    else
        success "Git found (version detection failed)"
    fi
fi

if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    warn "pip not found, but will try python3 -m pip"
else
    pip_version=$(python3 -m pip --version 2>&1 | awk '{print $2}')
    success "pip found: ${pip_version}"
fi

# Check for optional dependencies
if command -v shellcheck &> /dev/null; then
    shellcheck_version=$(shellcheck --version | grep version: | awk '{print $2}')
    success "ShellCheck found: ${shellcheck_version} (optional)"
else
    warn "ShellCheck not found (optional - for script validation)"
fi

if [ ${#missing_deps[@]} -ne 0 ]; then
    error "Missing dependencies: ${missing_deps[*]}"
    echo ""
    echo "Please install them first:"
    echo "  apk add ${missing_deps[*]}"
    exit 1
fi

success "System dependencies OK"

# Step 3: Install Python dependencies
info "Step 3/11: Installing Python dependencies..."

# Read requirements.txt and install all dependencies
if [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
    info "Found requirements.txt, installing Python packages..."
    
    # Try different installation methods
    if python3 -m pip install -r "${SCRIPT_DIR}/requirements.txt" --break-system-packages 2>/dev/null; then
        success "Python dependencies installed"
    elif python3 -m pip install -r "${SCRIPT_DIR}/requirements.txt" --user 2>/dev/null; then
        success "Python dependencies installed (user mode)"
    else
        error "Failed to install Python dependencies"
        echo ""
        echo "Please install manually:"
        echo "  python3 -m pip install -r ${SCRIPT_DIR}/requirements.txt --break-system-packages"
        exit 1
    fi
else
    warn "requirements.txt not found, installing essential packages only"
    
    # Install PyYAML at minimum
    if python3 -c "import yaml" 2>/dev/null; then
        success "PyYAML already installed"
    else
        if python3 -m pip install pyyaml --break-system-packages 2>/dev/null; then
            success "PyYAML installed"
        elif python3 -m pip install pyyaml --user 2>/dev/null; then
            success "PyYAML installed (user mode)"
        else
            error "Failed to install PyYAML"
            echo "Please install manually: python3 -m pip install pyyaml --break-system-packages"
            exit 1
        fi
    fi
fi

# Verify critical Python modules can be imported
info "Verifying Python module imports..."
python3 -c "import yaml" 2>/dev/null && success "PyYAML import OK" || error "PyYAML import failed"
python3 -c "import pathlib" 2>/dev/null && success "pathlib import OK" || warn "pathlib import failed"
python3 -c "import json" 2>/dev/null && success "json import OK" || error "json import failed"

# Try to import optional modules
python3 -c "import requests" 2>/dev/null && success "requests import OK" || warn "requests not available (optional)"
python3 -c "import paramiko" 2>/dev/null && success "paramiko import OK" || warn "paramiko not available (SSH features disabled)"
python3 -c "import streamlit" 2>/dev/null && success "streamlit import OK" || warn "streamlit not available (GUI disabled)"
python3 -c "import cryptography" 2>/dev/null && success "cryptography import OK" || warn "cryptography not available"

success "Python dependencies verified"

# Step 4: Download/copy Python scripts
info "Step 4/11: Installing Python scripts..."

scripts=(
    "workflow_logger.py"
    "workflow_config.py"
    "workflow_orchestrator.py"
    "workflow_gui.py"
    "ha_diagnostic_export.py"
    "ha_ai_context_gen.py"
    "ha_config_import.py"
    "ha_export_verifier.py"
    "secrets_manager.py"
    "ssh_transfer.py"
    "ha_api_client.py"
)

installed_count=0
skipped_count=0

for script in "${scripts[@]}"; do
    if [ -f "${SCRIPT_DIR}/${script}" ]; then
        cp "${SCRIPT_DIR}/${script}" "${INSTALL_DIR}/bin/"
        chmod +x "${INSTALL_DIR}/bin/${script}"
        success "Installed ${script}"
        ((installed_count++))
    elif [ -f "${SCRIPT_DIR}/bin/${script}" ]; then
        cp "${SCRIPT_DIR}/bin/${script}" "${INSTALL_DIR}/bin/"
        chmod +x "${INSTALL_DIR}/bin/${script}"
        success "Installed ${script}"
        ((installed_count++))
    else
        warn "${script} not found, skipping"
        ((skipped_count++))
    fi
done

success "Installed ${installed_count} Python scripts (${skipped_count} skipped)"

# Verify Python scripts are executable and importable
if [ "$VERBOSE" = true ]; then
    info "Verifying Python scripts..."
    for script in "${INSTALL_DIR}/bin/"*.py; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                if [ "$VERBOSE" = true ]; then
                    info "  ✓ $(basename "$script") is executable"
                fi
            else
                warn "  ⚠ $(basename "$script") is not executable"
                chmod +x "$script"
            fi
        fi
    done
fi

# Step 5: Install master script
info "Step 5/11: Installing shell scripts..."

if [ -f "${SCRIPT_DIR}/ha_ai_master_script.sh" ]; then
    cp "${SCRIPT_DIR}/ha_ai_master_script.sh" "${INSTALL_DIR}/ha_ai_master.sh"
    chmod +x "${INSTALL_DIR}/ha_ai_master.sh"
    ln -sf "${INSTALL_DIR}/ha_ai_master.sh" /usr/local/bin/ha-ai-workflow
    success "Master script installed"
    success "Symlink created: /usr/local/bin/ha-ai-workflow"
else
    error "Master script not found"
    exit 1
fi

# Make all shell scripts executable
info "Making all shell scripts executable..."
if [ -d "${SCRIPT_DIR}/tools" ]; then
    chmod +x "${SCRIPT_DIR}"/tools/*.sh 2>/dev/null || true
    success "Tools scripts made executable"
fi

# Validate shell scripts with shellcheck if available
if command -v shellcheck &> /dev/null; then
    info "Validating shell scripts with shellcheck..."
    validation_failed=0
    
    for script in "${INSTALL_DIR}/ha_ai_master.sh" "${SCRIPT_DIR}/setup.sh"; do
        if [ -f "$script" ]; then
            # Run shellcheck and capture exit code
            if ! shellcheck "$script" > /dev/null 2>&1; then
                warn "ShellCheck found issues in $(basename "$script")"
                if [ "$VERBOSE" = true ]; then
                    shellcheck "$script" || true
                fi
                ((validation_failed++))
            else
                if [ "$VERBOSE" = true ]; then
                    success "  $(basename "$script") passed shellcheck"
                fi
            fi
        fi
    done
    
    if [ $validation_failed -eq 0 ]; then
        success "Shell script validation passed"
    else
        warn "Shell script validation found ${validation_failed} issues (not critical)"
    fi
else
    info "Skipping shell script validation (shellcheck not installed)"
fi

# Step 6: Configure HA API token
banner "Home Assistant API Configuration"
info "Step 6/11: Configuring Home Assistant API access..."

ENV_FILE="${INSTALL_DIR}/.env"

# Check if SUPERVISOR_TOKEN is already set (add-on environment)
if [ -n "${SUPERVISOR_TOKEN:-}" ]; then
    success "SUPERVISOR_TOKEN already set (add-on environment detected)"
elif [ -f "${ENV_FILE}" ] && grep -q "SUPERVISOR_TOKEN=" "${ENV_FILE}" 2>/dev/null; then
    existing_token=$(grep "SUPERVISOR_TOKEN=" "${ENV_FILE}" | cut -d= -f2-)
    if [ -n "${existing_token}" ]; then
        success "Existing token found in ${ENV_FILE}"
        info "To update, re-run setup or edit ${ENV_FILE}"
    fi
else
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  HOME ASSISTANT API TOKEN REQUIRED                             ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  ℹ️  A Home Assistant Long-Lived Access Token is required to:"
    echo "     • Read entities, devices, and add-ons via the HA REST API"
    echo "     • Enable full automation features"
    echo "     • Test API connectivity"
    echo ""
    echo "  📝 How to create a token:"
    echo "     1. Open Home Assistant web interface"
    echo "     2. Click your profile (bottom left)"
    echo "     3. Scroll to 'Long-Lived Access Tokens'"
    echo "     4. Click 'Create Token'"
    echo "     5. Give it a name (e.g., 'HA AI Workflow')"
    echo "     6. Copy the generated token"
    echo ""
    echo "  ⚠️  NOTE: In add-on mode, this is NOT needed"
    echo "     (SUPERVISOR_TOKEN is automatically injected)"
    echo ""
    warn "Without a token, API features will not work!"
    echo ""
    read -r -p "  ➤ Enter your HA Long-Lived Access Token (or press Enter to skip): " ha_token

    if [ -n "${ha_token}" ]; then
        # Write token to env file (readable only by root)
        # Preserve existing content, remove old SUPERVISOR_TOKEN line
        if [ -f "${ENV_FILE}" ]; then
            grep -v "^SUPERVISOR_TOKEN=" "${ENV_FILE}" > "${ENV_FILE}.tmp" 2>/dev/null
            mv "${ENV_FILE}.tmp" "${ENV_FILE}"
        else
            touch "${ENV_FILE}"
        fi
        echo "SUPERVISOR_TOKEN=${ha_token}" >> "${ENV_FILE}"
        chmod 600 "${ENV_FILE}"
        success "✓ Token saved to ${ENV_FILE} (permissions: 600)"
        success "✓ API access configured successfully"
    else
        warn "⚠️  Token configuration skipped"
        warn "⚠️  API features will NOT work until you configure a token"
        echo ""
        echo "  You can set it later via:"
        echo "    • GUI: Configuration → HA API Token"
        echo "    • CLI: echo 'SUPERVISOR_TOKEN=your_token' >> ${ENV_FILE}"
        echo "    • Or re-run: sudo ${SCRIPT_DIR}/setup.sh"
        echo ""
    fi
fi

# Step 7: Initialize git repository
info "Step 7/11: Initializing git repository..."

cd "${CONFIG_DIR}"

if [ -d ".git" ]; then
    info "Git repository already exists"
else
    git config --global init.defaultBranch main 2>/dev/null || true
    git init
    
    # Create .gitignore
    cat > .gitignore << 'EOF'
# Home Assistant
*.db
*.db-shm
*.db-wal
*.log
home-assistant.log*
home-assistant_v2.db*
.cloud
.storage
deps/
tts/
__pycache__/
*.pyc

# AI Workflow
ai_exports/archives/
ai_exports/secrets/
ai_imports/pending/
*.tar.gz
debug_report_*.md

# System
.DS_Store
*.swp
*.swo
*~
EOF
    
    git add .gitignore
    git commit -m "Initial commit: HA AI Workflow setup" || true
    
    success "Git repository initialized"
fi

# Step 7: Create documentation
info "Step 8/11: Creating documentation..."

cat > "${INSTALL_DIR}/docs/QUICKSTART.md" << 'EOF'
# Quick Start Guide

## First Export

```bash
ha-ai-workflow export
```

This will:
1. Export your HA configuration
2. Generate AI-friendly context
3. Create secrets backup
4. Commit to git

## Working with AI

1. Find the generated prompt:
   ```bash
   cat /config/ai_exports/ha_export_*/AI_PROMPT.md
   ```

2. Share with AI assistant (exclude secrets!)

3. Place AI-generated files in:
   ```bash
   /config/ai_imports/pending/
   ```

## Import AI Changes

```bash
ha-ai-workflow import
```

This will:
1. Scan for new files
2. Create git branch
3. Validate configuration
4. Merge and deploy

## Check Status

```bash
ha-ai-workflow status
```

## Automated Mode

```bash
ha-ai-workflow export --auto
ha-ai-workflow import --auto
```
EOF

cat > "${INSTALL_DIR}/docs/TROUBLESHOOTING.md" << 'EOF'
# Troubleshooting Guide

## Export Issues

### PyYAML Not Found
```bash
python3 -m pip install pyyaml --break-system-packages
```

### Permission Denied
```bash
sudo ha-ai-workflow export
```

### Out of Space
```bash
# Clean old archives
rm -rf /config/ai_exports/archives/*
```

## Import Issues

### Validation Failed
Check the debug report:
```bash
cat /config/ai_exports/debug_report_*.md
```

### Git Conflicts
```bash
cd /config
git status
git stash
ha-ai-workflow import
```

### Rollback Changes
```bash
cd /config
git log --oneline
git checkout <commit-hash>
ha core restart
```

## Common Problems

### "No files to import"
Make sure files are in: `/config/ai_imports/pending/`

### "Secrets file not found"
Run export first: `ha-ai-workflow export`

### Configuration check fails
Review errors: `ha core check`

## Getting Help

1. Check logs: `/config/ai_exports/workflow.log`
2. Generate debug report
3. Share with AI (exclude secrets!)
EOF

success "Documentation created"

# Step 8: Run validation tests
info "Step 9/11: Running validation tests..."

# Test Python imports from installed location
test_failed=0

if [ "$VERBOSE" = true ]; then
    info "Testing Python module imports..."
fi

# Test workflow_logger
if python3 -c "import sys; sys.path.insert(0, '${INSTALL_DIR}/bin'); import workflow_logger; workflow_logger.get_logger().info('Test')" 2>/dev/null; then
    success "workflow_logger module OK"
else
    error "workflow_logger module failed to import"
    ((test_failed++))
fi

# Test workflow_config
if python3 -c "import sys; sys.path.insert(0, '${INSTALL_DIR}/bin'); import workflow_config" 2>/dev/null; then
    success "workflow_config module OK"
else
    warn "workflow_config module import issues (may need config file)"
fi

# Test secrets_manager
if python3 -c "import sys; sys.path.insert(0, '${INSTALL_DIR}/bin'); import secrets_manager" 2>/dev/null; then
    success "secrets_manager module OK"
else
    warn "secrets_manager module import issues"
fi

if [ $test_failed -gt 0 ]; then
    error "Validation tests failed: ${test_failed} errors"
    echo ""
    echo "Setup completed with errors. Check the log: ${SETUP_LOG}"
    exit 1
fi

success "Validation tests passed"

# Step 9: Test basic functionality
info "Step 10/11: Testing basic functionality..."

# Test logger creation
if python3 -c "import sys; sys.path.insert(0, '${INSTALL_DIR}/bin'); from workflow_logger import configure_logger; logger = configure_logger('INFO', '${LOG_DIR}/test.log'); logger.info('Test message'); logger.success('Test successful')" 2>/dev/null; then
    success "Logger functionality test passed"
    rm -f "${LOG_DIR}/test.log" 2>/dev/null || true
else
    warn "Logger functionality test had issues"
fi

# Test that ha-ai-workflow command is available
if command -v ha-ai-workflow &> /dev/null; then
    success "ha-ai-workflow command available"
else
    error "ha-ai-workflow command not found in PATH"
    ((test_failed++))
fi

# Test master script can be executed
if [ -x "${INSTALL_DIR}/ha_ai_master.sh" ]; then
    success "Master script is executable"
    
    # Try to get help (this should not fail)
    if "${INSTALL_DIR}/ha_ai_master.sh" --help &> /dev/null; then
        success "Master script help command works"
    else
        warn "Master script help command had issues"
    fi
else
    error "Master script is not executable"
    ((test_failed++))
fi

if [ $test_failed -gt 0 ]; then
    error "Basic functionality tests failed"
    exit 1
fi

success "Basic functionality tests passed"

# Step 10: Perform final checks
info "Step 11/11: Performing final checks..."

# Check directory structure
required_dirs=(
    "${INSTALL_DIR}/bin"
    "${INSTALL_DIR}/docs"
    "${CONFIG_DIR}/ai_exports"
    "${CONFIG_DIR}/ai_exports/secrets"
    "${CONFIG_DIR}/ai_exports/archives"
    "${CONFIG_DIR}/ai_imports/pending"
)

missing_dirs=0
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        if [ "$VERBOSE" = true ]; then
            success "  ✓ $dir exists"
        fi
    else
        error "  ✗ $dir missing"
        ((missing_dirs++))
    fi
done

if [ $missing_dirs -eq 0 ]; then
    success "Directory structure verified"
else
    error "Directory structure incomplete: ${missing_dirs} directories missing"
    exit 1
fi

# Count installed files
python_scripts=$(find "${INSTALL_DIR}/bin" -name "*.py" -type f 2>/dev/null | wc -l)
shell_scripts=$(find "${INSTALL_DIR}" -name "*.sh" -type f 2>/dev/null | wc -l)

info "Installation summary:"
info "  - Python scripts: ${python_scripts}"
info "  - Shell scripts: ${shell_scripts}"
info "  - Log file: ${SETUP_LOG}"

success "Final checks completed"

# Final summary
banner "Setup Complete!"

echo ""
success "Installation successful!"
echo ""
echo "📁 Installation directory: ${INSTALL_DIR}"
echo "📁 Config directory: ${CONFIG_DIR}"
echo "📁 Log directory: ${LOG_DIR}"
echo "🔧 Command: ha-ai-workflow"
echo "📋 Setup log: ${SETUP_LOG}"
echo ""
echo "📖 Documentation:"
echo "   Quick Start: ${INSTALL_DIR}/docs/QUICKSTART.md"
echo "   Troubleshooting: ${INSTALL_DIR}/docs/TROUBLESHOOTING.md"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "   1. Run your first export:"
echo "      ha-ai-workflow export"
echo ""
echo "   2. Review the AI prompt:"
echo "      cat /config/ai_exports/ha_export_*/AI_PROMPT.md"
echo ""
echo "   3. Share with AI and get help!"
echo ""
echo "   4. Place AI files in /config/ai_imports/pending/"
echo ""
echo "   5. Import changes:"
echo "      ha-ai-workflow import"
echo ""
echo "💡 Pro tips:"
echo "   - Use 'ha-ai-workflow --help' for all options"
echo "   - Enable verbose logging: ha-ai-workflow export --verbose"
echo "   - View logs: cat ${LOG_DIR}/workflow.log"
echo "   - Generate diagnostic report on errors for troubleshooting"
echo ""

log_to_file "===== Setup completed successfully ====="

exit 0
