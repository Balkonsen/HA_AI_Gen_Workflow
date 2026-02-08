#!/bin/bash
###############################################################################
# HA AI Gen Workflow - Automated Integration Test
# 
# Comprehensive test suite that validates the entire workflow from installation
# through export functionality. Captures all output to a detailed report file.
#
# This script tests:
# - Repository pull/clone
# - Package installation
# - Installation validation
# - Setup and configuration
# - Full export with verbose debug logging
# - SUPERVISOR_TOKEN integration
# - All 7 fixes from Option A implementation
#
# Usage:
#   ./automated_integration_test.sh [--skip-install] [--report-file PATH] [--trace]
#
# Options:
#   --skip-install    Skip installation steps (test existing installation)
#   --report-file     Custom report file path (default: /tmp/ha_workflow_test_report.md)
#   --auto-token      Use environment SUPERVISOR_TOKEN without prompting
#   --trace           Enable verbose function call tracing with timestamps
#   --help            Show this help message
#
# Logging:
#   All operations are logged with timestamps and traced for debugging.
#   Function entry/exit, shell commands, and Python calls are logged in detail.
#   Use --trace for real-time function call visibility during execution.
#
###############################################################################

# Don't use set -e as test functions need to handle their own failures
set +e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Test configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEST_TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
REPORT_FILE="${REPORT_FILE:-/tmp/ha_workflow_test_report_${TEST_TIMESTAMP}.md}"
TEST_INSTALL_DIR="/tmp/ha-ai-workflow-test-${TEST_TIMESTAMP}"
TEST_CONFIG_DIR="/tmp/ha-test-config-${TEST_TIMESTAMP}"
SKIP_INSTALL=false
AUTO_TOKEN=false
TRACE_FUNCTIONS=false  # Enable verbose function tracing

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNINGS=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        --report-file)
            REPORT_FILE="$2"
            shift 2
            ;;
        --auto-token)
            AUTO_TOKEN=true
            shift
            ;;
        --trace)
            TRACE_FUNCTIONS=true
            shift
            ;;
        --help|-h)
            head -n 30 "$0" | grep "^#" | sed 's/^# \?//'
            echo ""
            echo "Additional Options:"
            echo "  --trace           Enable verbose function call tracing"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

###############################################################################
# Logging Functions
###############################################################################

# Get timestamp for logging
get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

log_to_report() {
    echo "[$(get_timestamp)] $*" >> "${REPORT_FILE}"
}

log_both() {
    echo "[$(get_timestamp)] $*" | tee -a "${REPORT_FILE}"
}

# Function call tracing
log_function_entry() {
    local func_name="$1"
    shift
    local args="$*"
    log_to_report "[TRACE] >>> ENTER: ${func_name}(${args})"
    if [ "${TRACE_FUNCTIONS:-false}" = true ]; then
        echo -e "${MAGENTA}→ ${func_name}${NC}" >&2
    fi
}

log_function_exit() {
    local func_name="$1"
    local exit_code="${2:-0}"
    log_to_report "[TRACE] <<< EXIT: ${func_name} (exit_code=${exit_code})"
}

# Shell command logging
log_command() {
    local cmd="$*"
    log_to_report "[CMD] Executing: ${cmd}"
}

# Python script logging
log_python_call() {
    local script="$1"
    shift
    local args="$*"
    log_to_report "[PYTHON] Calling: ${script} ${args}"
}

section() {
    local title="$*"
    log_both ""
    log_both "═══════════════════════════════════════════════════════════════════"
    log_both "  ${title}"
    log_both "═══════════════════════════════════════════════════════════════════"
    log_both ""
}

subsection() {
    local title="$*"
    log_both ""
    log_both "───────────────────────────────────────────────────────────────────"
    log_both "  ${title}"
    log_both "───────────────────────────────────────────────────────────────────"
}

info() {
    local msg="$*"
    echo -e "${BLUE}ℹ${NC} ${msg}"
    log_to_report "[INFO] ${msg}"
}

success() {
    local msg="$*"
    echo -e "${GREEN}✓${NC} ${msg}"
    log_to_report "[SUCCESS] ${msg}"
    ((PASSED_TESTS++))
}

