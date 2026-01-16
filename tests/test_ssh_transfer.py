"""
Tests for SSH Transfer Module
"""
import pytest
import subprocess
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import time

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

from ssh_transfer import SSHTransfer, HARemoteManager


class TestSSHTransfer:
    """Tests for SSHTransfer class."""
    
    def test_init_default_values(self):
        """Test SSHTransfer initialization with default values."""
        ssh = SSHTransfer(host="test.host.com")
        
        assert ssh.host == "test.host.com"
        assert ssh.user == "root"
        assert ssh.port == 22
        assert ssh.connection_timeout == 30
        assert ssh.transfer_timeout == 600
        assert ssh.retry_attempts == 3
        assert ssh.retry_delay == 2
    
    def test_init_custom_values(self):
        """Test SSHTransfer initialization with custom values."""
        ssh = SSHTransfer(
            host="custom.host.com",
            user="admin",
            port=2222,
            key_path="~/.ssh/custom_key",
            connection_timeout=60,
            transfer_timeout=1200,
            retry_attempts=5,
            retry_delay=3
        )
        
        assert ssh.host == "custom.host.com"
        assert ssh.user == "admin"
        assert ssh.port == 2222
        assert ssh.connection_timeout == 60
        assert ssh.transfer_timeout == 1200
        assert ssh.retry_attempts == 5
        assert ssh.retry_delay == 3
    
    @patch('subprocess.run')
    def test_connection_success(self, mock_run):
        """Test successful SSH connection."""
        mock_run.return_value = Mock(returncode=0, stdout="Connection successful", stderr="")
        
        ssh = SSHTransfer(host="test.host.com")
        success, message = ssh.test_connection()
        
        assert success is True
        assert message == "Connection successful"
        mock_run.assert_called_once()
        
        # Check timeout was passed
        call_args = mock_run.call_args
        assert call_args.kwargs['timeout'] == 30
    
    @patch('subprocess.run')
    def test_connection_refused(self, mock_run):
        """Test connection refused error."""
        mock_run.return_value = Mock(
            returncode=255, 
            stdout="", 
            stderr="ssh: connect to host test.host.com port 22: Connection refused"
        )
        
        ssh = SSHTransfer(host="test.host.com", retry_attempts=1)
        success, message = ssh.test_connection()
        
        assert success is False
        assert "Connection refused" in message
        assert "SSH service may not be running" in message
    
    @patch('subprocess.run')
    def test_authentication_failure(self, mock_run):
        """Test SSH authentication failure."""
        mock_run.return_value = Mock(
            returncode=255,
            stdout="",
            stderr="Permission denied (publickey,password)"
        )
        
        ssh = SSHTransfer(host="test.host.com", retry_attempts=1)
        success, message = ssh.test_connection()
        
        assert success is False
        assert "Authentication failed" in message or "Permission denied" in message
    
    @patch('subprocess.run')
    def test_connection_timeout(self, mock_run):
        """Test connection timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=30)
        
        ssh = SSHTransfer(host="test.host.com", retry_attempts=1)
        success, message = ssh.test_connection()
        
        assert success is False
        assert "timeout" in message.lower()
    
    @patch('subprocess.run')
    @patch('time.sleep')
    def test_connection_retry_logic(self, mock_sleep, mock_run):
        """Test retry logic for transient failures."""
        # First two attempts fail, third succeeds
        mock_run.side_effect = [
            Mock(returncode=255, stdout="", stderr="Network error"),
            Mock(returncode=255, stdout="", stderr="Network error"),
            Mock(returncode=0, stdout="Connection successful", stderr="")
        ]
        
        ssh = SSHTransfer(host="test.host.com", retry_attempts=3, retry_delay=1)
        success, message = ssh.test_connection()
        
        assert success is True
        assert message == "Connection successful"
        assert mock_run.call_count == 3
        assert mock_sleep.call_count == 2  # Sleeps between retries
    
    @patch('subprocess.run')
    def test_hostname_resolution_failure(self, mock_run):
        """Test hostname resolution failure."""
        mock_run.return_value = Mock(
            returncode=255,
            stdout="",
            stderr="ssh: Could not resolve hostname invalid.host: Name or service not known"
        )
        
        ssh = SSHTransfer(host="invalid.host", retry_attempts=1)
        success, message = ssh.test_connection()
        
        assert success is False
        assert "resolve hostname" in message.lower() or "invalid.host" in message
    
    @patch('subprocess.run')
    def test_execute_command_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="command output",
            stderr=""
        )
        
        ssh = SSHTransfer(host="test.host.com")
        success, stdout, stderr = ssh.execute_command("ls -la")
        
        assert success is True
        assert stdout == "command output"
        assert stderr == ""
    
    @patch('subprocess.run')
    def test_execute_command_failure(self, mock_run):
        """Test failed command execution."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="command not found"
        )
        
        ssh = SSHTransfer(host="test.host.com")
        success, stdout, stderr = ssh.execute_command("invalid_command")
        
        assert success is False
        assert stderr == "command not found"
    
    @patch('subprocess.run')
    def test_execute_command_timeout(self, mock_run):
        """Test command execution timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=120)
        
        ssh = SSHTransfer(host="test.host.com")
        success, stdout, stderr = ssh.execute_command("long_running_command")
        
        assert success is False
        assert "timeout" in stderr.lower()
    
    @patch('subprocess.run')
    def test_download_file_success(self, mock_run, temp_dir):
        """Test successful file download."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        local_path = os.path.join(temp_dir, "test.txt")
        ssh = SSHTransfer(host="test.host.com")
        
        success = ssh.download_file("/remote/test.txt", local_path)
        
        assert success is True
        mock_run.assert_called_once()
        
        # Check timeout was passed
        call_args = mock_run.call_args
        assert call_args.kwargs['timeout'] == 600
    
    @patch('subprocess.run')
    def test_download_file_not_found(self, mock_run):
        """Test download when remote file doesn't exist."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="scp: /remote/missing.txt: No such file or directory"
        )
        
        ssh = SSHTransfer(host="test.host.com", retry_attempts=1)
        success = ssh.download_file("/remote/missing.txt", "/local/test.txt")
        
        assert success is False
    
    @patch('subprocess.run')
    def test_download_file_permission_denied(self, mock_run):
        """Test download with permission denied."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="scp: /remote/test.txt: Permission denied"
        )
        
        ssh = SSHTransfer(host="test.host.com", retry_attempts=1)
        success = ssh.download_file("/remote/test.txt", "/local/test.txt")
        
        assert success is False
    
    @patch('subprocess.run')
    def test_download_file_timeout(self, mock_run):
        """Test download timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="scp", timeout=600)
        
        ssh = SSHTransfer(host="test.host.com", retry_attempts=1)
        success = ssh.download_file("/remote/large.txt", "/local/large.txt")
        
        assert success is False
    
    @patch('subprocess.run')
    @patch('time.sleep')
    def test_download_retry_logic(self, mock_sleep, mock_run, temp_dir):
        """Test retry logic for file download."""
        # First attempt fails, second succeeds
        mock_run.side_effect = [
            Mock(returncode=1, stdout="", stderr="Network error"),
            Mock(returncode=0, stdout="", stderr="")
        ]
        
        local_path = os.path.join(temp_dir, "test.txt")
        ssh = SSHTransfer(host="test.host.com", retry_attempts=2, retry_delay=1)
        
        success = ssh.download_file("/remote/test.txt", local_path)
        
        assert success is True
        assert mock_run.call_count == 2
        assert mock_sleep.call_count == 1
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_upload_file_success(self, mock_exists, mock_run):
        """Test successful file upload."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        ssh = SSHTransfer(host="test.host.com")
        success = ssh.upload_file("/local/test.txt", "/remote/test.txt")
        
        assert success is True
        mock_run.assert_called_once()
    
    @patch('pathlib.Path.exists')
    def test_upload_file_not_found(self, mock_exists):
        """Test upload when local file doesn't exist."""
        mock_exists.return_value = False
        
        ssh = SSHTransfer(host="test.host.com")
        success = ssh.upload_file("/local/missing.txt", "/remote/test.txt")
        
        assert success is False
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_upload_file_permission_denied(self, mock_exists, mock_run):
        """Test upload with permission denied on remote."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="scp: /remote/test.txt: Permission denied"
        )
        
        ssh = SSHTransfer(host="test.host.com", retry_attempts=1)
        success = ssh.upload_file("/local/test.txt", "/remote/test.txt")
        
        assert success is False
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_upload_file_timeout(self, mock_exists, mock_run):
        """Test upload timeout."""
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="scp", timeout=600)
        
        ssh = SSHTransfer(host="test.host.com", retry_attempts=1)
        success = ssh.upload_file("/local/large.txt", "/remote/large.txt")
        
        assert success is False
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('time.sleep')
    def test_upload_retry_logic(self, mock_sleep, mock_exists, mock_run):
        """Test retry logic for file upload."""
        mock_exists.return_value = True
        # First attempt fails, second succeeds
        mock_run.side_effect = [
            Mock(returncode=1, stdout="", stderr="Network error"),
            Mock(returncode=0, stdout="", stderr="")
        ]
        
        ssh = SSHTransfer(host="test.host.com", retry_attempts=2, retry_delay=1)
        success = ssh.upload_file("/local/test.txt", "/remote/test.txt")
        
        assert success is True
        assert mock_run.call_count == 2
        assert mock_sleep.call_count == 1
    
    @patch('subprocess.run')
    @patch('pathlib.Path.mkdir')
    def test_custom_timeout_values(self, mock_mkdir, mock_run):
        """Test that custom timeout values are properly used."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        ssh = SSHTransfer(
            host="test.host.com",
            connection_timeout=45,
            transfer_timeout=900
        )
        
        # Test connection timeout
        ssh.test_connection()
        assert mock_run.call_args.kwargs['timeout'] == 45
        
        # Test transfer timeout
        ssh.download_file("/remote/test.txt", "/local/test.txt")
        assert mock_run.call_args.kwargs['timeout'] == 900


