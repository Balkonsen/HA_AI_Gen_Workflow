#!/usr/bin/env python3
"""
SSH Transfer Module for HA AI Gen Workflow
Handles secure file transfer between local and remote Home Assistant.
"""

import os
import sys
import subprocess
import logging
import time
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class SSHTransfer:
    """Handles SSH/SCP file transfers to/from Home Assistant."""

    def __init__(
        self,
        host: str,
        user: str = "root",
        port: int = 22,
        key_path: Optional[str] = None,
        password: Optional[str] = None,
        connection_timeout: int = 30,
        transfer_timeout: int = 600,
        retry_attempts: int = 3,
        retry_delay: int = 2,
    ):
        """Initialize SSH transfer.

        Args:
            host: SSH host (IP or hostname)
            user: SSH username
            port: SSH port
            key_path: Path to SSH private key
            password: SSH password (if not using key)
            connection_timeout: SSH connection timeout in seconds (default: 30)
            transfer_timeout: File transfer timeout in seconds (default: 600)
            retry_attempts: Number of retry attempts for transient failures (default: 3)
            retry_delay: Delay between retries in seconds (default: 2)
        """
        self.host = host
        self.user = user
        self.port = port
        self.key_path = os.path.expanduser(key_path) if key_path else None
        self.password = password
        self.connection_timeout = connection_timeout
        self.transfer_timeout = transfer_timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        self._client = None
        self._sftp = None

    def _get_ssh_command_base(self) -> List[str]:
        """Get base SSH command with authentication."""
        cmd = []
        
        # Use sshpass for password authentication
        if self.password and not self.key_path:
            cmd.extend(["sshpass", "-p", self.password])
        
        cmd.extend(["ssh", "-p", str(self.port)])

        if self.key_path:
            cmd.extend(["-i", self.key_path])
            # BatchMode=yes prevents password prompts when using keys
            cmd.extend(["-o", "BatchMode=yes"])
        
        cmd.extend(["-o", "StrictHostKeyChecking=accept-new"])

        return cmd

    def _get_scp_command_base(self) -> List[str]:
        """Get base SCP command with authentication."""
        cmd = []
        
        # Use sshpass for password authentication
        if self.password and not self.key_path:
            cmd.extend(["sshpass", "-p", self.password])
        
        cmd.extend(["scp", "-P", str(self.port)])

        if self.key_path:
            cmd.extend(["-i", self.key_path])

        cmd.extend(["-o", "StrictHostKeyChecking=accept-new"])
        cmd.extend(["-r"])  # Recursive by default

        return cmd

    def test_connection(self) -> Tuple[bool, str]:
        """Test SSH connection with retry logic.

        Returns:
            Tuple of (success, message)
        """
        for attempt in range(self.retry_attempts):
            try:
                cmd = self._get_ssh_command_base()
                cmd.extend([f"{self.user}@{self.host}", "echo 'Connection successful'"])

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.connection_timeout)

                if result.returncode == 0:
                    logger.info(f"SSH connection successful to {self.user}@{self.host}:{self.port}")
                    return True, "Connection successful"
                else:
                    error_msg = result.stderr.strip()
                    logger.warning(f"SSH connection failed (attempt {attempt + 1}/{self.retry_attempts}): {error_msg}")

                    # Check for specific error conditions
                    if "Connection refused" in error_msg:
                        return False, f"Connection refused: SSH service may not be running on {self.host}:{self.port}"
                    elif "Permission denied" in error_msg or "Authentication failed" in error_msg:
                        return False, "Authentication failed: Check username, password, or SSH key"
                    elif "No route to host" in error_msg or "Network is unreachable" in error_msg:
                        return False, f"Network unreachable: Cannot reach host {self.host}"
                    elif "Could not resolve hostname" in error_msg:
                        return False, f"Cannot resolve hostname: {self.host}"

                    # For other errors, retry if attempts remain
                    if attempt < self.retry_attempts - 1:
                        logger.info(f"Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                        continue

                    return False, f"Connection failed: {error_msg}"

            except subprocess.TimeoutExpired:
                logger.warning(f"SSH connection timeout (attempt {attempt + 1}/{self.retry_attempts})")
                if attempt < self.retry_attempts - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    continue
                return False, f"Connection timeout after {self.connection_timeout}s. Host may be unreachable."

            except FileNotFoundError as e:
                logger.error(f"SSH command not found: {e}")
                return False, "SSH command not found. Please install OpenSSH client."

            except Exception as e:
                logger.exception(f"Unexpected error during SSH connection test: {e}")
                return False, f"Unexpected error: {str(e)}"

        return False, "Connection failed after all retry attempts"

    def execute_command(self, command: str, timeout: Optional[int] = None) -> Tuple[bool, str, str]:
        """Execute command on remote host with timeout.

        Args:
            command: Command to execute
            timeout: Command timeout in seconds (default: uses connection_timeout * 4)

        Returns:
            Tuple of (success, stdout, stderr)
        """
        if timeout is None:
            timeout = self.connection_timeout * 4  # Allow longer for command execution

        try:
            cmd = self._get_ssh_command_base()
            cmd.extend([f"{self.user}@{self.host}", command])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

            success = result.returncode == 0
            if success:
                logger.debug(f"Command executed successfully: {command}")
            else:
                logger.warning(f"Command failed with exit code {result.returncode}: {command}")

            return success, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout after {timeout}s: {command}")
            return False, "", f"Command timeout after {timeout}s"

        except FileNotFoundError as e:
            logger.error(f"SSH command not found: {e}")
            return False, "", "SSH command not found. Please install OpenSSH client."

        except Exception as e:
            logger.exception(f"Unexpected error executing command: {e}")
            return False, "", str(e)

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from remote host with retry logic.

        Args:
            remote_path: Path on remote host
            local_path: Local destination path

        Returns:
            True if successful
        """
        for attempt in range(self.retry_attempts):
            try:
                # Ensure local directory exists
                Path(local_path).parent.mkdir(parents=True, exist_ok=True)

                cmd = self._get_scp_command_base()
                cmd.extend([f"{self.user}@{self.host}:{remote_path}", local_path])

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.transfer_timeout)

                if result.returncode == 0:
                    logger.info(f"Downloaded: {remote_path} → {local_path}")
                    print(f"✓ Downloaded: {remote_path} → {local_path}")
                    return True
                else:
                    error_msg = result.stderr.strip()
                    logger.warning(f"Download failed (attempt {attempt + 1}/{self.retry_attempts}): {error_msg}")

                    # Check for specific error conditions
                    if "No such file or directory" in error_msg:
                        logger.error(f"Remote file not found: {remote_path}")
                        print(f"✗ Download failed: Remote file not found: {remote_path}")
                        return False
                    elif "Permission denied" in error_msg:
                        logger.error(f"Permission denied accessing: {remote_path}")
                        print(f"✗ Download failed: Permission denied: {remote_path}")
                        return False

                    # Retry for transient errors
                    if attempt < self.retry_attempts - 1:
                        logger.info(f"Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                        continue

                    print(f"✗ Download failed: {error_msg}")
                    return False

            except subprocess.TimeoutExpired:
                logger.warning(f"Download timeout (attempt {attempt + 1}/{self.retry_attempts})")
                if attempt < self.retry_attempts - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    continue
                print(f"✗ Download timeout after {self.transfer_timeout}s")
                return False

            except FileNotFoundError as e:
                logger.error(f"SCP command not found: {e}")
                print("✗ Download error: SCP command not found")
                return False

            except PermissionError:
                logger.error(f"Permission denied writing to: {local_path}")
                print(f"✗ Download error: Permission denied: {local_path}")
                return False

            except Exception as e:
                logger.exception(f"Unexpected error during download: {e}")
                print(f"✗ Download error: {e}")
                return False

        return False

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to remote host with retry logic.

        Args:
            local_path: Local source path
            remote_path: Path on remote host

        Returns:
            True if successful
        """
        for attempt in range(self.retry_attempts):
            try:
                # Check if local file exists
                if not Path(local_path).exists():
                    logger.error(f"Local file not found: {local_path}")
                    print(f"✗ Upload failed: Local file not found: {local_path}")
                    return False

                cmd = self._get_scp_command_base()
                cmd.extend([local_path, f"{self.user}@{self.host}:{remote_path}"])

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.transfer_timeout)

                if result.returncode == 0:
                    logger.info(f"Uploaded: {local_path} → {remote_path}")
                    print(f"✓ Uploaded: {local_path} → {remote_path}")
                    return True
                else:
                    error_msg = result.stderr.strip()
                    logger.warning(f"Upload failed (attempt {attempt + 1}/{self.retry_attempts}): {error_msg}")

                    # Check for specific error conditions
                    if "Permission denied" in error_msg:
                        logger.error(f"Permission denied writing to: {remote_path}")
                        print(f"✗ Upload failed: Permission denied: {remote_path}")
                        return False
                    elif "No such file or directory" in error_msg:
                        logger.error(f"Remote directory not found for: {remote_path}")
                        print(f"✗ Upload failed: Remote directory not found: {remote_path}")
                        return False

                    # Retry for transient errors
                    if attempt < self.retry_attempts - 1:
                        logger.info(f"Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                        continue

                    print(f"✗ Upload failed: {error_msg}")
                    return False

            except subprocess.TimeoutExpired:
                logger.warning(f"Upload timeout (attempt {attempt + 1}/{self.retry_attempts})")
                if attempt < self.retry_attempts - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    continue
                print(f"✗ Upload timeout after {self.transfer_timeout}s")
                return False

            except FileNotFoundError as e:
                if "scp" in str(e).lower():
                    logger.error(f"SCP command not found: {e}")
                    print("✗ Upload error: SCP command not found")
                else:
                    logger.error(f"File not found: {e}")
                    print(f"✗ Upload error: File not found: {e}")
                return False

            except PermissionError:
                logger.error(f"Permission denied reading: {local_path}")
                print(f"✗ Upload error: Permission denied: {local_path}")
                return False

            except Exception as e:
                logger.exception(f"Unexpected error during upload: {e}")
                print(f"✗ Upload error: {e}")
                return False

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
        except Exception:
            return False

    def _rsync_download(self, remote_path: str, local_path: str, exclude_patterns: List[str]) -> bool:
        """Download using rsync with timeout."""
        try:
            Path(local_path).mkdir(parents=True, exist_ok=True)

            cmd = []
            
            # Use sshpass for password authentication
            if self.password and not self.key_path:
                cmd.extend(["sshpass", "-p", self.password])
            
            ssh_opts = f"ssh -p {self.port}"
            if self.key_path:
                ssh_opts += f" -i {self.key_path}"
            
            cmd.extend([
                "rsync",
                "-avz",
                "--progress",
                "-e",
                ssh_opts,
            ])

            for pattern in exclude_patterns:
                cmd.extend(["--exclude", pattern])

            cmd.append(f"{self.user}@{self.host}:{remote_path}/")
            cmd.append(f"{local_path}/")

            print(f"Downloading {remote_path} with rsync...")
            logger.info(f"Starting rsync download from {remote_path}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.transfer_timeout)

            if result.returncode == 0:
                logger.info(f"Directory downloaded successfully: {remote_path}")
                print(f"✓ Directory downloaded: {remote_path}")
                return True
            else:
                logger.error(f"rsync failed: {result.stderr}")
                print(f"✗ rsync failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"rsync timeout after {self.transfer_timeout}s")
            print(f"✗ rsync timeout after {self.transfer_timeout}s")
            return False

        except FileNotFoundError as e:
            logger.error(f"rsync command not found: {e}")
            print("✗ rsync error: rsync command not found")
            return False

        except Exception as e:
            logger.exception(f"Unexpected rsync error: {e}")
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
        """Upload using rsync with timeout."""
        try:
            cmd = []
            
            # Use sshpass for password authentication
            if self.password and not self.key_path:
                cmd.extend(["sshpass", "-p", self.password])
            
            ssh_opts = f"ssh -p {self.port}"
            if self.key_path:
                ssh_opts += f" -i {self.key_path}"
            
            cmd.extend([
                "rsync",
                "-avz",
                "--progress",
                "-e",
                ssh_opts,
            ])

            for pattern in exclude_patterns:
                cmd.extend(["--exclude", pattern])

            cmd.append(f"{local_path}/")
            cmd.append(f"{self.user}@{self.host}:{remote_path}/")

            print(f"Uploading to {remote_path} with rsync...")
            logger.info(f"Starting rsync upload to {remote_path}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.transfer_timeout)

            if result.returncode == 0:
                logger.info(f"Directory uploaded successfully: {local_path}")
                print(f"✓ Directory uploaded: {local_path}")
                return True
            else:
                logger.error(f"rsync failed: {result.stderr}")
                print(f"✗ rsync failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"rsync timeout after {self.transfer_timeout}s")
            print(f"✗ rsync timeout after {self.transfer_timeout}s")
            return False

        except FileNotFoundError as e:
            logger.error(f"rsync command not found: {e}")
            print("✗ rsync error: rsync command not found")
            return False

        except Exception as e:
            logger.exception(f"Unexpected rsync error: {e}")
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
            "docker restart homeassistant",  # Docker
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
        self.ssh = SSHTransfer(
            host=config.get("host", ""),
            user=config.get("user", "root"),
            port=config.get("port", 22),
            key_path=config.get("key_path"),
            password=config.get("password"),
            connection_timeout=config.get("connection_timeout", 30),
            transfer_timeout=config.get("transfer_timeout", 600),
            retry_attempts=config.get("retry_attempts", 3),
            retry_delay=config.get("retry_delay", 2),
        )
        self.remote_config_path = config.get("remote_config_path", "/config")

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

        # Test connection first
        success, msg = self.ssh.test_connection()
        if not success:
            print(f"✗ {msg}")
            return False

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

        # Test connection
        success, msg = self.ssh.test_connection()
        if not success:
            print(f"✗ {msg}")
            return False

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
    # Test SSH connection
    import argparse

    parser = argparse.ArgumentParser(description="SSH Transfer for HA")
    parser.add_argument("--host", required=True, help="SSH host")
    parser.add_argument("--user", default="root", help="SSH user")
    parser.add_argument("--port", type=int, default=22, help="SSH port")
    parser.add_argument("--key", help="SSH key path")
    parser.add_argument("--test", action="store_true", help="Test connection")
    parser.add_argument("--ssh-timeout", type=int, default=30, help="SSH connection timeout (seconds)")
    parser.add_argument("--transfer-timeout", type=int, default=600, help="File transfer timeout (seconds)")

    args = parser.parse_args()

    ssh = SSHTransfer(
        host=args.host,
        user=args.user,
        port=args.port,
        key_path=args.key,
        connection_timeout=args.ssh_timeout,
        transfer_timeout=args.transfer_timeout,
    )

    if args.test:
        success, msg = ssh.test_connection()
        print(msg)
        sys.exit(0 if success else 1)
