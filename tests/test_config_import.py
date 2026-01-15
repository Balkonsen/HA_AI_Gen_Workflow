"""
Unit tests for ha_config_import.py
Tests the HAConfigImporter class and related functions.
"""
import pytest
import json
import yaml
from pathlib import Path
import sys
import os

# Add bin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

from ha_config_import import HAConfigImporter


class TestHAConfigImporter:
    """Test HAConfigImporter class"""
    
    def test_init(self, temp_dir):
        """Test initialization with correct constructor signature"""
        import_path = Path(temp_dir) / 'imports'
        secrets_file = Path(temp_dir) / 'secrets_map.json'
        
        # Create a valid secrets file
        secrets_file.write_text(json.dumps({'secrets': {}}))
        
        importer = HAConfigImporter(
            import_path=str(import_path),
            secrets_file=str(secrets_file)
        )
        
        assert importer.import_path == str(import_path)
        assert importer.secrets_file == str(secrets_file)
        assert importer.secrets_map == {}
        assert importer.reverse_map == {}
        assert importer.dry_run == True
        assert importer.changes_log == []
    
    def test_init_attributes(self, temp_dir):
        """Test that importer has expected attributes"""
        import_path = str(Path(temp_dir) / 'imports')
        secrets_file = str(Path(temp_dir) / 'secrets.json')
        
        importer = HAConfigImporter(import_path, secrets_file)
        
        assert hasattr(importer, 'import_path')
        assert hasattr(importer, 'secrets_file')
        assert hasattr(importer, 'secrets_map')
        assert hasattr(importer, 'reverse_map')
        assert hasattr(importer, 'config_backup_path')
        assert hasattr(importer, 'dry_run')
        assert hasattr(importer, 'changes_log')


class TestLoadSecrets:
    """Test secrets loading functionality"""
    
    def test_load_secrets_valid(self, temp_dir):
        """Test loading valid secrets file"""
        secrets_file = Path(temp_dir) / 'secrets_map.json'
        secrets_data = {
            'secrets': {
                '<<PASSWORD_1>>': 'actual_password',
                '<<TOKEN_1>>': 'actual_token',
                '<<API_KEY_1>>': 'actual_api_key'
            }
        }
        secrets_file.write_text(json.dumps(secrets_data))
        
        importer = HAConfigImporter(temp_dir, str(secrets_file))
        result = importer.load_secrets()
        
        assert result == True
        assert len(importer.secrets_map) == 3
        assert importer.secrets_map['<<PASSWORD_1>>'] == 'actual_password'
        # Check reverse map was created
        assert importer.reverse_map['actual_password'] == '<<PASSWORD_1>>'
    
    def test_load_secrets_missing_file(self, temp_dir):
        """Test loading non-existent secrets file"""
        importer = HAConfigImporter(temp_dir, str(Path(temp_dir) / 'nonexistent.json'))
        result = importer.load_secrets()
        
        assert result == False
    
    def test_load_secrets_invalid_json(self, temp_dir):
        """Test loading invalid JSON secrets file"""
        secrets_file = Path(temp_dir) / 'invalid.json'
        secrets_file.write_text('not valid json {')
        
        importer = HAConfigImporter(temp_dir, str(secrets_file))
        result = importer.load_secrets()
        
        assert result == False


class TestRestoreSecrets:
    """Test secrets restoration functionality"""
    
    def test_restore_secrets_basic(self, temp_dir):
        """Test basic secret restoration"""
        secrets_file = Path(temp_dir) / 'secrets_map.json'
        secrets_data = {
            'secrets': {
                '<<PASSWORD_1>>': 'my_secret_password',
                '<<IP_1>>': '192.168.1.100'
            }
        }
        secrets_file.write_text(json.dumps(secrets_data))
        
        importer = HAConfigImporter(temp_dir, str(secrets_file))
        importer.load_secrets()
        
        text = 'password: <<PASSWORD_1>>\nhost: <<IP_1>>'
        result = importer.restore_secrets(text)
        
        assert result == 'password: my_secret_password\nhost: 192.168.1.100'
        assert len(importer.changes_log) == 2
    
    def test_restore_secrets_no_placeholders(self, temp_dir):
        """Test restoration with no placeholders in text"""
        secrets_file = Path(temp_dir) / 'secrets_map.json'
        secrets_file.write_text(json.dumps({'secrets': {'<<TEST>>': 'value'}}))
        
        importer = HAConfigImporter(temp_dir, str(secrets_file))
        importer.load_secrets()
        
        text = 'no placeholders here'
        result = importer.restore_secrets(text)
        
        assert result == 'no placeholders here'
    
    def test_restore_secrets_non_string(self, temp_dir):
        """Test restoration with non-string input"""
        importer = HAConfigImporter(temp_dir, str(Path(temp_dir) / 'secrets.json'))
        
        # Should handle non-string gracefully
        result = importer.restore_secrets(None)
        assert result is None
        
        result = importer.restore_secrets(123)
        assert result == 123


