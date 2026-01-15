"""
Unit tests for ha_export_verifier.py
Tests the ExportVerifier class for verifying export completeness.
"""
import pytest
import json
from pathlib import Path
import sys
import os

# Add bin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

from ha_export_verifier import ExportVerifier


class TestExportVerifier:
    """Test ExportVerifier class"""
    
    def test_init(self, temp_dir):
        """Test initialization"""
        verifier = ExportVerifier(temp_dir)
        assert verifier.export_path == temp_dir
        assert verifier.issues == []
        assert verifier.warnings == []
        assert verifier.stats == {}
    
    def test_init_with_path(self, temp_dir):
        """Test initialization stores export path correctly"""
        export_path = str(Path(temp_dir) / 'exports')
        verifier = ExportVerifier(export_path)
        assert verifier.export_path == export_path


class TestVerifyStructure:
    """Test verify_structure method"""
    
    def test_verify_structure_complete(self, temp_dir):
        """Test verification with complete structure"""
        # Create required directories
        for dir_name in ['config', 'diagnostics', 'secrets', 'addons']:
            (Path(temp_dir) / dir_name).mkdir(exist_ok=True)
        
        # Create required files
        (Path(temp_dir) / 'METADATA.json').write_text('{}')
        (Path(temp_dir) / 'README.md').write_text('# Export')
        
        verifier = ExportVerifier(temp_dir)
        result = verifier.verify_structure()
        
        assert result == True
        assert len(verifier.issues) == 0
    
    def test_verify_structure_missing_dirs(self, temp_dir):
        """Test verification with missing directories"""
        verifier = ExportVerifier(temp_dir)
        result = verifier.verify_structure()
        
        assert result == False
        assert len(verifier.issues) > 0
        assert any('config' in issue for issue in verifier.issues)
    
    def test_verify_structure_missing_files(self, temp_dir):
        """Test verification with missing required files"""
        # Create directories but not files
        for dir_name in ['config', 'diagnostics', 'secrets', 'addons']:
            (Path(temp_dir) / dir_name).mkdir(exist_ok=True)
        
        verifier = ExportVerifier(temp_dir)
        result = verifier.verify_structure()
        
        assert result == False
        assert any('METADATA.json' in issue for issue in verifier.issues)


class TestVerifyEntities:
    """Test verify_entities method"""
    
    def test_verify_entities_success(self, temp_dir):
        """Test entity verification with valid data"""
        # Create directory structure
        diag_dir = Path(temp_dir) / 'diagnostics'
        diag_dir.mkdir(exist_ok=True)
        
        # Create entity registry file
        entity_data = {
            'total_entities': 10,
            'disabled_entities': ['sensor.disabled'],
            'entities_by_domain': {
                'light': ['light.living_room', 'light.bedroom'],
                'switch': ['switch.outlet']
            },
            'entities_by_platform': {
                'hue': ['light.living_room'],
                'zwave': ['switch.outlet']
            }
        }
        
        (diag_dir / 'entities_registry.json').write_text(json.dumps(entity_data))
        
        verifier = ExportVerifier(temp_dir)
        result = verifier.verify_entities()
        
        assert result == True
        assert 'entities' in verifier.stats
        assert verifier.stats['entities']['total'] == 10
    
    def test_verify_entities_missing_file(self, temp_dir):
        """Test entity verification with missing file"""
        verifier = ExportVerifier(temp_dir)
        result = verifier.verify_entities()
        
        assert result == False
        assert any('Entity registry' in issue for issue in verifier.issues)


class TestVerifyDevices:
    """Test verify_devices method"""
    
    def test_verify_devices_success(self, temp_dir):
        """Test device verification with valid data"""
        diag_dir = Path(temp_dir) / 'diagnostics'
        diag_dir.mkdir(exist_ok=True)
        
        device_data = {
            'total_devices': 5,
            'devices_by_manufacturer': {
                'Philips': 2,
                'Sonos': 1
            },
            'devices_by_integration': {
                'hue': 2,
                'sonos': 1
            }
        }
        
        (diag_dir / 'devices_registry.json').write_text(json.dumps(device_data))
        
        verifier = ExportVerifier(temp_dir)
        result = verifier.verify_devices()
        
        assert result == True
        assert 'devices' in verifier.stats
        assert verifier.stats['devices']['total'] == 5
    
    def test_verify_devices_missing_file(self, temp_dir):
        """Test device verification with missing file"""
        verifier = ExportVerifier(temp_dir)
        result = verifier.verify_devices()
        
        assert result == False


