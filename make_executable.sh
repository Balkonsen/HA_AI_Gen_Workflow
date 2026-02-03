#!/bin/bash
###############################################################################
# Make All Scripts Executable
# Quick utility to ensure all shell scripts have execute permissions
###############################################################################

set -e

echo "Making scripts executable..."

# Main scripts
chmod +x ha_ai_master_script.sh
chmod +x setup.sh

# Tools
chmod +x tools/validate_all.sh
chmod +x tools/quick_validate.sh
chmod +x tools/setup_pre_commit.sh
chmod +x tools/run_docker_tests.sh

# Tests
chmod +x tests/validate_shell_scripts.sh

echo "✓ All scripts are now executable"
echo ""
echo "You can now run:"
echo "  ./ha_ai_master_script.sh"
echo "  ./setup.sh"
echo "  ./tools/validate_all.sh"
echo "  make validate"
