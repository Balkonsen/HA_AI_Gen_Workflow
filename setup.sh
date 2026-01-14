#!/bin/bash
###############################################################################
# Home Assistant AI Workflow - Setup Script
# One-time setup for the complete workflow system
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}ℹ${NC} $@"; }
success() { echo -e "${GREEN}✓${NC} $@"; }
warn() { echo -e "${YELLOW}⚠${NC} $@"; }
error() { echo -e "${RED}✗${NC} $@"; }

banner() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  $@"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
}

INSTALL_DIR="/usr/local/ha-ai-workflow"
CONFIG_DIR="/config"

banner "Home Assistant AI Workflow - Setup"

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
info "Step 1/7: Creating directory structure..."
mkdir -p "${INSTALL_DIR}/bin"
mkdir -p "${INSTALL_DIR}/docs"
mkdir -p "${INSTALL_DIR}/templates"
mkdir -p "${CONFIG_DIR}/ai_exports/secrets"
mkdir -p "${CONFIG_DIR}/ai_exports/archives"
mkdir -p "${CONFIG_DIR}/ai_imports/pending"
success "Directories created"

# Step 2: Check dependencies
info "Step 2/7: Checking dependencies..."

missing_deps=()

if ! command -v python3 &> /dev/null; then
    missing_deps+=("python3")
fi

if ! command -v git &> /dev/null; then
    missing_deps+=("git")
fi

if [ ${#missing_deps[@]} -ne 0 ]; then
    error "Missing dependencies: ${missing_deps[*]}"
    echo ""
    echo "Please install them first:"
    echo "  apk add ${missing_deps[*]}"
    exit 1
fi

success "Dependencies OK"

# Step 3: Install PyYAML
info "Step 3/7: Installing PyYAML..."

if python3 -c "import yaml" 2>/dev/null; then
    success "PyYAML already installed"
else
    if python3 -m pip install pyyaml --break-system-packages; then
        success "PyYAML installed"
    else
        error "Failed to install PyYAML"
        echo "Please install manually: python3 -m pip install pyyaml --break-system-packages"
        exit 1
    fi
fi

# Step 4: Download/copy Python scripts
info "Step 4/7: Installing Python scripts..."

# Assuming scripts are in current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

scripts=(
    "ha_diagnostic_export.py"
    "ha_ai_context_gen.py"
    "ha_config_import.py"
    "ha_export_verifier.py"
)

for script in "${scripts[@]}"; do
    if [ -f "${SCRIPT_DIR}/${script}" ]; then
        cp "${SCRIPT_DIR}/${script}" "${INSTALL_DIR}/bin/"
        chmod +x "${INSTALL_DIR}/bin/${script}"
        success "Installed ${script}"
    elif [ -f "${SCRIPT_DIR}/bin/${script}" ]; then
        cp "${SCRIPT_DIR}/bin/${script}" "${INSTALL_DIR}/bin/"
        chmod +x "${INSTALL_DIR}/bin/${script}"
        success "Installed ${script}"
    else
        warn "${script} not found, skipping"
    fi
done

# Step 5: Install master script
info "Step 5/7: Installing master script..."

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

# Step 6: Initialize git repository
info "Step 6/7: Initializing git repository..."

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
info "Step 7/7: Creating documentation..."

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

# Final summary
banner "Setup Complete!"

echo ""
success "Installation successful!"
echo ""
echo "📁 Installation directory: ${INSTALL_DIR}"
echo "📁 Config directory: ${CONFIG_DIR}"
echo "🔧 Command: ha-ai-workflow"
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
echo "💡 Pro tip: Use 'ha-ai-workflow --help' for all options"
echo ""

exit 0
