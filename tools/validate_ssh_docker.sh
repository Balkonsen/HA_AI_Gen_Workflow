#!/bin/bash
#
# SSH Connection Validator for Docker-based Home Assistant
# Tests SSH connectivity to Proxmox/HA VM and Docker container access
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SSH_HOST="${1:-}"
SSH_USER="${2:-root}"
SSH_PORT="${3:-22}"
SSH_KEY="${4:-$HOME/.ssh/id_rsa}"
CONTAINER_NAME="${5:-homeassistant}"

# Print helper functions
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Usage
if [ -z "$SSH_HOST" ]; then
    echo "Usage: $0 <ssh_host> [ssh_user] [ssh_port] [ssh_key] [container_name]"
    echo ""
    echo "Examples:"
    echo "  $0 192.168.1.100"
    echo "  $0 192.168.1.100 root 22 ~/.ssh/id_rsa homeassistant"
    echo "  $0 homeassistant.local root 22 ~/.ssh/id_rsa homeassistant"
    exit 1
fi

# Expand home directory in SSH key path
SSH_KEY="${SSH_KEY/#\~/$HOME}"

print_header "SSH Connection Validation"
echo "Host: $SSH_HOST"
echo "User: $SSH_USER"
echo "Port: $SSH_PORT"
echo "Key: $SSH_KEY"
echo "Container: $CONTAINER_NAME"
echo ""

# ============================================================================
# PHASE 1: Local Prerequisite Checks
# ============================================================================
print_header "PHASE 1: Local Prerequisites"

# Check 1: SSH key exists
echo -n "Checking SSH key exists... "
if [ -f "$SSH_KEY" ]; then
    print_success "SSH key found"
else
    print_error "SSH key not found at $SSH_KEY"
    exit 1
fi

# Check 2: SSH key permissions
echo -n "Checking SSH key permissions... "
SSH_KEY_PERMS=$(stat -c '%a' "$SSH_KEY" 2>/dev/null || stat -f '%OLp' "$SSH_KEY" | tail -c 4)
if [ "$SSH_KEY_PERMS" = "600" ] || [ "$SSH_KEY_PERMS" = "0600" ]; then
    print_success "SSH key permissions correct (600)"
else
    print_warning "SSH key permissions are $SSH_KEY_PERMS (should be 600)"
    echo "  Fixing permissions..."
    chmod 600 "$SSH_KEY"
    print_success "SSH key permissions fixed"
fi

# Check 3: SSH key is readable
echo -n "Checking SSH key is readable... "
if [ -r "$SSH_KEY" ]; then
    print_success "SSH key is readable"
else
    print_error "SSH key is not readable"
    exit 1
fi

# Check 4: SSH client available
echo -n "Checking SSH client available... "
if command -v ssh &> /dev/null; then
    SSH_VERSION=$(ssh -V 2>&1 | head -n1)
    print_success "SSH client available: $SSH_VERSION"
else
    print_error "SSH client not found"
    exit 1
fi

# Check 5: SSH key type
echo -n "Checking SSH key format... "
if ssh-keygen -l -f "$SSH_KEY" &> /dev/null; then
    KEY_INFO=$(ssh-keygen -l -f "$SSH_KEY")
    print_success "SSH key format valid"
    echo "  $KEY_INFO"
else
    print_error "SSH key format invalid"
    exit 1
fi

echo ""

# ============================================================================
# PHASE 2: Network Connectivity
# ============================================================================
print_header "PHASE 2: Network Connectivity"

# Check 1: Host is resolvable
echo -n "Resolving hostname... "
if HOST_IP=$(getent hosts "$SSH_HOST" 2>/dev/null | awk '{print $1}' | head -1); then
    if [ -z "$HOST_IP" ]; then
        HOST_IP="$SSH_HOST"
    fi
    print_success "Host resolves to $HOST_IP"
else
    print_error "Cannot resolve hostname $SSH_HOST"
    exit 1
fi

# Check 2: Host is reachable (ping)
echo -n "Pinging host... "
if ping -c 1 -W 2 "$SSH_HOST" &> /dev/null; then
    print_success "Host is reachable"
else
    print_warning "Host may not be reachable (ping failed)"
fi

# Check 3: SSH port is open
echo -n "Checking SSH port ($SSH_PORT) is open... "
if command -v nc &> /dev/null; then
    if nc -z -w 2 "$SSH_HOST" "$SSH_PORT" &> /dev/null; then
        print_success "SSH port is open"
    else
        print_error "SSH port is not open or unreachable"
        exit 1
    fi
elif command -v timeout &> /dev/null; then
    if (timeout 2 bash -c "echo > /dev/tcp/$SSH_HOST/$SSH_PORT" 2>/dev/null); then
        print_success "SSH port is open"
    else
        print_error "SSH port is not open or unreachable"
        exit 1
    fi
else
    print_warning "Cannot verify SSH port (nc/timeout not available)"
fi

echo ""

# ============================================================================
# PHASE 3: SSH Authentication & Remote Access
# ============================================================================
print_header "PHASE 3: SSH Authentication"

# Test SSH connection
echo -n "Testing SSH connection... "
if ssh -i "$SSH_KEY" -p "$SSH_PORT" \
    -o StrictHostKeyChecking=accept-new \
    -o BatchMode=yes \
    -o ConnectTimeout=10 \
    "$SSH_USER@$SSH_HOST" \
    "echo 'SSH connection successful'" &> /dev/null; then
    print_success "SSH connection successful"
