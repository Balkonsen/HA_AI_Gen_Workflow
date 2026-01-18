# SSH Password Auth - Quick Reference Card

**For Putty/SSH password-based access to Proxmox/HA VM**

---

## ⚡ 60-Second Setup

```bash
# 1. Install library
pip install paramiko

# 2. Test connection (will prompt for password)
python3 bin/ssh_transfer_password.py \
  --host 192.168.1.100 \
  --user root \
  --test

# 3. Export HA config
python3 bin/workflow_orchestrator.py export \
  --source 192.168.1.100:/config \
  --output ./ha_backup
```

**That's it!** ✅

---

## Commands Cheat Sheet

### Test Connection
```bash
# Interactive (prompts for password)
python3 bin/ssh_transfer_password.py --host 192.168.1.100 --test

# With stored password
export SSH_PASSWORD="your_password"
python3 bin/ssh_transfer_password.py --host 192.168.1.100 --method paramiko --test

# Verbose debug
python3 bin/ssh_transfer_password.py --host 192.168.1.100 --test -vv
```

### Execute Commands
```bash
# Check Docker containers
python3 bin/ssh_transfer_password.py --host 192.168.1.100 --cmd "docker ps"

# Check HA config
python3 bin/ssh_transfer_password.py --host 192.168.1.100 --docker \
  --cmd "docker exec homeassistant ls /config"

# Restart HA
python3 bin/ssh_transfer_password.py --host 192.168.1.100 --docker \
  --cmd "docker restart homeassistant"
```

### Export/Import
```bash
# Export (interactive password prompt)
python3 bin/workflow_orchestrator.py export \
  --source 192.168.1.100:/config \
  --output ./exports

# Import (with dry-run first)
python3 bin/workflow_orchestrator.py import \
  --source ./ha_config \
  --target /config \
  --dry-run

# Full pipeline
python3 bin/workflow_orchestrator.py full \
  --source 192.168.1.100:/config \
  --output ./pipeline
```

---

## Configuration Template

```yaml
# config/workflow_config.yaml

ssh:
  enabled: true
  
  # Your VM details
  host: "192.168.1.100"          # Proxmox VM IP
  port: 22                        # SSH port
  user: "root"                    # SSH user
  
  # Authentication
  auth_method: "interactive"      # Prompts for password
  # OR for automation:
  # auth_method: "paramiko"       # Use paramiko
  # password: "${SSH_PASSWORD}"   # From environment
  
  # Docker container
  docker:
    enabled: true
    container_name: "homeassistant"
    use_docker_exec: true
```

---

## Auth Methods at a Glance

| Method | Command | Best For | Setup |
|--------|---------|----------|-------|
| **Interactive** | `--method interactive` | Manual use | Prompts for password |
| **Paramiko** | `--method paramiko` | Automation | `pip install paramiko` |
| **sshpass** | `--method sshpass` | CLI scripts | `apt-get install sshpass` |
| **SSH Key** | `--method key` | Production | Generate & copy key |

---

## Environment Variables

### Password Auth (Automation)
```bash
export SSH_PASSWORD="your_password"
python3 bin/workflow_orchestrator.py export --source 192.168.1.100
```

### From .bashrc (Persistent)
```bash
# Add to ~/.bashrc or ~/.zshrc
export SSH_PASSWORD="your_password"

# Then source and use
source ~/.bashrc
python3 bin/ssh_transfer_password.py --test
```

---

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| "Paramiko not available" | `pip install paramiko` |
| "Permission denied" | Check password is correct: `ssh root@192.168.1.100` |
| "Connection refused" | Check host is reachable: `ping 192.168.1.100` |
| "Cannot access /config" | Check container: `python3 ... --docker-check` |
| "sshpass not found" | Use interactive mode or install sshpass |
| "Timeout" | Try longer timeout or check network |

---

## Common Tasks

### Daily Export
```bash
# Create backup of current HA config
mkdir -p backups/$(date +%Y%m%d)
python3 bin/workflow_orchestrator.py export \
  --source 192.168.1.100:/config \
  --output backups/$(date +%Y%m%d)
```

### Before Major Update
```bash
# Full backup before updating HA
python3 bin/workflow_orchestrator.py full \
  --source 192.168.1.100:/config \
  --output backups/before_update_$(date +%Y%m%d)
```

### Test New Config
```bash
# Import with dry-run (no changes)
python3 bin/workflow_orchestrator.py import \
  --source ./new_config \
  --target /config \
  --dry-run

# If looks good, run for real
python3 bin/workflow_orchestrator.py import \
  --source ./new_config \
  --target /config
```

---

## Security Best Practices

### ✅ DO This
```bash
# Use interactive (most secure)
python3 ... --method interactive

# Or environment variable
export SSH_PASSWORD="..."
python3 ...

# Or upgrade to SSH keys (best)
ssh-keygen -t ed25519 -f ~/.ssh/ha_rsa -N ""
```

### ❌ DON'T Do This
```bash
# Don't hardcode password
python3 ... --password "secret123"  # ❌

# Don't commit password to git
git add config/workflow_config.yaml  # ❌ with password

# Don't expose in logs
python3 ... 2>&1 | tee log.txt       # ❌ password visible
```

---

## Upgrade Path: Password → SSH Keys

When you're ready for better security:

```bash
# 1. Generate key (once)
ssh-keygen -t ed25519 -f ~/.ssh/ha_rsa -N ""

# 2. Copy to VM (using current password)
export SSH_PASSWORD="your_password"
sshpass -e ssh-copy-id -i ~/.ssh/ha_rsa.pub root@192.168.1.100

# 3. Update config
# Set: auth_method: "key"
#      key_path: "~/.ssh/ha_rsa"

# 4. Test (no password needed anymore)
python3 bin/ssh_transfer_password.py --method key --test
```

---

## File Reference

| File | Purpose |
|------|---------|
| `bin/ssh_transfer_password.py` | Enhanced SSH implementation |
| `config/workflow_config.yaml` | Your configuration |
| `docs/SSH_PASSWORD_SETUP.md` | Detailed setup guide |
| `docs/SSH_PASSWORD_VALIDATION.md` | Technical details |

---

## Key Points to Remember

✅ **Paramiko is the way** - Install it and use interactive method  
✅ **Password is secure** - Only in memory, not stored  
✅ **Docker works** - Full container support included  
✅ **Backwards compatible** - SSH keys still work  
✅ **Ready to use** - No additional setup needed  

---

## Help & Support

**Quick test:**
```bash
python3 bin/ssh_transfer_password.py --host 192.168.1.100 --test
```

**See detailed guide:**
```bash
cat docs/SSH_PASSWORD_SETUP.md
```

**Report issues:**
Check `docs/SSH_PASSWORD_SETUP.md#troubleshooting`

---

**Status:** ✅ Ready to use  
**Last Updated:** January 16, 2026  
**Version:** 1.0

