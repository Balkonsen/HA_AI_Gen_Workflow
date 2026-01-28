#!/usr/bin/with-contenv bashio
# shellcheck shell=bash
# HA AI Gen Workflow Add-on Run Script
# Uses SUPERVISOR_TOKEN for secure HA API access

set -e

EXPORT_PATH=$(bashio::config 'export_path')
IMPORT_PATH=$(bashio::config 'import_path')
SECRETS_PATH=$(bashio::config 'secrets_path')
SSH_ENABLED=$(bashio::config 'ssh_enabled')
SSH_HOST=$(bashio::config 'ssh_host')
SSH_USER=$(bashio::config 'ssh_user')
SSH_PORT=$(bashio::config 'ssh_port')
SSH_KEY_PATH=$(bashio::config 'ssh_key_path')
REMOTE_CONFIG_PATH=$(bashio::config 'remote_config_path')

# Create necessary directories
mkdir -p "${EXPORT_PATH}" "${IMPORT_PATH}" "${SECRETS_PATH}"

bashio::log.info "Starting HA AI Gen Workflow..."
bashio::log.info "Export path: ${EXPORT_PATH}"
bashio::log.info "Import path: ${IMPORT_PATH}"

# Verify SUPERVISOR_TOKEN is available for secure API access
if [[ -n "${SUPERVISOR_TOKEN:-}" ]]; then
    bashio::log.info "SUPERVISOR_TOKEN available - HA API access enabled"
else
    bashio::log.warning "SUPERVISOR_TOKEN not available - some features may be limited"
fi

# Test Home Assistant API connectivity (optional, for diagnostics)
test_ha_api() {
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
        "http://supervisor/core/api/config" 2>/dev/null || echo "000")
    
    if [[ "${response}" == "200" ]]; then
        bashio::log.info "Home Assistant API connection verified"
        return 0
    else
        bashio::log.warning "Home Assistant API returned status: ${response}"
        return 1
    fi
}

# Test API if token is available
if [[ -n "${SUPERVISOR_TOKEN:-}" ]]; then
    test_ha_api || bashio::log.warning "API test failed, continuing anyway..."
fi

# Generate workflow configuration with HA API settings
cat > /app/workflow_config.yaml << EOF
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

# Get ingress information for Streamlit
INGRESS_URL=$(bashio::addon.ingress_url)

bashio::log.info "Ingress URL: ${INGRESS_URL}"
bashio::log.info "Starting Streamlit GUI..."

# Export environment variables for Python scripts to use
# SUPERVISOR_TOKEN is already available from the container environment
export HA_API_URL="http://supervisor/core/api"
export HA_SUPERVISOR_URL="http://supervisor"
export HA_CONFIG_PATH="/config"

# Run Streamlit with proper configuration for ingress
exec streamlit run /app/bin/workflow_gui.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.baseUrlPath="${INGRESS_URL}" \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --theme.base=dark
