# SSH Password-Based Setup Guide (Putty/SSH)

**For your current Putty/SSH password-based authentication setup**

---

## ⚡ Quick Start (2 minutes)

### 1. Install Dependencies
```bash
# Install Paramiko (Python SSH library for password auth)
pip install paramiko

# Optional: Install sshpass (for alternative password passing)
# Linux: sudo apt-get install sshpass
# macOS: brew install sshpass
```

### 2. Configure Workflow
```bash
# Copy configuration template
cp config/workflow_config.yaml.template config/workflow_config.yaml

# Edit and set SSH configuration
# See section "Configuration" below
```

### 3. Test Connection
```bash
# Test password-based SSH connection
python3 bin/ssh_transfer_password.py \
  --host 192.168.1.100 \
  --user root \
  --port 22 \
  --method interactive \
  --test

# Expected: Will prompt for password, then show "✓ SSH connection successful"
```

✅ Done! Now you can use the workflow.

---

## Configuration

### Option 1: Interactive Password Prompt (Recommended)
```yaml
# config/workflow_config.yaml
ssh:
  enabled: true
  
  # Your Proxmox VM details
  host: "192.168.1.100"
  port: 22
  user: "root"
  
  # Interactive mode - prompts for password when needed
  auth_method: "interactive"
  
  # Docker container settings
  docker:
    enabled: true
    container_name: "homeassistant"
    use_docker_exec: true
```

**Pros:**
- ✓ Password never stored in config file
- ✓ Password never visible in process list
- ✓ Secure - prompts on demand
- ✓ Works with terminal interaction

### Option 2: Paramiko with Stored Password
```yaml
# config/workflow_config.yaml
ssh:
  enabled: true
  
  host: "192.168.1.100"
  port: 22
  user: "root"
  
  # Use Paramiko (pure Python SSH)
  auth_method: "paramiko"
  
  # Store password (⚠️ DO NOT COMMIT THIS FILE TO GIT)
  password: "${SSH_PASSWORD}"  # From environment variable
  
  docker:
    enabled: true
    container_name: "homeassistant"
```

**Before running:**
```bash
export SSH_PASSWORD="your_password"
python3 bin/workflow_orchestrator.py export --source 192.168.1.100
```

### Option 3: sshpass Utility (Fast for Automation)
```yaml
# config/workflow_config.yaml
ssh:
  enabled: true
  
  host: "192.168.1.100"
  port: 22
  user: "root"
  
  # Use sshpass (requires sshpass utility installed)
  auth_method: "sshpass"
  
  # Password from environment variable
  password: "${SSH_PASSWORD}"
  
  docker:
    enabled: true
    container_name: "homeassistant"
```

**Before running:**
```bash
export SSH_PASSWORD="your_password"
python3 bin/workflow_orchestrator.py export --source 192.168.1.100
```

---

## Testing

### Test 1: Basic Connection Test
```bash
# Interactive method (prompts for password)
python3 bin/ssh_transfer_password.py \
  --host 192.168.1.100 \
  --user root \
  --method interactive \
  --test

# Expected output:
# 🔐 Using auth method: interactive
# 🔗 Testing SSH connection...
# ✓ SSH connection successful
```

### Test 2: Execute Remote Command
```bash
# List running Docker containers
python3 bin/ssh_transfer_password.py \
  --host 192.168.1.100 \
  --user root \
  --method interactive \
  --cmd "docker ps"

# Expected: Shows list of containers including homeassistant
```

### Test 3: Docker Container Check
```bash
# Verify Docker container is accessible
python3 bin/ssh_transfer_password.py \
  --host 192.168.1.100 \
  --user root \
  --method interactive \
  --docker \
  --docker-check

# Expected: Shows homeassistant container status
```

### Test 4: Check HA Config Path
```bash
python3 bin/ssh_transfer_password.py \
  --host 192.168.1.100 \
  --user root \
  --method interactive \
  --docker \
  --cmd "docker exec homeassistant ls -la /config | head"

# Expected: Lists files in /config directory
```

---

## Using the Workflow

### Export Configuration from HA
```bash
# Interactive prompt for password
python3 bin/workflow_orchestrator.py export \
  --source 192.168.1.100:/config \
  --output ./ha_export

# When prompted, enter your SSH password
# Configuration files will be downloaded to ./ha_export/
```

### Import Configuration to HA
```bash
# With dry-run first (no changes made)
python3 bin/workflow_orchestrator.py import \
  --source ./ha_config \
  --target /config \
  --dry-run

# If dry-run looks good, do actual import
python3 bin/workflow_orchestrator.py import \
  --source ./ha_config \
  --target /config
```

### Full Pipeline
```bash
# Complete workflow: export → sanitize → generate AI context
python3 bin/workflow_orchestrator.py full \
  --source 192.168.1.100:/config \
  --output ./pipeline_output

# When prompted, enter SSH password
```

---

## Authentication Methods Explained

