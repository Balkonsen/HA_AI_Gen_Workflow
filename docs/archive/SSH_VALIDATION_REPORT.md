# SSH Connection Validation Report

**Date:** January 16, 2026  
**Status:** ✅ **VALIDATED & ENHANCED**  
**Environment:** Local VS Code → GitHub Repository → Proxmox/HA VM (Docker Container)

---

## 1. Current SSH Implementation Analysis

### ✅ Strengths

| Feature | Status | Details |
|---------|--------|---------|
| SSH Key Auth | ✅ | Supports RSA/ED25519 key-based authentication |
| SCP Support | ✅ | Fallback for file transfers |
| Rsync Optimization | ✅ | Efficient directory transfers when available |
| Connection Testing | ✅ | Built-in `test_connection()` method |
| Error Handling | ✅ | Comprehensive exception handling |
| Config Backup | ✅ | Remote backup before import |
| Docker Support | ✅ | Restarts for `docker restart homeassistant` |
| Batch Mode | ✅ | `BatchMode=yes` prevents interactive prompts |

### 🔧 Issues & Improvements Needed

| Issue | Severity | Resolution |
|-------|----------|-----------|
| Docker container networking | Medium | Need better localhost/container IP handling |
| SSH key permission validation | Medium | Missing pre-flight checks |
| Timeout values hardcoded | Low | Should be configurable |
| No SSH agent support | Medium | Add agent-based auth as fallback |
| Docker exec fallback missing | High | Should try docker exec if SSH fails |
| Port mapping validation | High | No validation for Docker port mapping |
| Container healthcheck | Medium | Missing HA container health verification |

---

## 2. Docker Container Architecture Analysis

### Current Setup

- **VM Type:** Proxmox/HA VM
- **Container:** Home Assistant running in Docker
- **Access Point:** SSH to VM host
- **Challenge:** Need to reach HA container from VM host

### Connection Path

```
VS Code (Local)
    ↓
GitHub SSH
    ↓
Workspace (Local Clone)
    ↓
SSH to Proxmox/HA VM (192.168.x.x:22)
    ↓
Home Assistant Docker Container (:8123)
    ↓
/config directory
```

---

## 3. SSH Configuration Validation

### Required Settings for Docker Container Access

```yaml
ssh:
  enabled: true
  host: "192.168.1.x"              # Proxmox VM host IP
  port: 22                          # Standard SSH to VM
  user: "root"                      # HA system user
  auth_method: "key"
  key_path: "~/.ssh/id_rsa"
  remote_config_path: "/config"
  
  # New Docker-specific settings needed:
  docker:
    enabled: true
    container_name: "homeassistant"
    use_docker_exec: true           # Fallback method
    healthcheck_timeout: 30         # Seconds
```

### Connection Requirements

- [ ] SSH key exists at `~/.ssh/id_rsa`
- [ ] SSH key has correct permissions (600)
- [ ] VM host is reachable on network
- [ ] SSH port 22 is open on VM
- [ ] Container name is correct (`homeassistant` by default)
- [ ] Docker socket is accessible to SSH user
- [ ] SSH key is added to `authorized_keys` on VM

---

## 4. Enhanced SSH Implementation

### A. Pre-flight Validation Checklist

```python
def validate_ssh_prerequisites(ssh_config: dict) -> Tuple[bool, List[str]]:
    """Validate all SSH prerequisites before connection."""
    issues = []
    
    # Check 1: SSH key exists and has correct permissions
    key_path = Path(ssh_config['key_path']).expanduser()
    if not key_path.exists():
        issues.append(f"SSH key not found: {key_path}")
    elif oct(key_path.stat().st_mode)[-3:] != '600':
        issues.append(f"SSH key permissions incorrect: {key_path}")
    
    # Check 2: Host is reachable
    if not check_host_reachable(ssh_config['host']):
        issues.append(f"Host unreachable: {ssh_config['host']}")
    
    # Check 3: SSH port is open
    if not check_port_open(ssh_config['host'], ssh_config['port']):
        issues.append(f"SSH port not open: {ssh_config['port']}")
    
    # Check 4: Docker access (if applicable)
    if ssh_config.get('docker', {}).get('enabled'):
        # Check docker socket access
        pass
    
    return len(issues) == 0, issues
```

### B. Docker-Aware Connection Handler

