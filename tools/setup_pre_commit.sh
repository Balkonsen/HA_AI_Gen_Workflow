#!/bin/bash
###############################################################################
# Pre-commit Setup Script
# Installs and configures pre-commit hooks
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Pre-commit Hook Setup${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo -e "${YELLOW}Pre-commit not found. Installing...${NC}"
    pip install pre-commit
fi

# Install the git hook scripts
echo -e "${BLUE}Installing pre-commit hooks...${NC}"
pre-commit install

# Install commit-msg hook for conventional commits
echo -e "${BLUE}Installing commit-msg hooks...${NC}"
pre-commit install --hook-type commit-msg

# Run against all files initially
echo -e "${BLUE}Running pre-commit against all files...${NC}"
pre-commit run --all-files || echo -e "${YELLOW}Some checks failed. Please review and fix.${NC}"

echo ""
echo -e "${GREEN}✓ Pre-commit hooks installed successfully!${NC}"
echo ""
echo "Hooks will now run automatically on:"
echo "  - git commit (pre-commit)"
echo "  - git push (pre-push) [if configured]"
echo ""
echo "To run manually:"
echo "  pre-commit run --all-files"
echo ""
echo "To skip hooks (not recommended):"
echo "  git commit --no-verify"
