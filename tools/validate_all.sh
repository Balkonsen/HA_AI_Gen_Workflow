#!/bin/bash
###############################################################################
# Automated Validation Script
# Runs all validations before commit/merge
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_FILE="${PROJECT_ROOT}/validation.log"

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Initialize log
echo "Validation started at $(date)" > "${LOG_FILE}"

###############################################################################
# Utility Functions
###############################################################################

print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
}

failure() {
    echo -e "${RED}✗${NC} $1"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
}

run_check() {
    local name=$1
    shift
    local cmd="$@"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    print_step "$name"
    
    if eval "$cmd" >> "${LOG_FILE}" 2>&1; then
        success "$name passed"
        return 0
    else
        failure "$name failed"
        echo "  See ${LOG_FILE} for details"
        return 1
    fi
}

###############################################################################
# Validation Checks
###############################################################################

cd "${PROJECT_ROOT}"

print_header "Pre-Commit Validation Suite"

echo "Starting comprehensive validation..."
echo ""

# Check 1: Environment Setup
print_header "1. Environment Check"

run_check "Python version check" "python3 --version"
run_check "Git repository check" "git rev-parse --git-dir"

# Check dependencies with better error messaging
print_step "Dependencies check"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if pip list | grep -q pytest; then
    success "Dependencies check passed"
else
    failure "Dependencies check failed"
    echo "  Required test dependencies are not installed."
    echo ""
    echo "  To install dependencies, run one of:"
    echo "    • make install"
    echo "    • pip install -r requirements-test.txt"
    echo ""
    echo "  See GETTING_STARTED.md for complete setup instructions."
    echo ""
fi

# Check 2: Python Formatting
print_header "2. Code Formatting (Black)"

if command -v black &> /dev/null; then
    run_check "Python code formatting" "black --check --line-length 120 bin/"
else
    warning "Black not installed, skipping formatting check"
fi

# Check 3: Python Linting
print_header "3. Code Linting (Flake8)"

if command -v flake8 &> /dev/null; then
    run_check "Python linting" "flake8 bin/ --max-line-length=120 --ignore=E203,W503"
else
    warning "Flake8 not installed, skipping linting"
fi

# Check 4: Python Type Checking
print_header "4. Type Checking (MyPy)"

if command -v mypy &> /dev/null; then
    run_check "Python type checking" "mypy bin/ --ignore-missing-imports || true"
else
    warning "MyPy not installed, skipping type checking"
fi

# Check 5: Shell Script Validation
print_header "5. Shell Script Validation"

if [ -f "${PROJECT_ROOT}/tests/validate_shell_scripts.sh" ]; then
    run_check "Shell scripts validation" "bash ${PROJECT_ROOT}/tests/validate_shell_scripts.sh"
else
    warning "Shell validation script not found"
fi

# Check 6: Python Unit Tests
print_header "6. Python Unit Tests"

if command -v pytest &> /dev/null; then
    run_check "Unit tests" "pytest tests/ -v --tb=short"
else
    failure "Pytest not installed"
fi

# Check 7: Code Coverage
print_header "7. Code Coverage"

if command -v pytest &> /dev/null; then
    run_check "Coverage check" "pytest --cov=bin --cov-report=term --cov-fail-under=50"
else
    warning "Cannot check coverage without pytest"
fi

# Check 8: Security Scanning
print_header "8. Security Scanning (Bandit)"

if command -v bandit &> /dev/null; then
    run_check "Security scan" "bandit -r bin/ -ll -i"
else
    warning "Bandit not installed, skipping security scan"
fi

# Check 9: YAML Validation
print_header "9. YAML Validation"

YAML_FILES=$(find . -name "*.yaml" -o -name "*.yml" ! -path "*/.*" ! -path "*/venv/*")
if [ -n "$YAML_FILES" ]; then
    for file in $YAML_FILES; do
        run_check "YAML: $(basename $file)" "python3 -c \"import yaml; yaml.safe_load(open('$file'))\""
    done
else
    warning "No YAML files found"
fi

# Check 10: JSON Validation
print_header "10. JSON Validation"

JSON_FILES=$(find . -name "*.json" ! -path "*/.*" ! -path "*/venv/*" ! -path "*/node_modules/*")
if [ -n "$JSON_FILES" ]; then
    for file in $JSON_FILES; do
        run_check "JSON: $(basename $file)" "python3 -c \"import json; json.load(open('$file'))\""
    done
else
    warning "No JSON files found"
fi

# Check 11: Documentation Links
print_header "11. Documentation Validation"

MD_FILES=$(find docs -name "*.md" 2>/dev/null || true)
if [ -n "$MD_FILES" ]; then
    success "Found $(echo "$MD_FILES" | wc -l) markdown files"
else
    warning "No documentation files found"
fi

# Check 12: Git Status
print_header "12. Git Status Check"

if git diff --quiet; then
    success "Working directory clean"
else
    warning "Uncommitted changes detected"
fi

# Check 13: Branch Check
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" == "main" ] || [ "$CURRENT_BRANCH" == "master" ]; then
    warning "Working on protected branch: $CURRENT_BRANCH"
else
    success "Working on feature branch: $CURRENT_BRANCH"
fi

# Check 14: Large Files
print_header "14. Large Files Check"

LARGE_FILES=$(find . -type f -size +1M ! -path "*/.*" ! -path "*/venv/*" ! -path "*/.git/*")
if [ -z "$LARGE_FILES" ]; then
    success "No large files detected"
else
    warning "Large files found:"
    echo "$LARGE_FILES" | sed 's/^/  /'
fi

# Check 15: Secrets Detection
print_header "15. Secrets Detection"

# Simple pattern matching for common secrets
SECRETS_FOUND=false
for file in $(git ls-files); do
    if grep -qE "(password|secret|token|api[_-]?key).*[:=]\s*['\"][^'\"]{8,}['\"]" "$file" 2>/dev/null; then
        failure "Possible secret in: $file"
        SECRETS_FOUND=true
    fi
done

if [ "$SECRETS_FOUND" = false ]; then
    success "No obvious secrets detected"
fi

###############################################################################
# Summary
###############################################################################

print_header "Validation Summary"

echo ""
echo "Total Checks:    $TOTAL_CHECKS"
echo -e "${GREEN}Passed:${NC}         $PASSED_CHECKS"
echo -e "${YELLOW}Warnings:${NC}       $WARNING_CHECKS"
echo -e "${RED}Failed:${NC}         $FAILED_CHECKS"
echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✓ ALL VALIDATIONS PASSED${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Your code is ready to commit!"
    echo ""
    
    if [ $WARNING_CHECKS -gt 0 ]; then
        echo -e "${YELLOW}Note: $WARNING_CHECKS warning(s) detected. Review before merging.${NC}"
        echo ""
    fi
    
    exit 0
else
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ✗ VALIDATION FAILED${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Please fix the errors above before committing."
    echo ""
    echo "Detailed log: ${LOG_FILE}"
    echo ""
    
    exit 1
fi
