#!/usr/bin/env bash
# shellcheck shell=bash
# HA AI Gen Workflow Add-on Run Script
# Uses SUPERVISOR_TOKEN for secure HA API access
# Fixed to work without s6-overlay dependency

set -e

# Configuration paths
CONFIG_FILE="/data/options.json"
CONFIG_FILE_FALLBACK="/config/options.json"

# Verbose/debug mode flag (set via environment or config)
DEBUG_MODE="${DEBUG_MODE:-false}"
VERBOSE="${VERBOSE:-false}"

# Color codes for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

log_debug() {
    if [[ "${DEBUG_MODE}" == "true" ]] || [[ "${VERBOSE}" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
    fi
}

# Function to read config with fallback
get_config() {
    local key="$1"
    local default="$2"
    local value=""
    
    log_debug "Reading config key: ${key}"
    
    # Try primary config file
    if [[ -f "${CONFIG_FILE}" ]]; then
        log_debug "Reading from primary config: ${CONFIG_FILE}"
        # Use jq with --arg for safe parameter passing
        value=$(jq -r --arg k "${key}" '.[$k] // empty' "${CONFIG_FILE}" 2>/dev/null || echo "")
    fi
    
    # Fallback to secondary config file
    if [[ -z "${value}" ]] && [[ -f "${CONFIG_FILE_FALLBACK}" ]]; then
        log_debug "Trying fallback config: ${CONFIG_FILE_FALLBACK}"
        value=$(jq -r --arg k "${key}" '.[$k] // empty' "${CONFIG_FILE_FALLBACK}" 2>/dev/null || echo "")
    fi
    
    # Use default if still empty
    if [[ -z "${value}" ]] || [[ "${value}" == "null" ]]; then
        log_debug "Using default value for ${key}: ${default}"
        value="${default}"
    fi
    
    echo "${value}"
}

# Failsafe: Check if jq is available (required for JSON config parsing)
if ! command -v jq &> /dev/null; then
    log_warning "jq is not installed - installing now..."
    if ! apk add --no-cache jq; then
        log_error "Failed to install jq. Cannot proceed without JSON parser."
        log_error "This add-on requires Alpine Linux with apk package manager."
        exit 1
    fi
    log_info "jq installed successfully"
    
    # Verify jq is now available
    if ! command -v jq &> /dev/null; then
        log_error "jq installation appeared successful but command not found"
        log_error "This is a critical error - cannot parse configuration"
        exit 1
    fi
fi

# Failsafe: Check if config file exists
if [[ ! -f "${CONFIG_FILE}" ]] && [[ ! -f "${CONFIG_FILE_FALLBACK}" ]]; then
    log_warning "No config file found at ${CONFIG_FILE} or ${CONFIG_FILE_FALLBACK}"
    log_warning "Using default configuration values"
fi

log_info "=========================================="
log_info "HA AI Gen Workflow Add-on Starting"
log_info "=========================================="
log_debug "Debug mode: ${DEBUG_MODE}"
log_debug "Verbose mode: ${VERBOSE}"
log_debug "Config file: ${CONFIG_FILE}"

# Read debug/verbose mode from config if not already set via environment
if [[ "${DEBUG_MODE}" == "false" ]]; then
    DEBUG_MODE=$(get_config 'debug_mode' 'false')
fi
if [[ "${VERBOSE}" == "false" ]]; then
    VERBOSE=$(get_config 'verbose' 'false')
fi

log_debug "Debug mode (after config): ${DEBUG_MODE}"
log_debug "Verbose mode (after config): ${VERBOSE}"

# Read configuration with fallbacks
EXPORT_PATH=$(get_config 'export_path' '/config/ai_exports')
IMPORT_PATH=$(get_config 'import_path' '/config/ai_imports')
SECRETS_PATH=$(get_config 'secrets_path' '/config/ai_secrets')
SSH_ENABLED=$(get_config 'ssh_enabled' 'false')
SSH_HOST=$(get_config 'ssh_host' '')
SSH_USER=$(get_config 'ssh_user' 'root')
SSH_PORT=$(get_config 'ssh_port' '22')
SSH_KEY_PATH=$(get_config 'ssh_key_path' '')
REMOTE_CONFIG_PATH=$(get_config 'remote_config_path' '/config')

# Failsafe: Create necessary directories with error handling
log_info "Creating necessary directories..."
for dir in "${EXPORT_PATH}" "${IMPORT_PATH}" "${SECRETS_PATH}"; do
    if ! mkdir -p "${dir}" 2>/dev/null; then
        log_warning "Failed to create directory: ${dir}"
        # Try with sudo if available (uncommon in containers but worth trying)
        if command -v sudo &> /dev/null; then
            log_debug "Attempting to create with elevated permissions..."
            if sudo mkdir -p "${dir}" 2>/dev/null; then
                log_debug "Created directory with sudo: ${dir}"
            else
                log_warning "Failed to create directory even with elevated permissions: ${dir}"
                log_warning "Directory may already exist or permissions issue - continuing anyway"
            fi
        else
            log_warning "sudo not available - continuing anyway"
            log_debug "Directory may already exist or be created later"
        fi
    else
        log_debug "Created directory: ${dir}"
    fi
done

log_info "Configuration loaded successfully:"
log_info "  Export path: ${EXPORT_PATH}"
log_info "  Import path: ${IMPORT_PATH}"
log_info "  Secrets path: ${SECRETS_PATH}"
log_debug "  SSH enabled: ${SSH_ENABLED}"
log_debug "  SSH host: ${SSH_HOST}"
log_debug "  SSH user: ${SSH_USER}"
log_debug "  SSH port: ${SSH_PORT}"

# Verify SUPERVISOR_TOKEN is available for secure API access
if [[ -n "${SUPERVISOR_TOKEN:-}" ]]; then
    log_info "SUPERVISOR_TOKEN available - HA API access enabled"
    log_debug "Token length: ${#SUPERVISOR_TOKEN}"
else
    log_warning "SUPERVISOR_TOKEN not available - some features may be limited"
    log_warning "This is expected in non-addon environments"
fi

# Test Home Assistant API connectivity (optional, for diagnostics)
test_ha_api() {
    local response
    local retry_count=0
    local max_retries=3
    
    log_debug "Testing Home Assistant API connectivity..."
    
    while [[ ${retry_count} -lt ${max_retries} ]]; do
        response=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
            "http://supervisor/core/api/config" 2>/dev/null || echo "000")
        
        if [[ "${response}" == "200" ]]; then
            log_info "Home Assistant API connection verified (HTTP ${response})"
            return 0
        else
            retry_count=$((retry_count + 1))
            log_debug "API test attempt ${retry_count}/${max_retries} - Status: ${response}"
            
            if [[ ${retry_count} -lt ${max_retries} ]]; then
                log_debug "Waiting 2 seconds before retry..."
                sleep 2
            fi
        fi
    done
    
    log_warning "Home Assistant API returned status: ${response} after ${max_retries} attempts"
    return 1
}

# Failsafe: Test API if token is available
if [[ -n "${SUPERVISOR_TOKEN:-}" ]]; then
    if test_ha_api; then
        log_info "API connectivity check passed"
    else
        log_warning "API test failed - continuing anyway as this is not critical"
        log_info "The add-on will function but some features may be limited"
    fi
else
    log_debug "Skipping API test - no SUPERVISOR_TOKEN available"
fi

# Generate workflow configuration with HA API settings
log_info "Generating workflow configuration..."
log_debug "Writing config to /app/workflow_config.yaml"

# Verify /app directory exists and is writable
if [[ ! -d "/app" ]]; then
    log_error "/app directory does not exist - this is unexpected"
    log_error "Cannot proceed without application directory"
    exit 1
fi

if [[ ! -w "/app" ]]; then
    log_error "/app directory is not writable"
    log_error "Cannot write configuration file"
    exit 1
fi

if ! cat > /app/workflow_config.yaml << EOF
paths:
  export_dir: "${EXPORT_PATH}"
  import_dir: "${IMPORT_PATH}"
  secrets_dir: "${SECRETS_PATH}"
  backup_dir: "${EXPORT_PATH}/backups"

ssh:
  enabled: ${SSH_ENABLED}
  host: "${SSH_HOST}"
  user: "${SSH_USER}"
  port: ${SSH_PORT}
  key_path: "${SSH_KEY_PATH}"
  remote_config_path: "${REMOTE_CONFIG_PATH}"

secrets:
  label_prefix: "HA_SECRET"
  auto_restore: true

export:
  include_patterns:
    - "*.yaml"
    - "*.yml"
    - "*.json"
  exclude_patterns:
    - "*.log"
    - "*.db"
    - "*.db-wal"
    - "*.db-shm"
    - "__pycache__"
    - ".git"

# Home Assistant API configuration (for add-on use)
homeassistant:
  api_url: "http://supervisor/core/api"
  supervisor_url: "http://supervisor"
  # Token is provided via SUPERVISOR_TOKEN environment variable
  # Never store tokens in config files
EOF
then
    log_error "Failed to write workflow configuration file"
    log_error "This is a critical error - cannot proceed"
    exit 1
fi

log_info "Workflow configuration generated successfully"

# Get ingress information for Streamlit
# Fallback mechanism: try multiple methods to get ingress URL
log_info "Determining ingress URL..."

INGRESS_URL=""
INGRESS_ENTRY=""

# Method 1: Try reading from environment variable (set by Home Assistant)
if [[ -n "${INGRESS_ENTRY:-}" ]]; then
    INGRESS_URL="${INGRESS_ENTRY}"
    log_debug "Ingress URL from INGRESS_ENTRY: ${INGRESS_URL}"
fi

# Method 2: Try reading from supervisor API
if [[ -z "${INGRESS_URL}" ]] && [[ -n "${SUPERVISOR_TOKEN:-}" ]]; then
    log_debug "Attempting to get ingress URL from supervisor API..."
    INGRESS_URL=$(curl -s -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
        "http://supervisor/addons/self/info" 2>/dev/null | \
        jq -r '.data.ingress_url // empty' 2>/dev/null || echo "")
    
    if [[ -n "${INGRESS_URL}" ]]; then
        log_debug "Ingress URL from supervisor API: ${INGRESS_URL}"
    fi
fi

# Method 3: Fallback to default ingress path
if [[ -z "${INGRESS_URL}" ]]; then
    # Try to read slug file, suppress error if it doesn't exist
    local_slug='ha_ai_gen_workflow'
    if [[ -f "/data/slug" ]]; then
        local_slug=$(cat /data/slug 2>/dev/null || echo 'ha_ai_gen_workflow')
    fi
    INGRESS_URL="/api/hassio_ingress/${local_slug}"
    log_warning "Using fallback ingress URL: ${INGRESS_URL}"
fi

log_info "Ingress URL configured: ${INGRESS_URL}"

# Export environment variables for Python scripts to use
# SUPERVISOR_TOKEN is already available from the container environment
log_info "Setting up environment variables..."
export HA_API_URL="http://supervisor/core/api"
export HA_SUPERVISOR_URL="http://supervisor"
export HA_CONFIG_PATH="/config"

log_debug "Environment variables set:"
log_debug "  HA_API_URL=${HA_API_URL}"
log_debug "  HA_SUPERVISOR_URL=${HA_SUPERVISOR_URL}"
log_debug "  HA_CONFIG_PATH=${HA_CONFIG_PATH}"

# Failsafe: Check if Streamlit is available
log_info "Verifying Streamlit installation..."
if ! command -v streamlit &> /dev/null; then
    log_warning "Streamlit is not installed"
    log_info "Attempting to install Streamlit..."
    
    # Check if pip3 is available
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not available - cannot install Streamlit"
        log_error "This is a critical error - the add-on cannot function without Streamlit"
        exit 1
    fi
    
    if pip3 install --no-cache-dir streamlit; then
        log_info "Streamlit installed successfully"
    else
        log_error "Failed to install Streamlit - cannot start the application"
        log_error "Check the logs above for pip3 error messages"
        exit 1
    fi
fi

log_info "Streamlit version: $(streamlit --version 2>&1 || echo 'unknown')"

# Failsafe: Check if workflow_gui.py exists
if [[ ! -f "/app/bin/workflow_gui.py" ]]; then
    log_error "workflow_gui.py not found at /app/bin/workflow_gui.py"
    log_error "Cannot start the application"
    exit 1
fi

log_info "=========================================="
log_info "Starting Streamlit GUI..."
log_info "=========================================="
log_info "Access the UI via Home Assistant sidebar"
log_info "Or navigate to: ${INGRESS_URL}"
log_info ""

# Prepare Streamlit command with fallback for base URL path
STREAMLIT_CMD=(
    streamlit run /app/bin/workflow_gui.py
    --server.port=8501
    --server.address=0.0.0.0
    # Security settings disabled for Home Assistant ingress compatibility
    # CORS and XSRF protection are handled by Home Assistant's ingress proxy
    --server.enableCORS=false
    --server.enableXsrfProtection=false
    --server.headless=true
    --browser.gatherUsageStats=false
    --theme.base=dark
)

# Only add baseUrlPath if ingress URL is properly set and not root
if [[ -n "${INGRESS_URL}" ]] && [[ "${INGRESS_URL}" != "/" ]]; then
    # Basic validation: ensure URL doesn't contain obvious problematic characters
    if [[ "${INGRESS_URL}" =~ [[:space:]] ]]; then
        log_warning "Ingress URL contains spaces, which may cause issues: '${INGRESS_URL}'"
    fi
    STREAMLIT_CMD+=(--server.baseUrlPath="${INGRESS_URL}")
    log_debug "Using baseUrlPath: ${INGRESS_URL}"
fi

# Add verbose logging if debug mode is enabled
if [[ "${DEBUG_MODE}" == "true" ]] || [[ "${VERBOSE}" == "true" ]]; then
    STREAMLIT_CMD+=(--logger.level=debug)
    log_debug "Debug logging enabled for Streamlit"
fi

log_debug "Streamlit command: ${STREAMLIT_CMD[*]}"

# Run Streamlit with exec (replaces current process)
log_info "Executing Streamlit..."
exec "${STREAMLIT_CMD[@]}"