### Interactive (Recommended for Manual Use)
```bash
python3 ... --method interactive
```
- **How it works:** Prompts for password when needed (like Putty)
- **Best for:** Manual commands, occasional use
- **Security:** Excellent (password only in memory during session)
- **Automation:** Not ideal (can't auto-provide password)

### Paramiko (Best for Automation)
```bash
python3 ... --method paramiko --password "your_password"
export SSH_PASSWORD="your_password"
python3 ... --method paramiko
```
- **How it works:** Uses Python SSH library with password
- **Best for:** Automated scripts, CI/CD pipelines
- **Security:** Good (encrypted SSH channel)
- **Automation:** Excellent (can provide password via environment)

### sshpass (Fast CLI Method)
```bash
export SSH_PASSWORD="your_password"
python3 ... --method sshpass
```
- **How it works:** Injects password into SSH command
- **Best for:** Quick commands, testing
- **Security:** Fair (requires sshpass utility)
- **Automation:** Good (environment variable friendly)

### Key-Based (Best Overall - Recommended Future)
```bash
python3 ... --method key --key ~/.ssh/ha_rsa
```
- **How it works:** Uses SSH key instead of password
- **Best for:** Production, most secure
- **Security:** Excellent (asymmetric encryption)
- **Automation:** Excellent (no password needed)

---

## Troubleshooting

### Issue: "Paramiko not available"
```bash
pip install paramiko
```

### Issue: "sshpass: command not found"
```bash
# Linux
sudo apt-get install sshpass

# macOS
brew install sshpass

# Or just use interactive/paramiko method instead
```

### Issue: "Permission denied (password)"
```bash
# Verify password works manually first
ssh root@192.168.1.100
# (if manual SSH works, but script fails, password may have special characters)

# Test with explicit authentication method
python3 bin/ssh_transfer_password.py \
  --host 192.168.1.100 \
  --user root \
  --method paramiko \
  --test
```

### Issue: "Connection refused"
```bash
# Check SSH is running on VM
ping 192.168.1.100
ssh -v root@192.168.1.100  # Verbose to see what fails
```

### Issue: "Docker: Cannot read from /config"
```bash
# Verify container is running and /config is mounted
python3 bin/ssh_transfer_password.py \
  --host 192.168.1.100 \
  --user root \
  --docker \
  --cmd "docker exec homeassistant ls /config"
```

---

## Security Recommendations

### ✅ DO This
```bash
# Store password in environment variable
export SSH_PASSWORD="my_password"
python3 ... --method paramiko

# Or use interactive (no storage)
python3 ... --method interactive
# (then type password when prompted)

# Use SSH keys when possible (future upgrade)
ssh-keygen -t ed25519 -f ~/.ssh/ha_rsa -N ""
```

### ❌ DON'T Do This
```bash
# Don't hardcode password in script
python3 ... --password "my_password"  # ❌ Visible in command history

# Don't commit config with password
git add config/workflow_config.yaml  # ❌ If password in it

# Don't expose password in logs
python3 ... --password "my_password" 2>&1 | tee log.txt  # ❌ In log file
```

### 🔐 Best Practice
```bash
# Use .bashrc to set environment variable
# Add to ~/.bashrc or ~/.zshrc:
# export SSH_PASSWORD="your_password"

# Source it and use
source ~/.bashrc
python3 bin/workflow_orchestrator.py export
```

Or even better, **migrate to SSH keys**:
```bash
# Generate key (do once)
ssh-keygen -t ed25519 -f ~/.ssh/ha_rsa -N ""

# Copy to VM (using current password)
export SSH_PASSWORD="current_password"
sshpass -e ssh-copy-id -i ~/.ssh/ha_rsa.pub root@192.168.1.100

# Then switch config to use key (no password needed)
# Set auth_method: "key" and key_path: "~/.ssh/ha_rsa"
```

---

## Comparison: Password vs SSH Key

### Password-Based (Your Current Setup)
```
Advantages:
✓ Works immediately with Putty
✓ No key file to manage
✓ Can use same password everywhere

Disadvantages:
✗ Less secure (weaker authentication)
✗ Need to enter/store password
✗ Slower than key auth
✗ Vulnerable to brute force
```

### SSH Key-Based (Recommended Future)
```
Advantages:
✓ More secure (asymmetric encryption)
✓ No password to remember/store
✓ Faster authentication
✓ Can use SSH agent for multiple hosts
✓ Industry standard

Disadvantages:
✗ Need to generate and backup key
✗ Need to copy key to VM
```

---

## Automation Setup

### For Regular Automated Tasks

```bash
# 1. Create a helper script
cat > run_export.sh << 'EOF'
#!/bin/bash
export SSH_PASSWORD="${HA_SSH_PASSWORD}"
python3 bin/workflow_orchestrator.py export \
  --source 192.168.1.100:/config \
  --output ./exports/$(date +%Y%m%d)
EOF

chmod +x run_export.sh

# 2. Run with password from environment
export HA_SSH_PASSWORD="your_password"
./run_export.sh

# 3. Or schedule with cron (store password securely)
# In crontab:
# 0 2 * * * cd /path/to/workflow && export SSH_PASSWORD="..." && ./run_export.sh
```

### For GitHub Actions / CI-CD

```yaml
# .github/workflows/export-ha-config.yml
name: Export HA Config

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily

jobs:
  export:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install paramiko pyyaml
      
      - name: Export HA config
        env:
          SSH_PASSWORD: ${{ secrets.HA_SSH_PASSWORD }}
        run: |
          python3 bin/workflow_orchestrator.py export \
            --source 192.168.1.100:/config \
            --output ./exports
```

---

## Next Steps

1. ✅ Install Paramiko: `pip install paramiko`
2. ✅ Configure `workflow_config.yaml` with your VM details
3. ✅ Test connection: `python3 bin/ssh_transfer_password.py --test`
4. ✅ Run export: `python3 bin/workflow_orchestrator.py export`
5. 📈 (Future) Migrate to SSH keys for better security

---

## Summary

**Your password-based Putty/SSH setup is now fully supported!**

- ✅ Works with interactive password prompts
- ✅ Can automate with environment variables
- ✅ Integrates with Docker containers
- ✅ Full export/import workflow available

**For production use, consider migrating to SSH keys for better security and performance.**

