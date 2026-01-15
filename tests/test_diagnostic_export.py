"""
Unit tests for ha_diagnostic_export.py
Tests the HAConfigExporter class (note: actual class name in module).
"""
import pytest
import json
import re
from pathlib import Path
import sys
import os

# Add bin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

from ha_diagnostic_export import HAConfigExporter


class TestHAConfigExporter:
    """Test HAConfigExporter class"""
    
    def test_init(self, temp_dir):
        """Test initialization with default and custom output_dir"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        assert exporter.output_dir == temp_dir
        assert exporter.secrets_map == {}
        assert exporter.secret_counter == 0
        assert exporter.timestamp is not None
        assert exporter.export_name.startswith('ha_config_export_')
    
    def test_init_default(self):
        """Test initialization with default output directory"""
        exporter = HAConfigExporter()
        
        assert exporter.output_dir == '/tmp/ha_export'
    
    def test_sensitive_patterns_defined(self, temp_dir):
        """Test that sensitive patterns are properly defined"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        assert 'password' in exporter.sensitive_patterns
        assert 'token' in exporter.sensitive_patterns
        assert 'api_key' in exporter.sensitive_patterns
        assert 'secret' in exporter.sensitive_patterns
        assert 'email' in exporter.sensitive_patterns
        assert 'ip_address' in exporter.sensitive_patterns
        assert 'latitude' in exporter.sensitive_patterns
        assert 'longitude' in exporter.sensitive_patterns


class TestCreateExportStructure:
    """Test export directory structure creation"""
    
    def test_create_export_structure(self, temp_dir):
        """Test that export structure is created correctly"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        exporter.create_export_structure()
        
        export_path = Path(exporter.export_path)
        assert export_path.exists()
        assert (export_path / 'config').exists()
        assert (export_path / 'diagnostics').exists()
        assert (export_path / 'addons').exists()
        assert (export_path / 'secrets').exists()


class TestGenerateSecretPlaceholder:
    """Test secret placeholder generation"""
    
    def test_generate_secret_placeholder_new(self, temp_dir):
        """Test generating new placeholder for unknown value"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        placeholder = exporter.generate_secret_placeholder('password', 'my_secret')
        
        assert placeholder == '<<PASSWORD_1>>'
        assert 'my_secret' in exporter.secrets_map
        assert exporter.secrets_map['my_secret'] == '<<PASSWORD_1>>'
    
    def test_generate_secret_placeholder_existing(self, temp_dir):
        """Test that same value gets same placeholder"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        placeholder1 = exporter.generate_secret_placeholder('password', 'my_secret')
        placeholder2 = exporter.generate_secret_placeholder('password', 'my_secret')
        
        assert placeholder1 == placeholder2
        assert exporter.secret_counter == 1  # Counter only incremented once
    
    def test_generate_secret_placeholder_different_types(self, temp_dir):
        """Test placeholders for different secret types"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        pw_placeholder = exporter.generate_secret_placeholder('password', 'pw123')
        token_placeholder = exporter.generate_secret_placeholder('token', 'tok456')
        
        assert 'PASSWORD' in pw_placeholder
        assert 'TOKEN' in token_placeholder
        assert exporter.secret_counter == 2


class TestSanitizeText:
    """Test text sanitization functionality"""
    
    def test_sanitize_password(self, temp_dir):
        """Test password sanitization"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        text = 'password: mysecretpassword123'
        result = exporter.sanitize_text(text)
        
        assert 'mysecretpassword123' not in result
        assert '<<PASSWORD_' in result
    
    def test_sanitize_token(self, temp_dir):
        """Test token sanitization"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        text = 'token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
        result = exporter.sanitize_text(text)
        
        assert 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' not in result
    
    def test_sanitize_email(self, temp_dir):
        """Test email sanitization"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        text = 'contact: user@example.com'
        result = exporter.sanitize_text(text)
        
        assert 'user@example.com' not in result
    
    def test_sanitize_ip_address(self, temp_dir):
        """Test IP address sanitization"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        text = 'host: 192.168.1.100'
        result = exporter.sanitize_text(text)
        
        assert '192.168.1.100' not in result
    
    def test_sanitize_preserves_examples(self, temp_dir):
        """Test that example/placeholder values are not sanitized"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        # These should be skipped
        text = 'password: example_password'
        result = exporter.sanitize_text(text)
        
        # example values should be preserved
        assert 'example' in result.lower()
    
    def test_sanitize_non_string(self, temp_dir):
        """Test sanitization of non-string input"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        result = exporter.sanitize_text(123)
        assert result == 123
        
        result = exporter.sanitize_text(None)
        assert result is None


class TestExportYamlFile:
    """Test YAML file export functionality"""
    
    def test_export_yaml_file(self, temp_dir):
        """Test exporting and sanitizing YAML file"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        source_file = Path(temp_dir) / 'source.yaml'
        source_file.write_text('password: secret123\nname: test')
        
        dest_file = Path(temp_dir) / 'dest.yaml'
        
        result = exporter.export_yaml_file(str(source_file), str(dest_file))
        
        assert result == True
        assert dest_file.exists()
        
        content = dest_file.read_text()
        assert 'secret123' not in content
        assert 'name: test' in content
    
    def test_export_yaml_file_nonexistent(self, temp_dir):
        """Test exporting non-existent file"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        result = exporter.export_yaml_file(
            str(Path(temp_dir) / 'nonexistent.yaml'),
            str(Path(temp_dir) / 'dest.yaml')
        )
        
        assert result == False


class TestExportJsonFile:
    """Test JSON file export functionality"""
    
    def test_export_json_file(self, temp_dir):
        """Test exporting and sanitizing JSON file"""
        exporter = HAConfigExporter(output_dir=temp_dir)
        
        source_file = Path(temp_dir) / 'source.json'
        source_file.write_text('{"password": "secret123", "name": "test"}')
        
        dest_file = Path(temp_dir) / 'dest.json'
        
        result = exporter.export_json_file(str(source_file), str(dest_file))
        
        assert result == True
        assert dest_file.exists()
        
        content = dest_file.read_text()
        assert 'secret123' not in content
        assert '"name": "test"' in content


class TestDataValidation:
    """Test data validation"""
    
    def test_valid_json_export(self, temp_dir, mock_export_data):
        """Test that exported JSON is valid"""
        export_file = Path(temp_dir) / 'test_export.json'
        
        with open(export_file, 'w') as f:
            json.dump(mock_export_data, f)
        
        # Verify it can be loaded
        with open(export_file) as f:
            loaded_data = json.load(f)
        
        assert 'entities' in loaded_data
        assert 'devices' in loaded_data
        assert len(loaded_data['entities']) == 2