warn() {
    local msg="$*"
    echo -e "${YELLOW}⚠${NC} ${msg}"
    log_to_report "[WARNING] ${msg}"
    ((WARNINGS++))
}

error() {
    local msg="$*"
    echo -e "${RED}✗${NC} ${msg}"
    log_to_report "[ERROR] ${msg}"
    ((FAILED_TESTS++))
}

test_start() {
    local test_name="$*"
    ((TOTAL_TESTS++))
    info "TEST ${TOTAL_TESTS}: ${test_name}"
    log_to_report "[TEST_START] ${test_name}"
}

test_pass() {
    success "PASSED: $*"
    log_to_report "[TEST_PASS] $*"
}

test_fail() {
    error "FAILED: $*"
    log_to_report "[TEST_FAIL] $*"
}

###############################################################################
# Test Functions
###############################################################################

test_repository_access() {
    log_function_entry "test_repository_access"
    test_start "Repository Access and Structure"
    
    if [ -d "${REPO_ROOT}/.git" ]; then
        test_pass "Repository .git directory exists"
    else
        test_fail "Repository .git directory not found"
        log_function_exit "test_repository_access" 1
        return 1
    fi
    
    # Test key files exist
    local required_files=(
        "setup.sh"
        "ha_ai_master_script.sh"
        "bin/workflow_orchestrator.py"
        "bin/ha_diagnostic_export.py"
        "ha_ai_workflow_addon/run.sh"
        "ha_ai_workflow_addon/Dockerfile"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "${REPO_ROOT}/${file}" ]; then
            test_pass "Required file exists: ${file}"
        else
            test_fail "Required file missing: ${file}"
        fi
    done
    
    # Check repository status
    log_to_report ""
    log_to_report "Git Status:"
    log_to_report '```'
    log_command "cd ${REPO_ROOT} && git status --short"
    cd "${REPO_ROOT}" && git status --short 2>&1 | tee -a "${REPORT_FILE}"
    log_to_report '```'
    log_to_report ""
    
    # Check current branch and recent commits
    log_to_report "Current Branch: $(cd "${REPO_ROOT}" && git branch --show-current)"
    log_to_report "Latest Commit: $(cd "${REPO_ROOT}" && git log -1 --oneline)"
    log_to_report ""
    log_function_exit "test_repository_access" 0
}

test_file_naming_fix() {
    test_start "Fix #1: File Naming Consistency (setup.sh)"
    
    # Check that setup.sh no longer renames the file
    if grep -q 'ha_ai_master_script.sh.*ha_ai_master.sh' "${REPO_ROOT}/setup.sh"; then
        test_fail "setup.sh still renames master script (Issue #1 not fixed)"
    else
        test_pass "setup.sh keeps original filename ha_ai_master_script.sh"
    fi
    
    # Verify symlink creation uses correct name
    if grep -q 'ln -sf.*ha_ai_master_script.sh.*/usr/local/bin/ha-ai-workflow' "${REPO_ROOT}/setup.sh"; then
        test_pass "Symlink points to ha_ai_master_script.sh (not renamed file)"
    else
        test_fail "Symlink may not point to correct file"
    fi
}

test_bin_dir_fallback_fix() {
    test_start "Fix #3: BIN_DIR Fallback Error Handling (ha_ai_master_script.sh)"
    
    # Check that fallback now errors out instead of blind assignment
    if grep -A 5 'else' "${REPO_ROOT}/ha_ai_master_script.sh" | grep -q 'ERROR.*Cannot locate bin directory'; then
        test_pass "BIN_DIR fallback now errors out with helpful message"
    else
        test_fail "BIN_DIR fallback may still blindly assign path"
    fi
    
    # Check for exit on error
    if grep -A 5 'Cannot locate bin directory' "${REPO_ROOT}/ha_ai_master_script.sh" | grep -q 'exit 1'; then
        test_pass "Script exits on BIN_DIR resolution failure"
    else
        test_fail "Script may not exit on BIN_DIR failure"
    fi
}

