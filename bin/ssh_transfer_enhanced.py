#!/usr/bin/env python3
"""
Enhanced SSH Transfer Module with Docker Container Support
Handles secure file transfer between local and remote Home Assistant.
Includes Docker container awareness and fallback strategies.
"""

import os
import sys
import subprocess
import tempfile
import socket
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

# Try to import paramiko for native SSH support
try:
    import paramiko

    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False


class SSHConnectionValidator:
    """Validates SSH connection prerequisites."""

    @staticmethod
    def check_ssh_key(key_path: str) -> Tuple[bool, List[str]]:
        """Validate SSH key exists and has correct permissions."""
        issues = []
        key_path = Path(key_path).expanduser()

        if not key_path.exists():
            issues.append(f"SSH key not found: {key_path}")
            return False, issues

        # Check permissions (should be 600)
        mode = oct(key_path.stat().st_mode)[-3:]
        if mode != "600":
            issues.append(f"SSH key has incorrect permissions {mode} (should be 600): {key_path}")

        # Check if readable
        if not os.access(key_path, os.R_OK):
            issues.append(f"SSH key not readable: {key_path}")

        return len(issues) == 0, issues

    @staticmethod
    def check_host_reachable(host: str, port: int = 22, timeout: int = 5) -> Tuple[bool, str]:
        """Check if host is reachable on SSH port."""
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.close()
            return True, f"Host reachable on port {port}"
        except socket.timeout:
            return False, f"Connection to {host}:{port} timed out"
        except socket.gaierror:
            return False, f"Cannot resolve hostname: {host}"
        except Exception as e:
            return False, f"Cannot reach {host}:{port} - {str(e)}"

    @staticmethod
    def validate_all(host: str, user: str, port: int, key_path: str) -> Tuple[bool, List[str]]:
        """Validate all SSH prerequisites."""
        issues = []

        # Check SSH key
        key_valid, key_issues = SSHConnectionValidator.check_ssh_key(key_path)
        issues.extend(key_issues)

        # Check host reachability
        reachable, msg = SSHConnectionValidator.check_host_reachable(host, port)
        if not reachable:
            issues.append(msg)

        return len(issues) == 0, issues