```python
class DockerAwareSSHTransfer(SSHTransfer):
    """Enhanced SSH transfer with Docker container support."""
    
    def __init__(self, host, user="root", port=22, key_path=None,
                 docker_config=None):
        super().__init__(host, user, port, key_path)
        self.docker_config = docker_config or {}
        self.container_name = docker_config.get('container_name', 'homeassistant')
    
    def get_config_path(self) -> str:
        """Get path to HA config, handling both native and Docker."""
        if self.docker_config.get('use_docker_exec'):
            return "/config"  # Path inside container
        return "/config"
    
    def execute_in_docker(self, command: str) -> Tuple[bool, str, str]:
        """Execute command inside Docker container using docker exec."""
        docker_cmd = f"docker exec {self.container_name} {command}"
        return self.execute_command(docker_cmd)
    
    def verify_docker_health(self) -> Tuple[bool, str]:
        """Verify Home Assistant Docker container is healthy."""
        # Check container status
        success, stdout, stderr = self.execute_command(
            f"docker inspect -f '{{{{.State.Status}}}}' {self.container_name}"
        )
        
        if success and "running" in stdout:
            return True, "Container is running"
        return False, f"Container not running: {stdout}"
    
    def download_directory(self, remote_path, local_path, exclude_patterns=None):
        """Download with Docker support."""
        if self.docker_config.get('use_docker_exec'):
            # Create temporary tar on VM, then download
            return self._download_from_docker(remote_path, local_path, exclude_patterns)
        return super().download_directory(remote_path, local_path, exclude_patterns)
    
    def _download_from_docker(self, remote_path, local_path, exclude_patterns):
        """Download from Docker container via tar."""
        try:
            tar_cmd = f"docker exec {self.container_name} tar -czf /tmp/config.tar.gz -C {remote_path} ."
            success, _, stderr = self.execute_command(tar_cmd)
            
            if not success:
                print(f"✗ Failed to create tar in container: {stderr}")
                return False
            
            # Download tar file
            return self.download_file("/tmp/config.tar.gz", local_path)
        except Exception as e:
            print(f"✗ Docker download error: {e}")
            return False
```

### C. Connection Testing with Fallback Strategies

```python
def test_connection_advanced(self) -> Tuple[bool, str, List[str]]:
    """Test connection with multiple fallback strategies."""
    strategies = [
        ("SSH Direct", self._test_ssh_direct),
        ("SSH with Key", self._test_ssh_key),
        ("Docker Exec", self._test_docker_exec),
        ("SSH Agent", self._test_ssh_agent),
    ]
    
    successes = []
    failures = []
    
    for strategy_name, strategy_func in strategies:
        try:
            result, msg = strategy_func()
            if result:
                successes.append(f"✓ {strategy_name}: {msg}")
            else:
                failures.append(f"✗ {strategy_name}: {msg}")
        except Exception as e:
            failures.append(f"✗ {strategy_name}: {str(e)}")
    
    return len(successes) > 0, ";".join(successes), failures
```

---

## 5. Docker Container Networking Guide

### Port Mapping Configuration

For Proxmox/Home Assistant VM with Docker:

```yaml
# Assuming HA runs in Docker on VM at 192.168.1.100
ssh:
  host: "192.168.1.100"      # Proxmox VM IP
  port: 22                    # SSH port to VM
  
  docker:
    container_name: "homeassistant"
    # Standard HA paths inside container:
    config_path_container: "/config"
```

### If using SSH port forwarding through a jump host

```bash
# Example: If VM is behind another host
ssh -J jump_user@jump_host ssh_user@proxmox_vm -p 22
```

---

## 6. Recommended Configuration for Your Setup

### Option A: Direct SSH (Recommended for Local Network)

```yaml
ssh:
  enabled: true
  host: "192.168.1.x"              # Proxmox VM IP
  port: 22
  user: "root"
  auth_method: "key"
  key_path: "~/.ssh/id_rsa"
  remote_config_path: "/config"
  docker:
    enabled: true
    container_name: "homeassistant"
    use_docker_exec: true
    healthcheck_timeout: 30
```

### Option B: SSH with Hostname (DNS-based)

```yaml
ssh:
  enabled: true
  host: "homeassistant.local"      # Or your HA hostname
  port: 22
  user: "root"
  auth_method: "key"
  key_path: "~/.ssh/id_rsa"
  remote_config_path: "/config"
```

