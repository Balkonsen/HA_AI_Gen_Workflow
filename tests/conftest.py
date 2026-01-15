"""
Pytest configuration and fixtures for HA AI Gen Workflow tests
"""
import pytest
import os
import tempfile
import shutil
import json
import yaml
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_ha_config(temp_dir):
    """Create a mock Home Assistant configuration"""
    config_dir = Path(temp_dir) / "config"
    config_dir.mkdir(parents=True)
    
    # Create configuration.yaml
    config = {
        'homeassistant': {
            'name': 'Test Home',
            'latitude': '!secret latitude',
            'longitude': '!secret longitude',
            'elevation': 100,
            'unit_system': 'metric',
            'time_zone': 'Europe/Berlin'
        },
        'automation': '!include automations.yaml',
        'script': '!include scripts.yaml',
        'scene': '!include scenes.yaml'
    }
    
    with open(config_dir / 'configuration.yaml', 'w') as f:
        yaml.dump(config, f)
    
    # Create empty files
    for file in ['automations.yaml', 'scripts.yaml', 'scenes.yaml']:
        (config_dir / file).touch()
    
    # Create secrets.yaml
    secrets = {
        'latitude': 52.5200,
        'longitude': 13.4050,
        'ha_token': 'test_token_12345',
        'db_password': 'super_secret_password'
    }
    
    with open(config_dir / 'secrets.yaml', 'w') as f:
        yaml.dump(secrets, f)
    
    return config_dir


@pytest.fixture
def mock_export_data():
    """Create mock export data"""
    return {
        'entities': [
            {
                'entity_id': 'light.living_room',
                'state': 'on',
                'attributes': {
                    'friendly_name': 'Living Room Light',
                    'brightness': 255
                }
            },
            {
                'entity_id': 'sensor.temperature',
                'state': '22.5',
                'attributes': {
                    'friendly_name': 'Temperature Sensor',
                    'unit_of_measurement': '°C'
                }
            }
        ],
        'devices': [
            {
                'id': 'device_1',
                'name': 'Smart Light',
                'manufacturer': 'Philips',
                'model': 'Hue'
            }
        ],
        'automations': [],
        'scripts': []
    }


@pytest.fixture
def mock_diagnostic_data():
    """Create mock Home Assistant diagnostic data"""
    return {
        'home_assistant': {
            'installation_type': 'Home Assistant OS',
            'version': '2024.1.0',
            'dev': False,
            'hassio': True,
            'supervisor': '2024.01.0',
            'docker': True,
            'virtualenv': False,
            'python_version': '3.11.6',
            'os_name': 'Linux',
            'os_version': '6.1.21-v8',
            'arch': 'aarch64',
            'timezone': 'Europe/Berlin'
        },
        'custom_components': {},
        'integration_manifest': {},
        'config_entries': []
    }


@pytest.fixture
def mock_secrets():
    """Create mock secrets data"""
    return {
        'latitude': 52.5200,
        'longitude': 13.4050,
        'ha_token': 'test_token_12345',
        'db_password': 'super_secret_password',
        'email': 'test@example.com',
        'api_key': 'sk_test_1234567890'
    }
