#!/bin/bash
###############################################################################
# Home Assistant AI Workflow - Master Orchestrator
# Automated export, AI context generation, and import with git versioning
###############################################################################

set -e  # Exit on error (can be disabled with --no-strict)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="/config"
EXPORT_DIR="${CONFIG_DIR}/ai_exports"
SECRETS_DIR="${EXPORT_DIR}/secrets"
ARCHIVES_DIR="${EXPORT_DIR}/archives"
IMPORT_DIR="${CONFIG_DIR}/ai_imports/pending"
BIN_DIR="${SCRIPT_DIR}/bin"
LOG_FILE="${EXPORT_DIR}/workflow.log"
AUTO_MODE=false
STRICT_MODE=true
UPLOAD_DEBUG=false

# Ensure directories exist
mkdir -p "${EXPORT_DIR}" "${SECRETS_DIR}" "${ARCHIVES_DIR}" "${IMPORT_DIR}" "${BIN_DIR}"

###############################################################################
# Utility Functions
###############################################################################

log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOG_FILE}"
}

info() {
    echo -e "${BLUE}ℹ${NC} $@"
    log "INFO" "$@"
}

success() {
    echo -e "${GREEN}✓${NC} $@"
    log "SUCCESS" "$@"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $@"
    log "WARN" "$@"
}

error() {
    echo -e "${RED}✗${NC} $@"
    log "ERROR" "$@"
}

banner() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  $@"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
}