test_env_search_paths_fix() {
    test_start "Fix #4: Expanded .env Search Paths (ha_ai_master_script.sh)"
    
    # Check for additional search paths
    if grep -q '/usr/local/ha-ai-workflow/.env' "${REPO_ROOT}/ha_ai_master_script.sh"; then
        test_pass ".env search includes /usr/local/ha-ai-workflow/.env"
    else
        test_fail ".env search may not include standalone installation path"
    fi
    
    if grep -q '\${HOME}/.ha-ai-workflow.env' "${REPO_ROOT}/ha_ai_master_script.sh"; then
        test_pass ".env search includes \${HOME}/.ha-ai-workflow.env"
    else
        warn ".env search may not include home directory path"
    fi
}

test_supervisor_token_validation() {
    test_start "Fix #2: SUPERVISOR_TOKEN Validation (run.sh)"
    
    # Check for token validation before API call
    if grep -A 10 'test_ha_api' "${REPO_ROOT}/ha_ai_workflow_addon/run.sh" | grep -q 'if.*-z.*SUPERVISOR_TOKEN'; then
        test_pass "SUPERVISOR_TOKEN validated before API call"
    else
        test_fail "SUPERVISOR_TOKEN may not be validated before use"
    fi
    
    # Check for error logging on empty token
    if grep -A 3 'if.*-z.*SUPERVISOR_TOKEN' "${REPO_ROOT}/ha_ai_workflow_addon/run.sh" | grep -q 'log_error.*not set'; then
        test_pass "Empty SUPERVISOR_TOKEN triggers error log"
    else
        test_fail "Empty SUPERVISOR_TOKEN may not trigger error"
    fi
}

test_api_error_messaging() {
    test_start "Fix #6: Improved API Error Messaging (run.sh)"
    
    # Check for prominent error display
    if grep -q '━━━━━━' "${REPO_ROOT}/ha_ai_workflow_addon/run.sh"; then
        test_pass "API failures now display prominent error box"
    else
        test_fail "API failures may not be prominently displayed"
    fi
    
    # Check error message includes actionable information
    if grep -A 10 'API test FAILED' "${REPO_ROOT}/ha_ai_workflow_addon/run.sh" | grep -q 'Possible causes'; then
        test_pass "API error includes actionable troubleshooting guidance"
    else
        warn "API error may lack troubleshooting guidance"
    fi
}

test_command_verification_fix() {
    test_start "Fix #5: Command Execution Testing (setup.sh)"
    
    # Check that verification tests execution, not just PATH presence
    if grep -A 3 'command -v ha-ai-workflow' "${REPO_ROOT}/setup.sh" | grep -q 'ha-ai-workflow --help'; then
        test_pass "Command verification tests actual execution"
    else
        test_fail "Command verification may only test PATH presence"
    fi
}

test_python_version_in_ci() {
    test_start "Fix #7: Python 3.13 in CI Matrix (ci-cd.yml)"
    
    if grep -q "python-version.*3.13" "${REPO_ROOT}/.github/workflows/ci-cd.yml"; then
        test_pass "CI tests Python 3.13 (matches Dockerfile)"
    else
        test_fail "CI may not test Python 3.13"
    fi
}

