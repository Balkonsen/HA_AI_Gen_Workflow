#!/bin/bash
###############################################################################
# Quick Validation Script
# Fast pre-commit checks for rapid development
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Running quick validation..."
echo ""

# 1. Python syntax check
echo -n "Python syntax... "
if python3 -m py_compile bin/*.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# 2. Shell syntax check
echo -n "Shell syntax... "
if bash -n *.sh 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# 3. Quick tests
echo -n "Quick tests... "
if pytest tests/ -x -q 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Quick validation passed!${NC}"
echo "Run './tools/validate_all.sh' for comprehensive checks."