confirm() {
    local prompt="$1"
    local default="${2:-no}"
    
    if [ "$AUTO_MODE" = true ]; then
        info "Auto-mode enabled, assuming 'yes'"
        return 0
    fi
    
    if [ "$default" = "yes" ]; then
        read -p "$prompt [Y/n]: " response
        response=${response:-y}
    else
        read -p "$prompt [y/N]: " response
        response=${response:-n}
    fi
    
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

###############################################################################
# Dependency Management
###############################################################################

check_dependencies() {
    info "Checking dependencies..."
    
    local missing_deps=()
    
    # Check for Python 3
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Check for git
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi
    
    # Check for ha CLI
    if ! command -v ha &> /dev/null; then
        warn "Home Assistant CLI not found - some features may be limited"
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        error "Missing dependencies: ${missing_deps[*]}"
        return 1
    fi
    
    success "Core dependencies OK"
    return 0
}

install_pyyaml() {
    info "Checking PyYAML installation..."
    
    if python3 -c "import yaml" 2>/dev/null; then
        success "PyYAML already installed"
        return 0
    fi
    
    warn "PyYAML not found, attempting installation..."
    
    # Try different installation methods
    if python3 -m pip install pyyaml --break-system-packages &>/dev/null; then
        success "PyYAML installed successfully"
        return 0
    elif python3 -m pip install pyyaml --user &>/dev/null; then
        success "PyYAML installed successfully (user)"
        return 0
    else
        error "Failed to install PyYAML automatically"
        echo ""
        echo "Please install manually:"
        echo "  python3 -m pip install pyyaml --break-system-packages"
        echo "or:"
        echo "  python3 -m pip install pyyaml --user"
        return 1
    fi
}

###############################################################################
# Git Management
###############################################################################

init_git_repo() {
    if [ -d "${CONFIG_DIR}/.git" ]; then
        info "Git repository already initialized"
        return 0
    fi
    
    banner "Git Repository Initialization"
    
    info "Initializing git repository in ${CONFIG_DIR}..."
    cd "${CONFIG_DIR}"
    
    git init
    
    # Create .gitignore if it doesn't exist
    if [ ! -f .gitignore ]; then
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
        success "Created .gitignore"
    fi
    
    # Initial commit
    git add .gitignore
    git commit -m "Initial commit - HA AI Workflow setup" || true
    
    success "Git repository initialized"
}

get_current_branch() {
    git -C "${CONFIG_DIR}" branch --show-current 2>/dev/null || echo "main"
}

ensure_clean_working_tree() {
    cd "${CONFIG_DIR}"
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        warn "Working directory has uncommitted changes"
        if confirm "Commit changes before proceeding?"; then
            git add -A
            git commit -m "Auto-commit before AI workflow: $(date '+%Y-%m-%d %H:%M:%S')"
            success "Changes committed"
        else
            error "Please commit or stash changes first"
            return 1
        fi
    fi
    return 0
}

###############################################################################
# Export Workflow
###############################################################################

run_export() {
    banner "Starting Export Workflow"
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local export_name="ha_export_${timestamp}"
    local temp_export_dir="/tmp/${export_name}"
    
    # Step 1: Run diagnostic export
    info "Step 1/5: Running diagnostic export..."
    if ! python3 "${BIN_DIR}/ha_diagnostic_export.py" --output-dir "/tmp" --name "${export_name}"; then
        error "Export failed"
        return 1
    fi
    success "Export completed"
    
    # Step 2: Verify export
    info "Step 2/5: Verifying export completeness..."
    local tarball="/tmp/${export_name}.tar.gz"
    if [ ! -f "${tarball}" ]; then
        error "Export tarball not found: ${tarball}"
        return 1
    fi
    
    if ! python3 "${BIN_DIR}/ha_export_verifier.py" "${tarball}"; then
        error "Export verification failed"
        return 1
    fi
    success "Export verified"
    
    # Step 3: Extract to working directory
    info "Step 3/5: Extracting export..."
    tar -xzf "${tarball}" -C "${EXPORT_DIR}/"
    local extracted_dir="${EXPORT_DIR}/${export_name}"
    success "Extracted to ${extracted_dir}"
    
    # Step 4: Generate AI context
    info "Step 4/5: Generating AI context..."
    if ! python3 "${BIN_DIR}/ha_ai_context_gen.py" "${extracted_dir}"; then
        error "AI context generation failed"
        return 1
    fi
    success "AI context generated"
    
    # Step 5: Manage secrets
    info "Step 5/5: Managing secrets..."
    local secrets_file="${extracted_dir}/secrets/secrets_map.json"
    if [ -f "${secrets_file}" ]; then
        # Copy to secrets directory with timestamp
        cp "${secrets_file}" "${SECRETS_DIR}/secrets_map_${timestamp}.json"
        # Update latest
        cp "${secrets_file}" "${SECRETS_DIR}/secrets_map_latest.json"
        
        # Keep only last 5 backups
        cd "${SECRETS_DIR}"
        ls -t secrets_map_*.json 2>/dev/null | tail -n +7 | xargs -r rm
        
        success "Secrets backed up (keeping last 5 versions)"
    fi
    
    # Clean up temporary files
    info "Cleaning up temporary files..."
    rm -f "${tarball}"
    rm -rf "/tmp/${export_name}"
    [ -d "${ARCHIVES_DIR}" ] && find "${ARCHIVES_DIR}" -name "*.tar.gz" -mtime +7 -delete
    success "Cleanup completed"
    
    # Git commit snapshot
    info "Creating git snapshot..."
    cd "${CONFIG_DIR}"
    git add -A
    git commit -m "Export snapshot: ${timestamp}" || true
    
    # Summary
    banner "Export Workflow Complete"
    echo ""
    success "Export Location: ${extracted_dir}"
    success "AI Prompt: ${extracted_dir}/AI_PROMPT.md"
    success "AI Context: ${extracted_dir}/AI_CONTEXT.json"
    success "Secrets: ${SECRETS_DIR}/secrets_map_latest.json"
    echo ""
    info "Next Steps:"
    echo "  1. Review AI_PROMPT.md"
    echo "  2. Share with AI assistant (DO NOT share secrets!)"
    echo "  3. Place AI-generated files in: ${IMPORT_DIR}"
    echo "  4. Run: $(basename $0) import"
    echo ""
    
    return 0
}

###############################################################################
# Import Workflow
###############################################################################

scan_import_directory() {
    info "Scanning import directory: ${IMPORT_DIR}"
    
    if [ ! -d "${IMPORT_DIR}" ]; then
        warn "Import directory does not exist"
        return 1
    fi
    
    local file_count=$(find "${IMPORT_DIR}" -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) 2>/dev/null | wc -l)
    
    if [ "$file_count" -eq 0 ]; then
        warn "No files found in import directory"
        return 1
    fi
    
    success "Found ${file_count} file(s) to import"
    
    echo ""
    echo "Files found:"
    find "${IMPORT_DIR}" -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) -exec basename {} \; | sort
    echo ""
    
    return 0
}

