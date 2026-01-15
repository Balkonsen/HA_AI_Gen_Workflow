#!/bin/bash
###############################################################################
# Shell Script Linting and Validation
# Validates bash scripts for syntax and best practices
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "================================================"
echo "Shell Script Validation"
echo "================================================"
echo ""

# Find all bash scripts
SCRIPTS=$(find "${PROJECT_ROOT}" -type f -name "*.sh" ! -path "*/.*" ! -path "*/tests/*")

TOTAL=0
PASSED=0
FAILED=0

# Test 1: Syntax Check
echo "Test 1: Bash Syntax Check"
echo "------------------------"
for script in $SCRIPTS; do
    TOTAL=$((TOTAL + 1))
    echo -n "Checking $(basename $script)... "
    if bash -n "$script" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC}"
        FAILED=$((FAILED + 1))
        bash -n "$script" 2>&1 | sed 's/^/  /'
    fi
done
echo ""

# Test 2: ShellCheck (if available)
if command -v shellcheck &> /dev/null; then
    echo "Test 2: ShellCheck Analysis"
    echo "------------------------"
    for script in $SCRIPTS; do
        TOTAL=$((TOTAL + 1))
        echo -n "Analyzing $(basename $script)... "
        if shellcheck -x "$script" 2>/dev/null; then
            echo -e "${GREEN}✓${NC}"
            PASSED=$((PASSED + 1))
        else
            echo -e "${YELLOW}⚠${NC}"
            # Don't count shellcheck warnings as failures
            PASSED=$((PASSED + 1))
            shellcheck -x "$script" 2>&1 | grep -A 5 "^In" | sed 's/^/  /' || true
        fi
    done
    echo ""
else
    echo -e "${YELLOW}ShellCheck not installed, skipping...${NC}"
    echo ""
fi

# Test 3: Check for common issues
echo "Test 3: Common Issues Check"
echo "------------------------"
for script in $SCRIPTS; do
    ISSUES=0
    
    # Check for 'set -e' or error handling
    if ! grep -q "set -e" "$script" && ! grep -q "set -euo pipefail" "$script"; then
        echo -e "${YELLOW}⚠${NC} $(basename $script): No 'set -e' found (error handling)"
        ISSUES=$((ISSUES + 1))
    fi
    
    # Check for unquoted variables (basic check)
    if grep -q '\$[A-Z_]*[^"]' "$script" 2>/dev/null; then
        echo -e "${YELLOW}⚠${NC} $(basename $script): Possible unquoted variables"
        ISSUES=$((ISSUES + 1))
    fi
    
    if [ $ISSUES -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $(basename $script): No common issues found"
        PASSED=$((PASSED + 1))
    else
        # Don't fail on warnings
        PASSED=$((PASSED + 1))
    fi
    TOTAL=$((TOTAL + 1))
done
echo ""

# Test 4: Executable permissions
echo "Test 4: Executable Permissions"
echo "------------------------"
for script in $SCRIPTS; do
    TOTAL=$((TOTAL + 1))
    echo -n "Checking $(basename $script)... "
    if [ -x "$script" ]; then
        echo -e "${GREEN}✓${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${YELLOW}⚠${NC} Not executable"
        PASSED=$((PASSED + 1))  # Don't fail on this
    fi
done
echo ""

# Summary
echo "================================================"
echo "Summary"
echo "================================================"
echo "Total tests: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
    exit 1
else
    echo "All critical checks passed!"
    exit 0
fi
