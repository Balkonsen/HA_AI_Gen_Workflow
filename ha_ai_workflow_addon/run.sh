#!/usr/bin/env bashio
# shellcheck shell=bash
# HA AI Gen Workflow Add-on Run Script

set -e

# Get configuration from add-on options
CONFIG_PATH=/data/options.json

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

# Generate workflow configuration
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
EOF

# Get ingress information for Streamlit
INGRESS_URL=$(bashio::addon.ingress_url)

bashio::log.info "Ingress URL: ${INGRESS_URL}"
bashio::log.info "Starting Streamlit GUI..."

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