run_import() {
    banner "Starting Import Workflow"
    
    # Pre-flight checks
    if ! check_disk_space; then
        return 1
    fi
    
    # Step 1: Scan import directory
    if ! scan_import_directory; then
        handle_error "no_files_to_import" "No files found in ${IMPORT_DIR}" "import_scan"
        return 1
    fi
    
    # Step 1.5: Pre-import validation
    if ! pre_import_validation; then
        handle_error "import_failed" "Pre-import YAML validation failed" "pre_import_validation"
        return 1
    fi
    
    # Step 2: Get branch name
    local branch_name
    if [ "$AUTO_MODE" = true ]; then
        branch_name="ai-import-$(date '+%Y%m%d-%H%M%S')"
        info "Auto-mode: Using branch name: ${branch_name}"
    else
        echo ""
        read -p "Enter branch name for this import: " branch_name
        branch_name=${branch_name:-"ai-import-$(date '+%Y%m%d-%H%M%S')"}
    fi
    
    info "Branch name: ${branch_name}"
    
    # Step 3: Ensure clean working tree
    if ! ensure_clean_working_tree; then
        return 1
    fi
    
    # Step 4: Create new branch
    info "Creating branch: ${branch_name}"
    cd "${CONFIG_DIR}"
    if ! git checkout -b "${branch_name}" 2>/dev/null; then
        error "Failed to create branch (may already exist)"
        if confirm "Checkout existing branch?"; then
            git checkout "${branch_name}"
        else
            return 1
        fi
    fi
    success "Branch created"
    
    # Step 5: Run import script
    info "Running import script..."
    local secrets_file="${SECRETS_DIR}/secrets_map_latest.json"
    
    if [ ! -f "${secrets_file}" ]; then
        handle_error "secrets_not_found" "Secrets file not found: ${secrets_file}" "import"
        git checkout -
        return 1
    fi
    
    if ! python3 "${BIN_DIR}/ha_config_import.py" --apply "${IMPORT_DIR}" "${secrets_file}"; then
        handle_error "import_failed" "Import script failed" "ha_config_import"
        git checkout -
        return 1
    fi
    success "Import completed"
    
    # Step 6: Commit changes
    info "Committing changes..."
    git add -A
    git commit -m "AI Import: ${branch_name} - $(date '+%Y-%m-%d %H:%M:%S')"
    success "Changes committed"
    
    # Step 7: Show diff
    echo ""
    info "Changes made:"
    git diff HEAD~1 --stat
    echo ""
    
    # Step 8: Validate configuration
    info "Validating configuration..."
    if ! validate_ha_config; then
        handle_error "config_validation_failed" "Configuration validation failed" "${branch_name}"
        return 1
    fi
    success "Configuration valid"
    
    # Step 9: Merge to main
    local main_branch=$(git branch | grep -E '^\*?\s+(main|master)' | sed 's/^[* ]*//' | head -1)
    main_branch=${main_branch:-main}
    
    info "Merging ${branch_name} into ${main_branch}..."
    git checkout "${main_branch}"
    if ! git merge "${branch_name}" --no-ff -m "Merge AI import: ${branch_name}"; then
        error "Merge failed - conflicts detected"
        echo ""
        echo "Manual merge required:"
        echo "  1. Resolve conflicts: git status"
        echo "  2. Add resolved files: git add <file>"
        echo "  3. Complete merge: git commit"
        echo ""
        return 1
    fi
    success "Merged successfully"
    
    # Step 10: Deploy confirmation
    banner "Ready to Deploy"
    echo ""
    warn "This will restart Home Assistant with the new configuration"
    echo ""
    
    if [ "$AUTO_MODE" = false ]; then
        read -p "Type 'DEPLOY' to confirm restart: " confirm_deploy
        if [ "$confirm_deploy" != "DEPLOY" ]; then
            info "Deployment cancelled"
            info "Changes are committed but Home Assistant not restarted"
            info "To deploy later, run: ha core restart"
            return 0
        fi
    else
        info "Auto-mode: Proceeding with deployment"
    fi
    
    # Step 11: Restart Home Assistant
    info "Restarting Home Assistant..."
    if command -v ha &> /dev/null; then
        ha core restart
        success "Home Assistant restart initiated"
    else
        warn "HA CLI not available, please restart manually"
        echo "  docker restart homeassistant"
    fi
    
    # Step 12: Move imported files to archive
    info "Archiving imported files..."
    local archive_dir="${ARCHIVES_DIR}/imported_$(date '+%Y%m%d_%H%M%S')"
    mkdir -p "${archive_dir}"
    mv "${IMPORT_DIR}"/* "${archive_dir}/" 2>/dev/null || true
    success "Files archived"
    
    # Summary
    banner "Import Workflow Complete"
    echo ""
    success "Branch: ${branch_name}"
    success "Merged to: ${main_branch}"
    success "Home Assistant restarted"
    echo ""
    info "Monitor logs with: docker logs homeassistant -f"
    info "Or: tail -f /config/home-assistant.log"
    echo ""
    
    return 0
}

###############################################################################
# Validation
###############################################################################

validate_ha_config() {
    info "Running Home Assistant configuration check..."
    
    # Check if HA CLI is available
    if ! command -v ha &> /dev/null; then
        warn "HA CLI not available, skipping validation"
        warn "Please verify configuration manually"
        return 0
    fi
    
    # Run configuration check
    local check_output
    check_output=$(ha core check 2>&1)
    local check_result=$?
    
    if [ $check_result -eq 0 ]; then
        success "Configuration check passed"
        return 0
    else
        error "Configuration check failed"
        echo ""
        echo "Error details:"
        echo "${check_output}"
        echo ""
        
        # Check for common errors
        if echo "${check_output}" | grep -q "Integration error"; then
            echo "💡 Tip: Check integration configurations"
            echo "   Common issues:"
            echo "   - Missing required fields"
            echo "   - Invalid entity references"
            echo "   - Deprecated configuration syntax"
        fi
        
        if echo "${check_output}" | grep -q "Invalid config"; then
            echo "💡 Tip: YAML syntax error detected"
            echo "   Use online YAML validator or:"
            echo "   python3 -c \"import yaml; yaml.safe_load(open('configuration.yaml'))\""
        fi
        
        if echo "${check_output}" | grep -q "not found"; then
            echo "💡 Tip: Entity or service not found"
            echo "   - Verify entity IDs exist"
            echo "   - Check integration is loaded"
            echo "   - Restart HA if recently added"
        fi
        
        return 1
    fi
}

pre_import_validation() {
    info "Running pre-import validation..."
    
    # Check all YAML files in import directory
    local has_errors=false
    
    for file in "${IMPORT_DIR}"/*.{yaml,yml}; do
        if [ -f "${file}" ]; then
            info "Validating: $(basename ${file})"
            if ! validate_yaml_syntax "${file}"; then
                has_errors=true
            fi
        fi
    done 2>/dev/null
    
    if [ "$has_errors" = true ]; then
        error "YAML validation failed"
        return 1
    fi
    
    success "Pre-import validation passed"
    return 0
}

handle_error() {
    local error_type=$1
    local error_message=$2
    local context=$3
    
    error "ERROR: ${error_message}"
    
    # Log detailed error
    log "ERROR" "Type: ${error_type}"
    log "ERROR" "Message: ${error_message}"
    log "ERROR" "Context: ${context}"
    
    # Check for common error patterns
    case "${error_type}" in
        "pyyaml_missing")
            echo ""
            error "PyYAML is not installed"
            echo ""
            echo "Solutions:"
            echo "  1. python3 -m pip install pyyaml --break-system-packages"
            echo "  2. apk add py3-yaml"
            echo "  3. Run setup again: ./setup.sh"
            echo ""
            return 1
            ;;
        
        "git_not_initialized")
            echo ""
            error "Git repository not initialized"
            echo ""
            echo "Solutions:"
            echo "  1. Run: ha-ai-workflow setup"
            echo "  2. Manually: cd /config && git init"
            echo ""
            return 1
            ;;
        
        "config_validation_failed")
            echo ""
            error "Home Assistant configuration validation failed"
            echo ""
            echo "Solutions:"
            echo "  1. Check syntax: ha core check"
            echo "  2. Review debug report: cat ${EXPORT_DIR}/debug_report_*.md"
            echo "  3. Rollback: git checkout HEAD~1"
            echo ""
            generate_debug_report "validation_failed" "$(get_current_branch)"
            return 1
            ;;
        
        "no_files_to_import")
            echo ""
            warn "No files found in import directory"
            echo ""
            echo "Solutions:"
            echo "  1. Place AI-generated files in: ${IMPORT_DIR}"
            echo "  2. Verify directory exists: ls -la ${IMPORT_DIR}"
            echo "  3. Check file permissions"
            echo ""
            return 1
            ;;
        
        "secrets_not_found")
            echo ""
            error "Secrets file not found"
            echo ""
            echo "Solutions:"
            echo "  1. Run export first: ha-ai-workflow export"
            echo "  2. Check location: ls ${SECRETS_DIR}/secrets_map_latest.json"
            echo "  3. Restore from backup: cp ${SECRETS_DIR}/secrets_map_*.json ${SECRETS_DIR}/secrets_map_latest.json"
            echo ""
            return 1
            ;;
        
        "export_failed")
            echo ""
            error "Export process failed"
            echo ""
            echo "Possible causes:"
            echo "  1. Insufficient disk space: df -h"
            echo "  2. Permission issues: try sudo"
            echo "  3. /config directory not accessible"
            echo ""
            echo "Debug steps:"
            echo "  1. Check logs: tail -50 ${LOG_FILE}"
            echo "  2. Verify /config exists: ls -la /config"
            echo "  3. Check available space: df -h /config"
            echo ""
            return 1
            ;;
        
        "import_failed")
            echo ""
            error "Import process failed"
            echo ""
            echo "Recovery steps:"
            echo "  1. Check debug report: cat ${EXPORT_DIR}/debug_report_*.md"
            echo "  2. Verify file format: python3 -c 'import yaml; yaml.safe_load(open(\"${IMPORT_DIR}/file.yaml\"))'"
            echo "  3. Rollback: git checkout -"
            echo ""
            generate_debug_report "import_failed" "$(get_current_branch)"
            return 1
            ;;
        
        "disk_space_low")
            echo ""
            error "Low disk space detected"
            echo ""
            echo "Free up space:"
            echo "  1. Clean old exports: rm -rf ${ARCHIVES_DIR}/*"
            echo "  2. Clean HA logs: rm -f /config/*.log*"
            echo "  3. Clean docker: docker system prune"
            echo ""
            df -h /config
            echo ""
            return 1
            ;;
        
        *)
            echo ""
            error "An unexpected error occurred"
            echo ""
            echo "Debug information:"
            echo "  Error type: ${error_type}"
            echo "  Error message: ${error_message}"
            echo "  Context: ${context}"
            echo ""
            echo "Please check:"
            echo "  1. Log file: ${LOG_FILE}"
            echo "  2. System status: ha-ai-workflow status"
            echo "  3. GitHub issues: https://github.com/yourusername/ha-ai-workflow/issues"
            echo ""
            return 1
            ;;
    esac
}

check_disk_space() {
    local required_mb=500
    local available_mb=$(df -m /config | awk 'NR==2 {print $4}')
    
    if [ "${available_mb}" -lt "${required_mb}" ]; then
        handle_error "disk_space_low" "Only ${available_mb}MB available (${required_mb}MB required)" "/config"
        return 1
    fi
    
    return 0
}

validate_yaml_syntax() {
    local file=$1
    
    if [ ! -f "${file}" ]; then
        return 0  # File doesn't exist, skip
    fi
    
    if ! python3 -c "import yaml; yaml.safe_load(open('${file}'))" 2>/dev/null; then
        error "YAML syntax error in: ${file}"
        python3 -c "import yaml; yaml.safe_load(open('${file}'))" 2>&1
        return 1
    fi
    
    return 0
}

check_ha_availability() {
    if ! command -v ha &> /dev/null; then
        warn "Home Assistant CLI not available"
        warn "Some features will be limited"
        return 1
    fi
    
    if ! ha core info &>/dev/null; then
        warn "Cannot connect to Home Assistant"
        warn "Validation features disabled"
        return 1
    fi
    
    return 0
}

###############################################################################
# Debug Report Generation
###############################################################################

generate_debug_report() {
    local error_type=$1
    local branch_name=$2
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local debug_file="${EXPORT_DIR}/debug_report_${timestamp}.md"
    
    banner "Generating Debug Report"
    
    cat > "${debug_file}" << EOF
# Home Assistant AI Workflow - Debug Report

**Generated:** $(date '+%Y-%m-%d %H:%M:%S')
**Error Type:** ${error_type}
**Branch:** ${branch_name}

---

## Error Summary

The import workflow encountered an error during ${error_type}.

## Git Status

\`\`\`
$(cd "${CONFIG_DIR}" && git status)
\`\`\`

## Recent Changes

\`\`\`diff
$(cd "${CONFIG_DIR}" && git diff HEAD)
\`\`\`

## Configuration Check Output

\`\`\`
$(ha core check 2>&1 || echo "HA CLI not available")
\`\`\`

## Recent Log Entries

\`\`\`
$(tail -100 "${LOG_FILE}")
\`\`\`

## System Information

- **HA Version:** $(ha core info --raw-json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('version','unknown'))" 2>/dev/null || echo "unknown")
- **Supervisor Version:** $(ha supervisor info --raw-json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('version','unknown'))" 2>/dev/null || echo "unknown")
- **Python Version:** $(python3 --version)
- **Git Branch:** $(cd "${CONFIG_DIR}" && git branch --show-current)

## Files Changed

\`\`\`
$(cd "${CONFIG_DIR}" && git diff --name-only HEAD)
\`\`\`

## Recommendations for AI

1. Review the configuration check output above
2. Check for YAML syntax errors
3. Verify entity references are valid
4. Check for missing dependencies or integrations
5. Review recent log entries for specific errors

## How to Use This Report

Share this report with an AI assistant to get help debugging the issue.
DO NOT include any sensitive information (passwords, tokens, etc.).

## Rollback Instructions

To rollback these changes:

\`\`\`bash
cd ${CONFIG_DIR}
git checkout $(cd "${CONFIG_DIR}" && git branch | grep -v "${branch_name}" | head -1 | sed 's/^[* ]*//')
ha core restart
\`\`\`

---

*Generated by HA AI Workflow*
EOF
    
    success "Debug report created: ${debug_file}"
    
    # Offer to upload
    if [ "$UPLOAD_DEBUG" = true ]; then
        info "Uploading debug report..."
        # TODO: Add upload logic (e.g., to pastebin, gist, etc.)
        warn "Upload functionality not yet implemented"
    fi
    
    return 0
}

###############################################################################
# Status and Info
###############################################################################

show_status() {
    banner "HA AI Workflow Status"
    
    echo ""
    info "Configuration:"
    echo "  Config Dir: ${CONFIG_DIR}"
    echo "  Export Dir: ${EXPORT_DIR}"
    echo "  Import Dir: ${IMPORT_DIR}"
    echo ""
    
    info "Git Status:"
    cd "${CONFIG_DIR}"
    echo "  Current Branch: $(get_current_branch)"
    echo "  Last Commit: $(git log -1 --pretty=format:'%h - %s (%ar)' 2>/dev/null || echo 'No commits')"
    echo ""
    
    info "Recent Exports:"
    if [ -d "${EXPORT_DIR}" ]; then
        ls -lt "${EXPORT_DIR}" | grep '^d' | head -5 | awk '{print "  " $9 " (" $6 " " $7 " " $8 ")"}'
    fi
    echo ""
    
    info "Pending Imports:"
    if [ -d "${IMPORT_DIR}" ]; then
        local count=$(find "${IMPORT_DIR}" -type f 2>/dev/null | wc -l)
        echo "  ${count} file(s) in import directory"
    fi
    echo ""
    
    info "Secrets Backups:"
    if [ -d "${SECRETS_DIR}" ]; then
        ls -lt "${SECRETS_DIR}" | grep secrets_map_ | head -5 | awk '{print "  " $9 " (" $6 " " $7 " " $8 ")"}'
    fi
    echo ""
}

###############################################################################
# Main Script
###############################################################################

show_help() {
    cat << EOF
Home Assistant AI Workflow - Master Script

USAGE:
    $(basename $0) [COMMAND] [OPTIONS]

COMMANDS:
    export              Run full export workflow
    import              Run import workflow for AI-generated configs
    status              Show workflow status and recent activity
    setup               Initial setup (git, dependencies)
    help                Show this help message

OPTIONS:
    --auto              Enable auto-mode (no confirmations)
    --no-strict         Disable strict error handling
    --upload-debug      Enable debug report upload
    -h, --help          Show this help message

EXAMPLES:
    # Initial setup
    $(basename $0) setup

    # Export configuration for AI
    $(basename $0) export

    # Import AI-generated configs
    $(basename $0) import

    # Show status
    $(basename $0) status

    # Fully automated workflow (CI/CD)
    $(basename $0) export --auto
    $(basename $0) import --auto

For more information, see: ${SCRIPT_DIR}/docs/README.md
EOF
}

main() {
    # Parse arguments
    local command=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            export|import|status|setup|help)
                command=$1
                shift
                ;;
            --auto)
                AUTO_MODE=true
                shift
                ;;
            --no-strict)
                STRICT_MODE=false
                set +e
                shift
                ;;
            --upload-debug)
                UPLOAD_DEBUG=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Start logging
    log "INFO" "============================================"
    log "INFO" "HA AI Workflow started: command=${command}"
    log "INFO" "============================================"
    
    # Show banner
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║       Home Assistant AI Workflow Automation System            ║"
    echo "║                  Version 1.0.0                                ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Check dependencies
    if [ "$command" != "help" ] && [ "$command" != "setup" ]; then
        check_dependencies || exit 1
        install_pyyaml || exit 1
    fi
    
    # Execute command
    case $command in
        setup)
            init_git_repo
            ;;
        export)
            run_export
            ;;
        import)
            run_import
            ;;
        status)
            show_status
            ;;
        help|"")
            show_help
            ;;
        *)
            error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        success "Workflow completed successfully"
    else
        error "Workflow failed with exit code: $exit_code"
    fi
    
    log "INFO" "Workflow finished: exit_code=${exit_code}"
    
    exit $exit_code
}

# Run main
main "$@"