else
    print_error "SSH connection failed"
    echo ""
    echo "Attempting detailed diagnosis..."
    ssh -i "$SSH_KEY" -p "$SSH_PORT" \
        -o StrictHostKeyChecking=accept-new \
        "$SSH_USER@$SSH_HOST" \
        "echo 'test'" 2>&1 || true
    exit 1
fi

# Check SSH user home directory
echo -n "Checking user home directory... "
if HOME_DIR=$(ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" "echo \$HOME"); then
    print_success "User home directory: $HOME_DIR"
else
    print_error "Cannot determine home directory"
fi

# Check authorized_keys
echo -n "Checking authorized_keys... "
if ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
    "[ -f .ssh/authorized_keys ] && echo 'exists' || echo 'missing'" &> /dev/null; then
    print_success "authorized_keys file exists"
else
    print_warning "authorized_keys file may not exist"
fi

echo ""

# ============================================================================
# PHASE 4: Docker Container Access
# ============================================================================
print_header "PHASE 4: Docker Container Access"

# Check 1: Docker is installed
echo -n "Checking Docker installation... "
if ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
    "command -v docker >/dev/null 2>&1"; then
    DOCKER_VERSION=$(ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" "docker --version")
    print_success "Docker is installed: $DOCKER_VERSION"
else
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check 2: Docker daemon is running
echo -n "Checking Docker daemon... "
if ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
    "docker ps >/dev/null 2>&1"; then
    print_success "Docker daemon is running"
else
    print_error "Docker daemon is not running or not accessible"
    exit 1
fi

# Check 3: Container exists
echo -n "Checking container '$CONTAINER_NAME'... "
if CONTAINER_ID=$(ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
    "docker ps -aq --filter name=$CONTAINER_NAME | head -1"); then
    if [ -z "$CONTAINER_ID" ]; then
        print_warning "Container not found or not running"
        # List available containers
        echo "  Available containers:"
        ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
            "docker ps --format 'table {{.Names}}\t{{.Status}}'" | head -5 || true
    else
        print_success "Container found: $CONTAINER_ID"
    fi
else
    print_error "Cannot query container list"
fi

# Check 4: Container is running
echo -n "Checking container status... "
if CONTAINER_STATUS=$(ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
    "docker inspect -f '{{.State.Status}}' $CONTAINER_NAME 2>/dev/null"); then
    if [ "$CONTAINER_STATUS" = "running" ]; then
        print_success "Container is running"
    else
        print_warning "Container status is: $CONTAINER_STATUS"
    fi
else
    print_error "Cannot check container status"
fi

# Check 5: Config directory exists in container
echo -n "Checking /config path in container... "
if ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
    "docker exec $CONTAINER_NAME test -d /config 2>/dev/null"; then
    print_success "/config directory exists in container"
else
    print_error "/config directory not found in container"
    exit 1
fi

# Check 6: Can read config files
echo -n "Checking config file access... "
if CONFIG_FILES=$(ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
    "docker exec $CONTAINER_NAME ls -la /config | head -5"); then
    print_success "Can access config files"
    echo "  Sample files:"
    echo "$CONFIG_FILES" | sed 's/^/    /' || true
else
    print_error "Cannot access config files"
fi

echo ""

# ============================================================================
# PHASE 5: File Transfer Capability
# ============================================================================
print_header "PHASE 5: File Transfer Capability"

# Check rsync availability
echo -n "Checking rsync availability (optimal)... "
if ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
    "command -v rsync >/dev/null 2>&1"; then
    print_success "rsync available (will be used for transfers)"
else
    print_info "rsync not available (will use SCP as fallback)"
fi

# Check SCP availability
echo -n "Checking SCP availability (fallback)... "
if ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
    "command -v scp >/dev/null 2>&1"; then
    print_success "SCP available"
else
    print_warning "SCP not available (file transfers will be limited)"
fi

echo ""

# ============================================================================
# PHASE 6: Home Assistant Detection
# ============================================================================
print_header "PHASE 6: Home Assistant Detection"

# Check HA command availability
echo -n "Checking 'ha' command (HA OS)... "
if ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
    "command -v ha >/dev/null 2>&1"; then
    HA_VERSION=$(ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
        "ha --version 2>/dev/null" || echo "unknown")
    print_success "Home Assistant OS detected: $HA_VERSION"
else
    print_info "Home Assistant OS not detected (likely Docker-based)"
fi

# Check HA config validity
echo -n "Checking Home Assistant config... "
if ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
    "docker exec $CONTAINER_NAME test -f /config/configuration.yaml 2>/dev/null"; then
    print_success "configuration.yaml exists"
    CONFIG_SIZE=$(ssh -i "$SSH_KEY" -p "$SSH_PORT" -q "$SSH_USER@$SSH_HOST" \
        "docker exec $CONTAINER_NAME wc -l /config/configuration.yaml 2>/dev/null | awk '{print \$1}'")
    echo "  Config file size: ~$CONFIG_SIZE lines"
else
    print_warning "configuration.yaml not found in expected location"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================
print_header "Validation Summary"
print_success "All SSH and Docker connectivity checks passed!"
echo ""
echo "You can now use:"
echo "  - Export: python3 bin/ssh_transfer_enhanced.py export ..."
echo "  - Import: python3 bin/ssh_transfer_enhanced.py import ..."
echo ""
echo "Configuration to add to workflow_config.yaml:"
cat << EOF
ssh:
  enabled: true
  host: "$SSH_HOST"
  port: $SSH_PORT
  user: "$SSH_USER"
  key_path: "$SSH_KEY"
  remote_config_path: "/config"
  docker:
    enabled: true
    container_name: "$CONTAINER_NAME"
    use_docker_exec: true
    healthcheck_timeout: 30
EOF

echo ""
print_success "Validation complete!"
