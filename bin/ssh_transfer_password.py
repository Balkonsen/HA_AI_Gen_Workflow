#!/usr/bin/env python3
"""
Enhanced SSH Transfer Module with Password Authentication Support
Handles secure file transfer between local and remote Home Assistant.
Supports both SSH key-based and password-based authentication.
"""

import os
import sys
import subprocess
import tempfile
import socket
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
import getpass

# Try to import paramiko for native SSH support (preferred for password auth)
try:
    import paramiko

    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False


class SSHAuthValidator:
    """Validates SSH authentication prerequisites."""

    @staticmethod
    def check_sshpass_available() -> bool:
        """Check if sshpass utility is available."""
        try:
            result = subprocess.run(["which", "sshpass"], capture_output=True)
            return result.returncode == 0
        except:
            return False

    @staticmethod
    def check_password_auth_viable(host: str, user: str, port: int) -> Tuple[bool, str]:
        """Check if password auth is viable (can at least reach SSH)."""
        try:
            sock = socket.create_connection((host, port), timeout=5)
            sock.close()
            return True, "Host SSH port is reachable"
        except Exception as e:
            return False, f"Cannot reach SSH port: {str(e)}"

    @staticmethod
    def validate_auth_config(
        host: str, user: str, port: int, key_path: Optional[str] = None, password: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        """Determine best available authentication method."""
        issues = []
        method = None

        # Priority 1: SSH key if provided and exists
        if key_path:
            key_path_expanded = Path(key_path).expanduser()
            if key_path_expanded.exists():
                # Check permissions
                mode = oct(key_path_expanded.stat().st_mode)[-3:]
                if mode == "600":
                    return "key", []
                else:
                    issues.append(f"SSH key permissions incorrect ({mode}, should be 600)")
            else:
                issues.append(f"SSH key not found: {key_path}")

        # Priority 2: Paramiko if password provided and library available
        if password and PARAMIKO_AVAILABLE:
            return "paramiko", issues

        # Priority 3: sshpass if password provided and tool available
        if password and SSHAuthValidator.check_sshpass_available():
            return "sshpass", issues

        # Priority 4: Interactive prompt for password
        if password:
            issues.append("No automated password auth available; will prompt for password")
            return "interactive", issues

        # Priority 5: SSH Agent
        try:
            result = subprocess.run(["ssh-add", "-l"], capture_output=True)
            if result.returncode == 0:
                return "ssh-agent", issues
        except:
            pass

        issues.append("No SSH key or password provided")
        return "unknown", issues


class SSHTransferPasswordSupport:
    """Enhanced SSH transfer with password authentication support."""

    def __init__(
        self,
        host: str,
        user: str = "root",
        port: int = 22,
        key_path: Optional[str] = None,
        password: Optional[str] = None,
        auth_method: str = "auto",
        docker_config: Optional[dict] = None,
    ):
        """Initialize SSH transfer with password support.

        Args:
            host: SSH host (IP or hostname)
            user: SSH username
            port: SSH port
            key_path: Path to SSH private key
            password: SSH password (for password-based auth)
            auth_method: "auto", "key", "password", "paramiko", "sshpass", "interactive"
            docker_config: Docker configuration dictionary
        """
        self.host = host
        self.user = user
        self.port = port
        self.key_path = os.path.expanduser(key_path) if key_path else None
        self.password = password
        self.auth_method = auth_method

        self.docker_config = docker_config or {}
        self.docker_enabled = self.docker_config.get("enabled", False)
        self.container_name = self.docker_config.get("container_name", "homeassistant")

        # Auto-detect authentication method if requested
        if auth_method == "auto":
            self.auth_method, _ = SSHAuthValidator.validate_auth_config(host, user, port, key_path, password)

        self._client = None
        self._sftp = None

    def _get_ssh_command_base(self, allow_interactive: bool = False) -> List[str]:
        """Get base SSH command with appropriate authentication.

        Args:
            allow_interactive: Allow interactive password prompt (for interactive method)
        """
        cmd = ["ssh", "-p", str(self.port)]

        # Add key if using key-based auth
        if self.auth_method == "key" and self.key_path:
            cmd.extend(["-i", self.key_path])

        # Configure host key verification
        cmd.extend(["-o", "StrictHostKeyChecking=accept-new"])

        # Only use BatchMode if NOT using password auth
        if self.auth_method != "password" and self.auth_method != "interactive":
            cmd.extend(["-o", "BatchMode=yes"])

        cmd.extend(["-o", f"ConnectTimeout=10"])

        return cmd

    def _get_scp_command_base(self) -> List[str]:
        """Get base SCP command with authentication."""
        cmd = ["scp", "-P", str(self.port)]

        if self.auth_method == "key" and self.key_path:
            cmd.extend(["-i", self.key_path])

        cmd.extend(["-o", "StrictHostKeyChecking=accept-new"])
        cmd.extend(["-r"])  # Recursive by default

        return cmd

    def _execute_with_sshpass(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Execute command using sshpass for password auth."""
        if not self.password:
            raise ValueError("Password required for sshpass method")

        # Prepend sshpass (password is hidden from process list)
        full_cmd = ["sshpass", "-p", self.password] + cmd

        try:
            result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=120)
            return result
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Command timed out: {' '.join(cmd[:3])}")

    def _execute_with_paramiko(self, command: str) -> Tuple[bool, str, str]:
        """Execute command using Paramiko (pure Python SSH)."""
        if not PARAMIKO_AVAILABLE:
            return False, "", "Paramiko not available"

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect with password
            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password if self.auth_method in ["paramiko", "interactive"] else None,
                key_filename=self.key_path if self.auth_method == "key" else None,
                timeout=30,
                auth_timeout=30,
                look_for_keys=True if self.auth_method == "key" else False,
            )

            stdin, stdout, stderr = client.exec_command(command, timeout=120)

            stdout_text = stdout.read().decode()
            stderr_text = stderr.read().decode()
            success = stdout.channel.recv_exit_status() == 0

            client.close()
            return success, stdout_text, stderr_text

        except paramiko.AuthenticationException as e:
            return False, "", f"Authentication failed: {str(e)}"
        except Exception as e:
            return False, "", f"Paramiko error: {str(e)}"

    def _execute_with_interactive(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Execute command with interactive password prompt."""
        # Remove BatchMode for interactive prompts
        ssh_cmd = ["ssh", "-p", str(self.port)]

        if self.key_path:
            ssh_cmd.extend(["-i", self.key_path])

        ssh_cmd.extend(["-o", "StrictHostKeyChecking=accept-new"])

        full_cmd = ssh_cmd + cmd

        try:
            # Allow interactive input (TTY)
            result = subprocess.run(
                full_cmd, capture_output=False, text=True, timeout=300  # Longer timeout for interactive
            )
            return result
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Interactive command timed out")

    def test_connection(self) -> Tuple[bool, str]:
        """Test SSH connection using selected authentication method.

        Returns:
            Tuple of (success, message)
        """
        try:
            if self.auth_method == "paramiko":
                success, stdout, stderr = self._execute_with_paramiko("echo 'SSH connection successful'")
                msg = stdout if success else stderr
                return success, msg

            elif self.auth_method == "sshpass":
                cmd = self._get_ssh_command_base()
                cmd.extend([f"{self.user}@{self.host}", "echo 'SSH connection successful'"])
                result = self._execute_with_sshpass(cmd)
                return result.returncode == 0, result.stdout or result.stderr

            elif self.auth_method == "interactive":
                cmd = self._get_ssh_command_base(allow_interactive=True)
                cmd.extend([f"{self.user}@{self.host}", "echo 'SSH connection successful'"])
                result = self._execute_with_interactive(cmd)
                return result.returncode == 0, (
                    "Interactive connection successful" if result.returncode == 0 else "Interactive connection failed"
                )

            else:  # key or auto
                cmd = self._get_ssh_command_base()
                cmd.extend([f"{self.user}@{self.host}", "echo 'SSH connection successful'"])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return result.returncode == 0, result.stdout or result.stderr

        except subprocess.TimeoutExpired:
            return False, "Connection timed out"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def execute_command(self, command: str) -> Tuple[bool, str, str]:
        """Execute command on remote host.

        Args:
            command: Command to execute

        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            if self.auth_method == "paramiko":
                return self._execute_with_paramiko(command)

            elif self.auth_method == "sshpass":
                cmd = self._get_ssh_command_base()
                cmd.extend([f"{self.user}@{self.host}", command])
                result = self._execute_with_sshpass(cmd)
                return result.returncode == 0, result.stdout, result.stderr

            elif self.auth_method == "interactive":
                cmd = self._get_ssh_command_base(allow_interactive=True)
                cmd.extend([f"{self.user}@{self.host}", command])
                result = self._execute_with_interactive(cmd)
                return result.returncode == 0, "", ""

            else:  # key or auto
                cmd = self._get_ssh_command_base()
                cmd.extend([f"{self.user}@{self.host}", command])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                return result.returncode == 0, result.stdout, result.stderr

        except Exception as e:
            return False, "", str(e)

    def execute_in_docker(self, command: str) -> Tuple[bool, str, str]:
        """Execute command inside Docker container."""
        if not self.docker_enabled:
            return False, "", "Docker support not enabled"

        docker_command = f"docker exec {self.container_name} {command}"
        return self.execute_command(docker_command)

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from remote host."""
        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)

            cmd = self._get_scp_command_base()
            cmd.extend([f"{self.user}@{self.host}:{remote_path}", local_path])

            if self.auth_method == "sshpass":
                result = self._execute_with_sshpass(cmd)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print(f"✓ Downloaded: {remote_path} → {local_path}")
                return True
            else:
                print(f"✗ Download failed: {result.stderr if hasattr(result, 'stderr') else str(result)}")
                return False

        except Exception as e:
            print(f"✗ Download error: {e}")
            return False

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to remote host."""
        try:
            cmd = self._get_scp_command_base()
            cmd.extend([local_path, f"{self.user}@{self.host}:{remote_path}"])

            if self.auth_method == "sshpass":
                result = self._execute_with_sshpass(cmd)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print(f"✓ Uploaded: {local_path} → {remote_path}")
                return True
            else:
                print(f"✗ Upload failed: {result.stderr if hasattr(result, 'stderr') else str(result)}")
                return False

        except Exception as e:
            print(f"✗ Upload error: {e}")
            return False

    def download_directory(
        self, remote_path: str, local_path: str, exclude_patterns: Optional[List[str]] = None
    ) -> bool:
        """Download directory from remote host."""
        exclude_patterns = exclude_patterns or []

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

            ssh_args = f"ssh -p {self.port}"
            if self.auth_method == "key" and self.key_path:
                ssh_args += f" -i {self.key_path}"

            cmd = [
                "rsync",
                "-avz",
                "--progress",
                "-e",
                ssh_args,
            ]

            for pattern in exclude_patterns:
                cmd.extend(["--exclude", pattern])

            cmd.append(f"{self.user}@{self.host}:{remote_path}/")
            cmd.append(f"{local_path}/")

            print(f"Downloading {remote_path} with rsync...")

            if self.auth_method == "sshpass":
                result = self._execute_with_sshpass(cmd)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                print(f"✓ Directory downloaded: {remote_path}")
                return True
            else:
                print(f"✗ rsync failed: {result.stderr if hasattr(result, 'stderr') else str(result)}")
                return False

        except Exception as e:
            print(f"✗ rsync error: {e}")
            return False

    def _scp_download_dir(self, remote_path: str, local_path: str) -> bool:
        """Download directory using SCP."""
        return self.download_file(remote_path, local_path)

    def upload_directory(self, local_path: str, remote_path: str, exclude_patterns: Optional[List[str]] = None) -> bool:
        """Upload directory to remote host."""
        exclude_patterns = exclude_patterns or []

        if self._has_rsync():
            return self._rsync_upload(local_path, remote_path, exclude_patterns)
        else:
            return self.upload_file(local_path, remote_path)

    def _rsync_upload(self, local_path: str, remote_path: str, exclude_patterns: List[str]) -> bool:
        """Upload using rsync."""
        try:
            ssh_args = f"ssh -p {self.port}"
            if self.auth_method == "key" and self.key_path:
                ssh_args += f" -i {self.key_path}"

            cmd = [
                "rsync",
                "-avz",
                "--progress",
                "-e",
                ssh_args,
            ]

            for pattern in exclude_patterns:
                cmd.extend(["--exclude", pattern])

            cmd.append(f"{local_path}/")
            cmd.append(f"{self.user}@{self.host}:{remote_path}/")

            print(f"Uploading to {remote_path} with rsync...")

            if self.auth_method == "sshpass":
                result = self._execute_with_sshpass(cmd)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                print(f"✓ Directory uploaded: {local_path}")
                return True
            else:
                print(f"✗ rsync failed: {result.stderr if hasattr(result, 'stderr') else str(result)}")
                return False

        except Exception as e:
            print(f"✗ rsync error: {e}")
            return False

    def backup_remote(self, remote_path: str, backup_name: Optional[str] = None) -> Tuple[bool, str]:
        """Create backup on remote host."""
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
        """Restart Home Assistant on remote host."""
        restart_commands = [
            "ha core restart",
            f"docker restart {self.container_name}",
            "systemctl restart home-assistant@homeassistant",
            "supervisorctl restart homeassistant",
        ]

        for cmd in restart_commands:
            success, stdout, stderr = self.execute_command(cmd)
            if success:
                print(f"✓ Home Assistant restart initiated: {cmd}")
                return True

        print("⚠ Could not restart Home Assistant automatically")
        return False

    def check_config(self, config_path: str = "/config") -> Tuple[bool, str]:
        """Check Home Assistant configuration."""
        success, stdout, stderr = self.execute_command("ha core check")

        if success:
            return True, "Configuration check passed"

        success, stdout, stderr = self.execute_command(f"hass --script check_config -c {config_path}")

        if success:
            return True, stdout
        else:
            return False, stderr or stdout


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced SSH Transfer with Password Support")
    parser.add_argument("--host", required=True, help="SSH host")
    parser.add_argument("--user", default="root", help="SSH user")
    parser.add_argument("--port", type=int, default=22, help="SSH port")
    parser.add_argument("--key", help="SSH key path")
    parser.add_argument("--password", help="SSH password")
    parser.add_argument(
        "--method",
        choices=["auto", "key", "password", "paramiko", "sshpass", "interactive"],
        default="auto",
        help="Authentication method",
    )
    parser.add_argument("--test", action="store_true", help="Test connection")
    parser.add_argument("--cmd", help="Execute command")
    parser.add_argument("--docker", action="store_true", help="Docker container support")
    parser.add_argument("--docker-check", action="store_true", help="Check Docker container")

    args = parser.parse_args()

    # Prompt for password if not provided and method requires it
    password = args.password
    if args.method in ["password", "interactive", "paramiko"] and not password:
        password = getpass.getpass(f"SSH password for {args.user}@{args.host}: ")

    docker_config = {"enabled": args.docker, "container_name": "homeassistant"} if args.docker else None

    ssh = SSHTransferPasswordSupport(
        host=args.host,
        user=args.user,
        port=args.port,
        key_path=args.key,
        password=password,
        auth_method=args.method,
        docker_config=docker_config,
    )

    print(f"🔐 Using auth method: {ssh.auth_method}")

    if args.test:
        print("🔗 Testing SSH connection...")
        success, msg = ssh.test_connection()
        print(f"{'✓' if success else '✗'} {msg}")
        sys.exit(0 if success else 1)

    if args.cmd:
        print(f"▶ Executing: {args.cmd}")
        success, stdout, stderr = ssh.execute_command(args.cmd)
        if success:
            print(stdout)
        else:
            print(f"Error: {stderr}", file=sys.stderr)
        sys.exit(0 if success else 1)

    if args.docker_check:
        print("🐳 Checking Docker container...")
        success, stdout, stderr = ssh.execute_command(f"docker ps --filter name={ssh.container_name}")
        print(stdout)
        sys.exit(0 if success else 1)