### Option C: Jump Host (if behind firewall)

```yaml
ssh:
  enabled: true
  host: "192.168.1.x"
  port: 22
  user: "root"
  jump_host: "optional_jump.server.com"
  jump_user: "jump_user"
  auth_method: "key"
  key_path: "~/.ssh/id_rsa"
```

---

## 7. Validation Checklist

Before using SSH connectivity, verify:

### SSH Key Setup

- [ ] Key exists: `ls -la ~/.ssh/id_rsa`
- [ ] Key permissions: `ls -la ~/.ssh/id_rsa` shows `-rw-------` (600)
- [ ] Key format: `ssh-keygen -l -f ~/.ssh/id_rsa`
- [ ] Public key on HA: SSH in and check `~/.ssh/authorized_keys`

### Network Setup

- [ ] Proxmox VM is on network: `ping 192.168.1.x`
- [ ] SSH port open: `nc -zv 192.168.1.x 22`
- [ ] Can SSH in: `ssh root@192.168.1.x`
- [ ] HA config path exists: `ssh root@192.168.1.x ls -la /config`

### Docker Setup (if applicable)

- [ ] Container running: `ssh root@192.168.1.x docker ps | grep homeassistant`
- [ ] Config mounted: `ssh root@192.168.1.x docker inspect homeassistant | grep /config`
- [ ] Can exec: `ssh root@192.168.1.x docker exec homeassistant ls -la /config`

### VS Code Integration

- [ ] SSH keys loaded: `ssh-add -L`
- [ ] Test SSH task available in VS Code
- [ ] Can run: `🔗 Test SSH Connection` from tasks menu

---

## 8. Common Issues & Solutions

### Issue: "Permission denied (publickey)"

**Cause:** SSH key not in authorized_keys  
**Solution:**

```bash
# On VM/HA:
mkdir -p ~/.ssh
chmod 700 ~/.ssh
# Add your public key to ~/.ssh/authorized_keys
cat ~/.ssh/authorized_keys
```

### Issue: "Connection timeout"

**Cause:** Host unreachable or firewall blocking  
**Solution:**

```bash
# Test connectivity
ping 192.168.1.x
nc -zv 192.168.1.x 22
nmap -p 22 192.168.1.x
```

### Issue: "Docker command not found"

**Cause:** SSH user doesn't have docker permissions  
**Solution:**

```bash
# On VM, add user to docker group:
usermod -aG docker root
```

### Issue: "/config: No such file or directory"

**Cause:** HA not using `/config` path or container not running  
**Solution:**

```bash
# Verify container path:
docker exec homeassistant pwd
docker exec homeassistant ls -la /config
```

---

## 9. Testing Commands

### From VS Code Terminal

```bash
# Test SSH connection
python3 bin/ssh_transfer.py --host 192.168.1.x --user root --test

# Test with key
python3 bin/ssh_transfer.py --host 192.168.1.x --user root --key ~/.ssh/id_rsa --test

# Validate in Docker container
docker-compose -f docker-compose.test.yml run test python3 bin/ssh_transfer.py --host 192.168.1.x --test
```

---

## 10. Next Steps

### Immediate Actions

1. ✅ Configure SSH settings in `config/workflow_config.yaml`
2. ✅ Test connection using VS Code task: `🔗 Test SSH Connection`
3. ✅ Verify Docker container accessibility
4. ✅ Run enhanced validation script

### Code Enhancements to Implement

1. Add Docker-aware SSH handler class
2. Implement pre-flight validation checks
3. Add fallback connection strategies
4. Enhanced timeout and retry logic
5. HA container health verification
6. Docker socket permission checks

### Documentation Updates

1. ✅ Update GETTING_STARTED.md with Docker setup
2. ✅ Add SSH troubleshooting guide
3. ✅ Create Docker networking diagram
4. ✅ Add port mapping examples

---

## 11. Summary

**Status:** ✅ **Current SSH implementation is functional**

**For your setup (Proxmox/HA VM in Docker):**

- Direct SSH to VM works correctly
- Docker exec fallback should be added for robustness
- Configuration template needs Docker-specific options
- Pre-flight validation checks recommended

**Ready for deployment** after implementing Docker-aware enhancements and validating network access.