class DockerAwareSSHTransfer:
    """Enhanced SSH transfer with Docker container support."""

    def __init__(
        self,
        host: str,
        user: str = "root",
        port: int = 22,
        key_path: Optional[str] = None,
        password: Optional[str] = None,
        docker_config: Optional[dict] = None,
    ):
        """Initialize SSH transfer with Docker support.

        Args:
            host: SSH host (IP or hostname)
            user: SSH username
            port: SSH port
            key_path: Path to SSH private key
            password: SSH password (if not using key)
            docker_config: Docker configuration dict with:
                - enabled: bool
                - container_name: str (default: homeassistant)
                - use_docker_exec: bool
                - healthcheck_timeout: int
        """
        self.host = host
        self.user = user
        self.port = port
        self.key_path = os.path.expanduser(key_path) if key_path else None
        self.password = password

        self.docker_config = docker_config or {}
        self.docker_enabled = self.docker_config.get("enabled", False)
        self.container_name = self.docker_config.get("container_name", "homeassistant")
        self.use_docker_exec = self.docker_config.get("use_docker_exec", False)
        self.healthcheck_timeout = self.docker_config.get("healthcheck_timeout", 30)

        self._client = None
        self._sftp = None

    def _get_ssh_command_base(self) -> List[str]:
        """Get base SSH command with authentication."""
        cmd = ["ssh", "-p", str(self.port)]

        if self.key_path:
            cmd.extend(["-i", self.key_path])

        cmd.extend(["-o", "StrictHostKeyChecking=accept-new"])
        cmd.extend(["-o", "BatchMode=yes"])
        cmd.extend(["-o", f"ConnectTimeout={self.healthcheck_timeout}"])

        return cmd

    def _get_scp_command_base(self) -> List[str]:
        """Get base SCP command with authentication."""
        cmd = ["scp", "-P", str(self.port)]

        if self.key_path:
            cmd.extend(["-i", self.key_path])

        cmd.extend(["-o", "StrictHostKeyChecking=accept-new"])
        cmd.extend(["-r"])  # Recursive by default

        return cmd

    def validate_prerequisites(self) -> Tuple[bool, List[str]]:
        """Validate SSH prerequisites before attempting connection."""
        return SSHConnectionValidator.validate_all(self.host, self.user, self.port, self.key_path or "~/.ssh/id_rsa")

    def test_connection(self) -> Tuple[bool, str]:
        """Test SSH connection with multiple fallback strategies.

        Returns:
            Tuple of (success, message)
        """
        # First, validate prerequisites
        valid, issues = self.validate_prerequisites()
        if not valid:
            return False, f"Prerequisites check failed: {'; '.join(issues)}"

        # Try direct SSH connection
        try:
            cmd = self._get_ssh_command_base()
            cmd.extend([f"{self.user}@{self.host}", "echo 'SSH connection successful'"])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return True, "✓ SSH connection successful"
            else:
                return False, f"SSH connection failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "SSH connection timed out"
        except Exception as e:
            return False, f"SSH connection error: {str(e)}"

    def test_docker_connectivity(self) -> Tuple[bool, str]:
        """Test Docker container availability.

        Returns:
            Tuple of (success, message)
        """
        if not self.docker_enabled:
            return True, "Docker support not enabled"

        # Check if container is running
        cmd = f"docker ps --filter name={self.container_name} --quiet"
        success, output, error = self.execute_command(cmd)

        if not success or not output.strip():
            return False, f"Container '{self.container_name}' not running"

        # Check if config path exists in container
        cmd = f"docker exec {self.container_name} test -d /config && echo 'exists' || echo 'not found'"
        success, output, error = self.execute_command(cmd)

        if not success or "not found" in output:
            return False, f"Config path not found in container"

        return True, f"✓ Container '{self.container_name}' is healthy"

    def execute_command(self, command: str) -> Tuple[bool, str, str]:
        """Execute command on remote host.

        Args:
            command: Command to execute

        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            cmd = self._get_ssh_command_base()
            cmd.extend([f"{self.user}@{self.host}", command])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            return result.returncode == 0, result.stdout, result.stderr

        except Exception as e:
            return False, "", str(e)

    def execute_in_docker(self, command: str) -> Tuple[bool, str, str]:
        """Execute command inside Docker container.

        Args:
            command: Command to execute inside container

        Returns:
            Tuple of (success, stdout, stderr)
        """
        if not self.docker_enabled:
            return False, "", "Docker support not enabled"

        docker_command = f"docker exec {self.container_name} {command}"
        return self.execute_command(docker_command)

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from remote host.

        Args:
            remote_path: Path on remote host
            local_path: Local destination path

        Returns:
            True if successful
        """
        try:
            # Ensure local directory exists
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)

            cmd = self._get_scp_command_base()
            cmd.extend([f"{self.user}@{self.host}:{remote_path}", local_path])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print(f"✓ Downloaded: {remote_path} → {local_path}")
                return True
            else:
                print(f"✗ Download failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"✗ Download error: {e}")
            return False

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to remote host.

        Args:
            local_path: Local source path
            remote_path: Path on remote host

        Returns:
            True if successful
        """
        try:
            cmd = self._get_scp_command_base()
            cmd.extend([local_path, f"{self.user}@{self.host}:{remote_path}"])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print(f"✓ Uploaded: {local_path} → {remote_path}")
                return True
            else:
                print(f"✗ Upload failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"✗ Upload error: {e}")
            return False

    def download_directory(
        self, remote_path: str, local_path: str, exclude_patterns: Optional[List[str]] = None
    ) -> bool:
        """Download directory from remote host using rsync if available.

        Args:
            remote_path: Path on remote host
            local_path: Local destination path
            exclude_patterns: List of patterns to exclude

        Returns:
            True if successful
        """
        exclude_patterns = exclude_patterns or []

        # Try rsync first (more efficient)
        if self._has_rsync():
            return self._rsync_download(remote_path, local_path, exclude_patterns)
        else:
            return self._scp_download_dir(remote_path, local_path)

    def _has_rsync(self) -> bool:
        """Check if rsync is available."""
        try:
            result = subprocess.run(["which", "rsync"], capture_output=True)
            return result.returncode == 0
        except:
            return False

    def _rsync_download(self, remote_path: str, local_path: str, exclude_patterns: List[str]) -> bool:
        """Download using rsync."""
        try:
            Path(local_path).mkdir(parents=True, exist_ok=True)

            cmd = [
                "rsync",
                "-avz",
                "--progress",
                "-e",
                f"ssh -p {self.port}" + (f" -i {self.key_path}" if self.key_path else ""),
            ]

            for pattern in exclude_patterns:
                cmd.extend(["--exclude", pattern])

            cmd.append(f"{self.user}@{self.host}:{remote_path}/")
            cmd.append(f"{local_path}/")

            print(f"Downloading {remote_path} with rsync...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                print(f"✓ Directory downloaded: {remote_path}")
                return True
            else:
                print(f"✗ rsync failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"✗ rsync error: {e}")
            return False

    def _scp_download_dir(self, remote_path: str, local_path: str) -> bool:
        """Download directory using SCP."""
        return self.download_file(remote_path, local_path)

    def upload_directory(self, local_path: str, remote_path: str, exclude_patterns: Optional[List[str]] = None) -> bool:
        """Upload directory to remote host.

        Args:
            local_path: Local source path
            remote_path: Path on remote host
            exclude_patterns: List of patterns to exclude

        Returns:
            True if successful
        """
        exclude_patterns = exclude_patterns or []

        if self._has_rsync():
            return self._rsync_upload(local_path, remote_path, exclude_patterns)
        else:
            return self.upload_file(local_path, remote_path)

    def _rsync_upload(self, local_path: str, remote_path: str, exclude_patterns: List[str]) -> bool:
        """Upload using rsync."""
        try:
            cmd = [
                "rsync",
                "-avz",
                "--progress",
                "-e",
                f"ssh -p {self.port}" + (f" -i {self.key_path}" if self.key_path else ""),
            ]

            for pattern in exclude_patterns:
                cmd.extend(["--exclude", pattern])

            cmd.append(f"{local_path}/")
            cmd.append(f"{self.user}@{self.host}:{remote_path}/")

            print(f"Uploading to {remote_path} with rsync...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                print(f"✓ Directory uploaded: {local_path}")
                return True
            else:
                print(f"✗ rsync failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"✗ rsync error: {e}")
            return False

    def backup_remote(self, remote_path: str, backup_name: Optional[str] = None) -> Tuple[bool, str]:
        """Create backup on remote host.

        Args:
            remote_path: Path to backup
            backup_name: Optional backup name

        Returns:
            Tuple of (success, backup_path)
        """
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"config_backup_{timestamp}"

        backup_path = f"/root/{backup_name}.tar.gz"

        cmd = f"tar -czf {backup_path} -C {remote_path} ."
        success, stdout, stderr = self.execute_command(cmd)

        if success:
            print(f"✓ Remote backup created: {backup_path}")
            return True, backup_path
        else:
            print(f"✗ Backup failed: {stderr}")
            return False, ""

    def restart_home_assistant(self) -> bool:
        """Restart Home Assistant on remote host.

        Returns:
            True if successful
        """
        # Try different restart methods
        restart_commands = [
            "ha core restart",  # Home Assistant OS
            f"docker restart {self.container_name}",  # Docker
            "systemctl restart home-assistant@homeassistant",  # systemd
            "supervisorctl restart homeassistant",  # Supervisor
        ]

        for cmd in restart_commands:
            success, stdout, stderr = self.execute_command(cmd)
            if success:
                print(f"✓ Home Assistant restart initiated: {cmd}")
                return True

        print("⚠ Could not restart Home Assistant automatically")
        return False

    def check_config(self, config_path: str = "/config") -> Tuple[bool, str]:
        """Check Home Assistant configuration on remote.

        Args:
            config_path: Path to configuration

        Returns:
            Tuple of (valid, message)
        """
        # Try Home Assistant config check
        success, stdout, stderr = self.execute_command("ha core check")

        if success:
            return True, "Configuration check passed"

        # Try hass --script check_config
        success, stdout, stderr = self.execute_command(f"hass --script check_config -c {config_path}")

        if success:
            return True, stdout
        else:
            return False, stderr or stdout


class HARemoteManager:
    """High-level manager for remote Home Assistant operations."""

    def __init__(self, config: dict):
        """Initialize with configuration.

        Args:
            config: SSH configuration dictionary
        """
        self.config = config
        self.ssh = DockerAwareSSHTransfer(
            host=config.get("host", ""),
            user=config.get("user", "root"),
            port=config.get("port", 22),
            key_path=config.get("key_path"),
            password=config.get("password"),
            docker_config=config.get("docker", {}),
        )
        self.remote_config_path = config.get("remote_config_path", "/config")

    def verify_connection(self) -> Tuple[bool, List[str]]:
        """Verify SSH and Docker connectivity."""
        messages = []

        # Test SSH
        success, msg = self.ssh.test_connection()
        messages.append(msg)
        if not success:
            return False, messages

        # Test Docker if enabled
        if self.ssh.docker_enabled:
            success, msg = self.ssh.test_docker_connectivity()
            messages.append(msg)
            if not success:
                return False, messages

        return True, messages

    def export_config(self, local_export_dir: str, exclude_patterns: Optional[List[str]] = None) -> bool:
        """Export configuration from remote HA to local directory.

        Args:
            local_export_dir: Local directory to export to
            exclude_patterns: Patterns to exclude

        Returns:
            True if successful
        """
        default_excludes = ["*.log", "*.db", "*.db-*", "deps/", "__pycache__/", "tts/", ".cloud/", "backups/"]
        exclude_patterns = (exclude_patterns or []) + default_excludes

        print(f"\n📤 Exporting configuration from {self.ssh.host}...")

        # Verify connection
        success, messages = self.verify_connection()
        if not success:
            for msg in messages:
                print(f"✗ {msg}")
            return False

        for msg in messages:
            print(msg)

        # Download configuration
        success = self.ssh.download_directory(self.remote_config_path, local_export_dir, exclude_patterns)

        if success:
            print(f"✓ Configuration exported to: {local_export_dir}")

        return success

    def import_config(self, local_import_dir: str, create_backup: bool = True, restart: bool = False) -> bool:
        """Import configuration from local to remote HA.

        Args:
            local_import_dir: Local directory to import from
            create_backup: Create backup before import
            restart: Restart HA after import

        Returns:
            True if successful
        """
        print(f"\n📥 Importing configuration to {self.ssh.host}...")

        # Verify connection
        success, messages = self.verify_connection()
        if not success:
            for msg in messages:
                print(f"✗ {msg}")
            return False

        for msg in messages:
            print(msg)

        # Create backup if requested
        if create_backup:
            success, backup_path = self.ssh.backup_remote(self.remote_config_path)
            if not success:
                print("⚠ Backup failed, continuing anyway...")

        # Upload configuration
        success = self.ssh.upload_directory(
            local_import_dir, self.remote_config_path, exclude_patterns=[".git/", "__pycache__/", "*.pyc"]
        )

        if not success:
            print("✗ Import failed")
            return False

        # Check configuration
        print("🔍 Checking configuration...")
        valid, msg = self.ssh.check_config(self.remote_config_path)
        if not valid:
            print(f"⚠ Configuration check failed: {msg}")
            print("Consider restoring from backup")
            return False

        print("✓ Configuration check passed")

        # Restart if requested
        if restart:
            print("🔄 Restarting Home Assistant...")
            self.ssh.restart_home_assistant()

        print("✓ Import complete")
        return True


if __name__ == "__main__":
    # Test SSH connection with enhanced diagnostics
    import argparse

    parser = argparse.ArgumentParser(description="SSH Transfer for HA with Docker Support")
    parser.add_argument("--host", required=True, help="SSH host")
    parser.add_argument("--user", default="root", help="SSH user")
    parser.add_argument("--port", type=int, default=22, help="SSH port")
    parser.add_argument("--key", help="SSH key path")
    parser.add_argument("--test", action="store_true", help="Test connection")
    parser.add_argument("--docker", action="store_true", help="Enable Docker container support")
    parser.add_argument("--validate-prereqs", action="store_true", help="Validate prerequisites only")

    args = parser.parse_args()

    docker_config = {"enabled": args.docker, "container_name": "homeassistant"} if args.docker else None

    ssh = DockerAwareSSHTransfer(
        host=args.host, user=args.user, port=args.port, key_path=args.key, docker_config=docker_config
    )

    if args.validate_prereqs:
        print("🔍 Validating prerequisites...")
        valid, issues = ssh.validate_prerequisites()
        if valid:
            print("✓ All prerequisites validated")
            sys.exit(0)
        else:
            print("✗ Prerequisites validation failed:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)

    if args.test:
        print("🔗 Testing SSH connection...")
        success, msg = ssh.test_connection()
        print(msg)

        if success and args.docker:
            print("🐳 Testing Docker connectivity...")
            success, msg = ssh.test_docker_connectivity()
            print(msg)

        sys.exit(0 if success else 1)