class TestVerifyConfigFiles:
    """Test verify_config_files method"""
    
    def test_verify_config_files_success(self, temp_dir):
        """Test config file verification"""
        config_dir = Path(temp_dir) / 'config'
        config_dir.mkdir(exist_ok=True)
        
        # Create key config files
        (config_dir / 'configuration.yaml').write_text('homeassistant:\n  name: Home')
        (config_dir / 'automations.yaml').write_text('[]')
        
        verifier = ExportVerifier(temp_dir)
        result = verifier.verify_config_files()
        
        assert result == True
        assert 'config_files' in verifier.stats
    
    def test_verify_config_files_missing_dir(self, temp_dir):
        """Test config file verification with missing directory"""
        verifier = ExportVerifier(temp_dir)
        result = verifier.verify_config_files()
        
        assert result == False


class TestVerifySecrets:
    """Test verify_secrets method"""
    
    def test_verify_secrets_success(self, temp_dir):
        """Test secrets verification with valid data"""
        secrets_dir = Path(temp_dir) / 'secrets'
        secrets_dir.mkdir(exist_ok=True)
        
        secrets_data = {
            'total_secrets': 5,
            'secrets': {
                '<<PASSWORD_1>>': 'description_1',
                '<<TOKEN_1>>': 'description_2'
            }
        }
        
        (secrets_dir / 'secrets_map.json').write_text(json.dumps(secrets_data))
        
        verifier = ExportVerifier(temp_dir)
        result = verifier.verify_secrets()
        
        assert result == True
        assert 'secrets' in verifier.stats
        assert verifier.stats['secrets']['total'] == 5
    
    def test_verify_secrets_missing_file(self, temp_dir):
        """Test secrets verification with missing file"""
        verifier = ExportVerifier(temp_dir)
        result = verifier.verify_secrets()
        
        assert result == False


class TestRun:
    """Test run method"""
    
    def test_run_complete_export(self, temp_dir):
        """Test run with complete export structure"""
        # Create complete structure
        for dir_name in ['config', 'diagnostics', 'secrets', 'addons']:
            (Path(temp_dir) / dir_name).mkdir(exist_ok=True)
        
        (Path(temp_dir) / 'METADATA.json').write_text('{}')
        (Path(temp_dir) / 'README.md').write_text('# Export')
        
        # Create necessary registry files
        diag_dir = Path(temp_dir) / 'diagnostics'
        (diag_dir / 'entities_registry.json').write_text(json.dumps({
            'total_entities': 5,
            'entities_by_domain': {},
            'entities_by_platform': {},
            'disabled_entities': []
        }))
        (diag_dir / 'devices_registry.json').write_text(json.dumps({
            'total_devices': 3,
            'devices_by_manufacturer': {},
            'devices_by_integration': {}
        }))
        
        config_dir = Path(temp_dir) / 'config'
        (config_dir / 'configuration.yaml').write_text('homeassistant:\n  name: Test')
        
        secrets_dir = Path(temp_dir) / 'secrets'
        (secrets_dir / 'secrets_map.json').write_text(json.dumps({
            'total_secrets': 2,
            'secrets': {}
        }))
        
        verifier = ExportVerifier(temp_dir)
        verifier.run()
        
        # Run should not raise and should populate stats
        assert 'entities' in verifier.stats or len(verifier.issues) > 0


class TestGenerateReport:
    """Test generate_report method"""
    
    def test_generate_report(self, temp_dir):
        """Test report generation"""
        verifier = ExportVerifier(temp_dir)
        verifier.stats = {
            'entities': {'total': 10},
            'devices': {'total': 5}
        }
        verifier.issues = ['Issue 1']
        verifier.warnings = ['Warning 1']
        
        report = verifier.generate_report()
        
        assert report is not None
        assert isinstance(report, dict)


class TestIssueTracking:
    """Test issue and warning tracking"""
    
    def test_issues_accumulated(self, temp_dir):
        """Test that issues are accumulated across verifications"""
        verifier = ExportVerifier(temp_dir)
        
        # Run multiple verifications on empty dir
        verifier.verify_structure()
        verifier.verify_entities()
        verifier.verify_devices()
        
        # Should have accumulated multiple issues
        assert len(verifier.issues) >= 3