class TestProcessFile:
    """Test file processing functionality"""
    
    def test_process_file_dry_run(self, temp_dir):
        """Test file processing in dry run mode"""
        # Setup
        source_dir = Path(temp_dir) / 'source'
        source_dir.mkdir()
        dest_dir = Path(temp_dir) / 'dest'
        
        source_file = source_dir / 'config.yaml'
        source_file.write_text('key: value')
        
        dest_file = dest_dir / 'config.yaml'
        
        secrets_file = Path(temp_dir) / 'secrets.json'
        secrets_file.write_text(json.dumps({'secrets': {}}))
        
        importer = HAConfigImporter(temp_dir, str(secrets_file))
        importer.dry_run = True
        
        result = importer.process_file(str(source_file), str(dest_file))
        
        assert result == True
        # In dry run, file should not be created
        assert not dest_file.exists()
    
    def test_process_file_apply(self, temp_dir):
        """Test file processing with apply mode"""
        # Setup
        source_dir = Path(temp_dir) / 'source'
        source_dir.mkdir()
        dest_dir = Path(temp_dir) / 'dest'
        
        source_file = source_dir / 'config.yaml'
        source_file.write_text('key: value')
        
        dest_file = dest_dir / 'config.yaml'
        
        secrets_file = Path(temp_dir) / 'secrets.json'
        secrets_file.write_text(json.dumps({'secrets': {}}))
        
        importer = HAConfigImporter(temp_dir, str(secrets_file))
        importer.dry_run = False
        
        result = importer.process_file(str(source_file), str(dest_file))
        
        assert result == True
        assert dest_file.exists()
        assert dest_file.read_text() == 'key: value'
    
    def test_process_file_with_secrets(self, temp_dir):
        """Test file processing with secret restoration"""
        # Setup
        source_dir = Path(temp_dir) / 'source'
        source_dir.mkdir()
        dest_dir = Path(temp_dir) / 'dest'
        
        source_file = source_dir / 'config.yaml'
        source_file.write_text('password: <<PASSWORD_1>>')
        
        dest_file = dest_dir / 'config.yaml'
        
        secrets_file = Path(temp_dir) / 'secrets.json'
        secrets_file.write_text(json.dumps({'secrets': {'<<PASSWORD_1>>': 'secret123'}}))
        
        importer = HAConfigImporter(temp_dir, str(secrets_file))
        importer.load_secrets()
        importer.dry_run = False
        
        result = importer.process_file(str(source_file), str(dest_file))
        
        assert result == True
        assert dest_file.exists()
        assert dest_file.read_text() == 'password: secret123'


class TestImportConfigFiles:
    """Test configuration import functionality"""
    
    def test_import_config_files_no_config_dir(self, temp_dir):
        """Test import when no config directory exists"""
        secrets_file = Path(temp_dir) / 'secrets.json'
        secrets_file.write_text(json.dumps({'secrets': {}}))
        
        importer = HAConfigImporter(temp_dir, str(secrets_file))
        result = importer.import_config_files()
        
        assert result == False


class TestImportAddonConfigs:
    """Test add-on configuration import functionality"""
    
    def test_import_addon_configs_no_addons(self, temp_dir):
        """Test import when no addons directory exists"""
        secrets_file = Path(temp_dir) / 'secrets.json'
        secrets_file.write_text(json.dumps({'secrets': {}}))
        
        importer = HAConfigImporter(temp_dir, str(secrets_file))
        result = importer.import_addon_configs()
        
        # Should return True (not a failure, just no addons)
        assert result == True