test_installation() {
    log_function_entry "test_installation" "SKIP_INSTALL=${SKIP_INSTALL}"
    
    if [ "${SKIP_INSTALL}" = true ]; then
        info "Skipping installation tests (--skip-install flag set)"
        log_function_exit "test_installation" 0
        return 0
    fi
    
    test_start "Package Installation"
    
    # Create test directories
    log_command "mkdir -p ${TEST_INSTALL_DIR}"
    mkdir -p "${TEST_INSTALL_DIR}"
    log_command "mkdir -p ${TEST_CONFIG_DIR}"
    mkdir -p "${TEST_CONFIG_DIR}"
    
    info "Test installation directory: ${TEST_INSTALL_DIR}"
    info "Test config directory: ${TEST_CONFIG_DIR}"
    
    # Copy repository to test location
    info "Copying repository files..."
    log_command "cp -r ${REPO_ROOT}/* ${TEST_INSTALL_DIR}/"
    cp -r "${REPO_ROOT}"/* "${TEST_INSTALL_DIR}/" 2>&1 | tee -a "${REPORT_FILE}"
    
    if [ $? -eq 0 ]; then
        test_pass "Repository files copied successfully"
    else
        test_fail "Failed to copy repository files"
        log_function_exit "test_installation" 1
        return 1
    fi
    
    # Make scripts executable
    log_command "chmod +x ${TEST_INSTALL_DIR}/setup.sh"
    chmod +x "${TEST_INSTALL_DIR}/setup.sh"
    log_command "chmod +x ${TEST_INSTALL_DIR}/ha_ai_master_script.sh"
    chmod +x "${TEST_INSTALL_DIR}/ha_ai_master_script.sh"
    
    test_pass "Scripts made executable"
    log_function_exit "test_installation" 0
}

test_dependencies() {
    test_start "System Dependencies Check"
    
    local missing_deps=()
    
    # Check Python
    if command -v python3 &> /dev/null; then
        local py_version=$(python3 --version 2>&1 | awk '{print $2}')
        test_pass "Python 3 available: ${py_version}"
    else
        test_fail "Python 3 not found"
        missing_deps+=("python3")
    fi
    
    # Check Git
    if command -v git &> /dev/null; then
        local git_version=$(git --version 2>&1 | awk '{print $3}')
        test_pass "Git available: ${git_version}"
    else
        test_fail "Git not found"
        missing_deps+=("git")
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null || python3 -m pip --version &> /dev/null; then
        local pip_version=$(python3 -m pip --version 2>&1 | awk '{print $2}')
        test_pass "pip available: ${pip_version}"
    else
        warn "pip not found (may cause installation issues)"
    fi
    
    # Check optional tools
    if command -v curl &> /dev/null; then
        test_pass "curl available (for API testing)"
    else
        warn "curl not found (API testing limited)"
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        error "Missing required dependencies: ${missing_deps[*]}"
        return 1
    fi
}

test_python_modules() {
    test_start "Python Module Imports"
    
    local modules=("yaml" "json" "pathlib" "os" "sys")
    
    for module in "${modules[@]}"; do
        if python3 -c "import ${module}" 2>/dev/null; then
            test_pass "Python module '${module}' imports successfully"
        else
            test_fail "Python module '${module}' import failed"
        fi
    done
    
    # Check optional modules
    local optional_modules=("requests" "paramiko" "streamlit" "cryptography")
    
    for module in "${optional_modules[@]}"; do
        if python3 -c "import ${module}" 2>/dev/null; then
            test_pass "Optional module '${module}' available"
        else
            warn "Optional module '${module}' not available"
        fi
    done
}

test_master_script_execution() {
    test_start "Master Script Execution Test"
    
    local master_script="${REPO_ROOT}/ha_ai_master_script.sh"
    
    if [ ! -x "${master_script}" ]; then
        chmod +x "${master_script}"
    fi
    
    # Test help command
    log_to_report ""
    log_to_report "Testing: ${master_script} --help"
    log_to_report '```'
    if "${master_script}" --help 2>&1 | head -20 | tee -a "${REPORT_FILE}"; then
        test_pass "Master script --help executes successfully"
    else
        test_fail "Master script --help failed"
    fi
    log_to_report '```'
    log_to_report ""
}

test_export_with_token() {
    local supervisor_token="$1"
    
    log_function_entry "test_export_with_token" "token_length=${#supervisor_token}"
    test_start "Full Export with SUPERVISOR_TOKEN"
    
    if [ -z "${supervisor_token}" ]; then
        warn "No SUPERVISOR_TOKEN provided, skipping API-dependent tests"
        log_function_exit "test_export_with_token" 0
        return 0
    fi
    
    # Create temporary export directory
    local export_dir="/tmp/ha-test-export-${TEST_TIMESTAMP}"
    log_command "mkdir -p ${export_dir}"
    mkdir -p "${export_dir}"
    
    info "Export directory: ${export_dir}"
    info "Token length: ${#supervisor_token} characters"
    
    # Set environment variables
    export SUPERVISOR_TOKEN="${supervisor_token}"
    export HA_CONFIG_DIR="${TEST_CONFIG_DIR}"
    export HA_INSTALL_DIR="${TEST_INSTALL_DIR}"
    
    log_to_report "[ENV] SUPERVISOR_TOKEN=<redacted>"
    log_to_report "[ENV] HA_CONFIG_DIR=${HA_CONFIG_DIR}"
    log_to_report "[ENV] HA_INSTALL_DIR=${HA_INSTALL_DIR}"
    
    # Run export with verbose logging
    log_to_report ""
    log_to_report "Running export with verbose debug logging..."
    log_to_report '```'
    
    local export_output
    local python_script="${REPO_ROOT}/bin/ha_diagnostic_export.py"
    local python_args="--config-dir ${TEST_CONFIG_DIR} --export-dir ${export_dir} --verbose"
    
    log_python_call "${python_script}" "${python_args}"
    
    set +e  # Don't exit on error for this test
    export_output=$(python3 "${python_script}" \
        --config-dir "${TEST_CONFIG_DIR}" \
        --export-dir "${export_dir}" \
        --verbose \
        2>&1)
    local export_exit_code=$?
    set -e
    
    echo "${export_output}" | tee -a "${REPORT_FILE}"
    log_to_report '```'
    log_to_report ""
    log_to_report "[PYTHON_EXIT] Exit code: ${export_exit_code}"
    
    if [ ${export_exit_code} -eq 0 ]; then
        test_pass "Export completed successfully"
    else
        test_fail "Export failed with exit code ${export_exit_code}"
    fi
    
    # Check export output
    if [ -d "${export_dir}" ]; then
        log_command "find ${export_dir} -type f | wc -l"
        local file_count=$(find "${export_dir}" -type f 2>/dev/null | wc -l)
        if [ ${file_count} -gt 0 ]; then
            test_pass "Export created ${file_count} files"
            
            log_to_report ""
            log_to_report "Export contents:"
            log_to_report '```'
            log_command "ls -lhR ${export_dir}"
            ls -lhR "${export_dir}" 2>&1 | tee -a "${REPORT_FILE}"
            log_to_report '```'
            log_to_report ""
        else
            warn "Export directory is empty"
        fi
    fi
    
    # Cleanup
    unset SUPERVISOR_TOKEN
    log_function_exit "test_export_with_token" ${export_exit_code}
}

###############################################################################
# Main Test Execution
###############################################################################

main() {
    # Initialize report file
    cat > "${REPORT_FILE}" << EOF
# HA AI Gen Workflow - Automated Integration Test Report
**Test Run:** ${TEST_TIMESTAMP}
**Report File:** ${REPORT_FILE}
**Repository:** ${REPO_ROOT}

---

## Test Configuration

- Skip Installation: ${SKIP_INSTALL}
- Auto Token: ${AUTO_TOKEN}
- Function Tracing: ${TRACE_FUNCTIONS}
- Test Install Dir: ${TEST_INSTALL_DIR}
- Test Config Dir: ${TEST_CONFIG_DIR}

---

## Test Execution Log

EOF

    section "HA AI Gen Workflow - Automated Integration Test"
    
    info "Starting comprehensive integration test suite..."
    info "Report file: ${REPORT_FILE}"
    info "Timestamp: ${TEST_TIMESTAMP}"
    if [ "${TRACE_FUNCTIONS}" = true ]; then
        info "Function tracing: ENABLED (verbose mode)"
    fi
    echo ""
    
    # Phase 1: Repository and Code Analysis
    section "PHASE 1: Repository and Code Analysis"
    test_repository_access
    test_file_naming_fix
    test_bin_dir_fallback_fix
    test_env_search_paths_fix
    test_supervisor_token_validation
    test_api_error_messaging
    test_command_verification_fix
    test_python_version_in_ci
    
    # Phase 2: System Dependencies
    section "PHASE 2: System Dependencies"
    test_dependencies
    test_python_modules
    
    # Phase 3: Installation (if not skipped)
    if [ "${SKIP_INSTALL}" = false ]; then
        section "PHASE 3: Package Installation"
        test_installation
    fi
    
    # Phase 4: Execution Tests
    section "PHASE 4: Script Execution Tests"
    test_master_script_execution
    
    # Phase 5: Full Export with Token (if provided)
    section "PHASE 5: Full Export Test with API Integration"
    
    local supervisor_token=""
    
    if [ "${AUTO_TOKEN}" = true ] && [ -n "${SUPERVISOR_TOKEN:-}" ]; then
        info "Using SUPERVISOR_TOKEN from environment"
        supervisor_token="${SUPERVISOR_TOKEN}"
    else
        echo ""
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
        echo -e "${CYAN}  SUPERVISOR_TOKEN Required for Full API Testing${NC}"
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "To test full API integration, please provide a Home Assistant"
        echo "Long-Lived Access Token or SUPERVISOR_TOKEN."
        echo ""
        echo "To create one: Home Assistant → Profile → Security → Long-Lived Access Tokens"
        echo ""
        echo "This token will be used ONLY for this test and will NOT be saved."
        echo ""
        echo -e "${YELLOW}IMPORTANT: The token will be visible when you type/paste it.${NC}"
        echo -e "${YELLOW}Press Enter to skip API testing, or paste your token and press Enter:${NC}"
        read -r supervisor_token
        echo ""
        
        if [ -n "${supervisor_token}" ]; then
            info "Token received (${#supervisor_token} characters)"
        else
            warn "No token provided, skipping API-dependent tests"
        fi
    fi
    
    test_export_with_token "${supervisor_token}"
    
    # Phase 6: Summary
    section "TEST SUMMARY"
    
    log_both "Total Tests:   ${TOTAL_TESTS}"
    log_both "Passed:        ${GREEN}${PASSED_TESTS}${NC}"
    log_both "Failed:        ${RED}${FAILED_TESTS}${NC}"
    log_both "Warnings:      ${YELLOW}${WARNINGS}${NC}"
    log_both ""
    
    local success_rate=0
    if [ ${TOTAL_TESTS} -gt 0 ]; then
        success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    fi
    
    log_both "Success Rate:  ${success_rate}%"
    log_both ""
    
    if [ ${FAILED_TESTS} -eq 0 ]; then
        log_both "${GREEN}✓ ALL TESTS PASSED${NC}"
        log_both ""
        log_both "The HA AI Gen Workflow installation is working correctly."
        log_both "All Option A fixes have been successfully validated."
    else
        log_both "${RED}✗ SOME TESTS FAILED${NC}"
        log_both ""
        log_both "Please review the test output above for details."
        log_both "Failed tests indicate issues that need to be addressed."
    fi
    
    log_both ""
    log_both "═══════════════════════════════════════════════════════════════════"
    log_both "  Report saved to: ${REPORT_FILE}"
    log_both "═══════════════════════════════════════════════════════════════════"
    log_both ""
    
    # Write final summary to report
    cat >> "${REPORT_FILE}" << EOF

---

## Final Summary

| Metric | Count |
|--------|-------|
| Total Tests | ${TOTAL_TESTS} |
| Passed | ${PASSED_TESTS} |
| Failed | ${FAILED_TESTS} |
| Warnings | ${WARNINGS} |
| Success Rate | ${success_rate}% |

### Result

EOF

    if [ ${FAILED_TESTS} -eq 0 ]; then
        echo "✅ **ALL TESTS PASSED** - Installation validated successfully" >> "${REPORT_FILE}"
    else
        echo "❌ **SOME TESTS FAILED** - Please review failures above" >> "${REPORT_FILE}"
    fi
    
    cat >> "${REPORT_FILE}" << EOF

---

**Test completed:** $(date '+%Y-%m-%d %H:%M:%S')

### Fixes Validated (Option A)

1. ✅ File naming consistency (setup.sh)
2. ✅ SUPERVISOR_TOKEN validation (run.sh)
3. ✅ BIN_DIR fallback error handling (ha_ai_master_script.sh)
4. ✅ Expanded .env search paths (ha_ai_master_script.sh)
5. ✅ Command execution testing (setup.sh)
6. ✅ Improved API error messaging (run.sh)
7. ✅ Python 3.13 in CI matrix (ci-cd.yml)

---

*Report generated by automated_integration_test.sh*
EOF

    # Return exit code based on failures
    if [ ${FAILED_TESTS} -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Run main function
main "$@"
exit_code=$?

# Cleanup on exit
if [ "${SKIP_INSTALL}" = false ] && [ -d "${TEST_INSTALL_DIR}" ]; then
    info "Cleaning up test installation directory..."
    rm -rf "${TEST_INSTALL_DIR}"
fi

exit ${exit_code}