class TestHARemoteManager:
    """Tests for HARemoteManager class."""
    
    @patch('ssh_transfer.SSHTransfer')
    def test_init_with_config(self, mock_ssh_class):
        """Test HARemoteManager initialization with configuration."""
        config = {
            'host': 'ha.local',
            'user': 'admin',
            'port': 2222,
            'key_path': '~/.ssh/ha_key',
            'connection_timeout': 45,
            'transfer_timeout': 900,
            'retry_attempts': 5,
            'retry_delay': 3,
            'remote_config_path': '/config'
        }
        
        manager = HARemoteManager(config)
        
        # Verify SSHTransfer was initialized with correct parameters
        mock_ssh_class.assert_called_once_with(
            host='ha.local',
            user='admin',
            port=2222,
            key_path='~/.ssh/ha_key',
            password=None,
            connection_timeout=45,
            transfer_timeout=900,
            retry_attempts=5,
            retry_delay=3
        )
    
    @patch('ssh_transfer.SSHTransfer')
    def test_init_with_defaults(self, mock_ssh_class):
        """Test HARemoteManager with default values."""
        config = {
            'host': 'ha.local'
        }
        
        manager = HARemoteManager(config)
        
        # Verify defaults were used
        call_args = mock_ssh_class.call_args
        assert call_args.kwargs['user'] == 'root'
        assert call_args.kwargs['port'] == 22
        assert call_args.kwargs['connection_timeout'] == 30
        assert call_args.kwargs['transfer_timeout'] == 600
        assert call_args.kwargs['retry_attempts'] == 3
        assert call_args.kwargs['retry_delay'] == 2
    
    @patch('ssh_transfer.SSHTransfer')
    def test_export_config_success(self, mock_ssh_class, temp_dir):
        """Test successful configuration export."""
        # Mock the SSH transfer object
        mock_ssh = Mock()
        mock_ssh.test_connection.return_value = (True, "Connected")
        mock_ssh.download_directory.return_value = True
        mock_ssh_class.return_value = mock_ssh
        
        config = {'host': 'ha.local'}
        manager = HARemoteManager(config)
        
        export_dir = os.path.join(temp_dir, "export")
        success = manager.export_config(export_dir)
        
        assert success is True
        mock_ssh.test_connection.assert_called_once()
        mock_ssh.download_directory.assert_called_once()
    
    @patch('ssh_transfer.SSHTransfer')
    def test_export_config_connection_failure(self, mock_ssh_class):
        """Test export when connection fails."""
        mock_ssh = Mock()
        mock_ssh.test_connection.return_value = (False, "Connection failed")
        mock_ssh_class.return_value = mock_ssh
        
        config = {'host': 'ha.local'}
        manager = HARemoteManager(config)
        
        success = manager.export_config("/tmp/export")
        
        assert success is False
        mock_ssh.test_connection.assert_called_once()
        mock_ssh.download_directory.assert_not_called()
    
    @patch('ssh_transfer.SSHTransfer')
    def test_import_config_with_backup(self, mock_ssh_class):
        """Test import with backup creation."""
        mock_ssh = Mock()
        mock_ssh.test_connection.return_value = (True, "Connected")
        mock_ssh.backup_remote.return_value = (True, "/backup/path")
        mock_ssh.upload_directory.return_value = True
        mock_ssh.check_config.return_value = (True, "Valid")
        mock_ssh_class.return_value = mock_ssh
        
        config = {'host': 'ha.local'}
        manager = HARemoteManager(config)
        
        success = manager.import_config("/local/config", create_backup=True)
        
        assert success is True
        mock_ssh.backup_remote.assert_called_once()
        mock_ssh.upload_directory.assert_called_once()
        mock_ssh.check_config.assert_called_once()


class TestTimeoutConfiguration:
    """Tests for timeout configuration and override."""
    
    @patch('subprocess.run')
    @patch('pathlib.Path.mkdir')
    def test_timeout_from_config(self, mock_mkdir, mock_run):
        """Test that timeout values from config are properly applied."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Create SSH transfer with specific timeouts
        ssh = SSHTransfer(
            host="test.host.com",
            connection_timeout=50,
            transfer_timeout=1000
        )
        
        # Test connection uses connection_timeout
        ssh.test_connection()
        assert mock_run.call_args.kwargs['timeout'] == 50
        
        # Test download uses transfer_timeout
        mock_run.reset_mock()
        ssh.download_file("/remote/file.txt", "/local/file.txt")
        assert mock_run.call_args.kwargs['timeout'] == 1000
    
    @patch('subprocess.run')
    def test_command_timeout_override(self, mock_run):
        """Test command timeout override."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        ssh = SSHTransfer(host="test.host.com", connection_timeout=30)
        
        # Execute command with custom timeout
        ssh.execute_command("long_command", timeout=200)
        
        assert mock_run.call_args.kwargs['timeout'] == 200
