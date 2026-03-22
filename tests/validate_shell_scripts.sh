#!/usr/bin/env bash
###############################################################################
# Shell Script Linting and Validation
# Validates bash scripts for syntax and best practices
###############################################################################

set -euo pipefail

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

# Find all bash scripts while handling spaces in paths.
declare -a SCRIPTS=()
while IFS= read -r -d '' script; do
    SCRIPTS+=("$script")
done < <(
    find "${PROJECT_ROOT}" \
        \( -path "*/.git" -o -path "*/.pytest_cache" -o -path "*/__pycache__" -o -path "*/htmlcov" -o -path "*/.venv" -o -path "*/.agents" -o -path "*/.claude" \) -prune \
        -o -type f -name "*.sh" ! -path "*/tests/*" -print0 2>/dev/null
)

TOTAL=0
PASSED=0
FAILED=0
declare -a TEMP_FILES=()

cleanup_temp_files() {
    for file in "${TEMP_FILES[@]}"; do
        rm -f "$file"
    done
}

prepare_script_for_check() {
    local script="$1"
    local tmp_file
    tmp_file="$(mktemp)"
    tr -d '\r' < "$script" > "$tmp_file"
    TEMP_FILES+=("$tmp_file")
    printf '%s' "$tmp_file"
}

trap cleanup_temp_files EXIT

# Test 1: Syntax Check
echo "Test 1: Bash Syntax Check"
echo "------------------------"
for script in "${SCRIPTS[@]}"; do
    normalized_script="$(prepare_script_for_check "$script")"
    TOTAL=$((TOTAL + 1))
    echo -n "Checking $(basename "$script")... "
    if bash -n "$normalized_script" 2>/dev/null; then
        echo -e "${GREEN}[OK]${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}[FAIL]${NC}"
        FAILED=$((FAILED + 1))
        bash -n "$normalized_script" 2>&1 | sed 's/^/  /'
    fi
done
echo ""

# Test 2: ShellCheck (if available)
if command -v shellcheck >/dev/null 2>&1; then
    echo "Test 2: ShellCheck Analysis"
    echo "------------------------"
    for script in "${SCRIPTS[@]}"; do
        normalized_script="$(prepare_script_for_check "$script")"
        TOTAL=$((TOTAL + 1))
        echo -n "Analyzing $(basename "$script")... "
        if shellcheck -x "$normalized_script" 2>/dev/null; then
            echo -e "${GREEN}[OK]${NC}"
            PASSED=$((PASSED + 1))
        else
            echo -e "${YELLOW}[WARN]${NC}"
            # Keep shellcheck non-blocking for now.
            PASSED=$((PASSED + 1))
            shellcheck -x "$normalized_script" 2>&1 | grep -A 5 "^In" | sed 's/^/  /' || true
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
for script in "${SCRIPTS[@]}"; do
    issues=0

    # Check for 'set -e' or strict mode.
    if ! grep -q "set -e" "$script" && ! grep -q "set -euo pipefail" "$script"; then
        echo -e "${YELLOW}[WARN]${NC} $(basename "$script"): No 'set -e' found (error handling)"
        issues=$((issues + 1))
    fi

    # Check for possible unquoted variables (basic heuristic).
    if grep -q '\$[A-Z_]*[^"]' "$script" 2>/dev/null; then
        echo -e "${YELLOW}[WARN]${NC} $(basename "$script"): Possible unquoted variables"
        issues=$((issues + 1))
    fi

    if [ "$issues" -eq 0 ]; then
        echo -e "${GREEN}[OK]${NC} $(basename "$script"): No common issues found"
        PASSED=$((PASSED + 1))
    else
        # Keep this non-blocking and informational.
        PASSED=$((PASSED + 1))
    fi
    TOTAL=$((TOTAL + 1))
done
echo ""

# Test 4: Executable permissions
echo "Test 4: Executable Permissions"
echo "------------------------"
for script in "${SCRIPTS[@]}"; do
    TOTAL=$((TOTAL + 1))
    echo -n "Checking $(basename "$script")... "
    if [ -x "$script" ]; then
        echo -e "${GREEN}[OK]${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${YELLOW}[WARN]${NC} Not executable"
        # Keep this non-blocking because Windows checkouts often lose +x bits.
        PASSED=$((PASSED + 1))
    fi
done
echo ""

# Summary
echo "================================================"
echo "Summary"
echo "================================================"
echo "Total tests: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ "$FAILED" -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
    exit 1
fi

echo "All critical checks passed!"
exit 0
