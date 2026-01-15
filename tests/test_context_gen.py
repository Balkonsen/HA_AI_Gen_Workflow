"""
Unit tests for ha_ai_context_gen.py
Tests the HAContextGenerator class and related functions.
"""
import pytest
import json
import yaml
from pathlib import Path
import sys
import os

# Add bin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

from ha_ai_context_gen import HAContextGenerator, HAYAMLLoader


class TestHAContextGenerator:
    """Test HAContextGenerator class"""
    
    def test_init(self, temp_dir):
        """Test initialization of HAContextGenerator"""
        generator = HAContextGenerator(temp_dir)
        assert generator.export_path == temp_dir
        assert 'system_overview' in generator.context
        assert 'integrations' in generator.context
        assert 'entities' in generator.context
        assert 'devices' in generator.context
        assert 'automations' in generator.context
        assert 'scripts' in generator.context
        assert 'addons' in generator.context
        assert 'capabilities' in generator.context
        assert 'recommendations' in generator.context
    
    def test_context_initial_structure(self, temp_dir):
        """Test that context has correct initial structure"""
        generator = HAContextGenerator(temp_dir)
        
        # All top-level keys should be empty dicts or lists
        assert generator.context['system_overview'] == {}
        assert generator.context['integrations'] == {}
        assert generator.context['entities'] == {}
        assert generator.context['devices'] == {}
        assert generator.context['automations'] == {}
        assert generator.context['scripts'] == {}
        assert generator.context['addons'] == {}
        assert generator.context['capabilities'] == {}
        assert generator.context['recommendations'] == []


class TestSafeYamlLoad:
    """Test YAML loading functionality"""
    
    def test_safe_yaml_load_valid(self, temp_dir):
        """Test loading valid YAML file"""
        yaml_file = Path(temp_dir) / 'test.yaml'
        yaml_file.write_text('key: value\nlist:\n  - item1\n  - item2')
        
        generator = HAContextGenerator(temp_dir)
        result = generator.safe_yaml_load(str(yaml_file))
        
        assert result is not None
        assert result['key'] == 'value'
        assert result['list'] == ['item1', 'item2']
    
    def test_safe_yaml_load_with_ha_tags(self, temp_dir):
        """Test loading YAML with Home Assistant specific tags"""
        yaml_file = Path(temp_dir) / 'config.yaml'
        yaml_file.write_text("""
homeassistant:
  name: Test Home
  latitude: !secret latitude
  longitude: !secret longitude
automation: !include automations.yaml
script: !include scripts.yaml
""")
        
        generator = HAContextGenerator(temp_dir)
        result = generator.safe_yaml_load(str(yaml_file))
        
        assert result is not None
        assert 'homeassistant' in result
        assert result['homeassistant']['name'] == 'Test Home'
        # !secret tags should be preserved as strings
        assert '!secret latitude' in str(result['homeassistant']['latitude'])
    
    def test_safe_yaml_load_invalid_yaml(self, temp_dir):
        """Test loading invalid YAML returns structure with error info"""
        yaml_file = Path(temp_dir) / 'invalid.yaml'
        yaml_file.write_text('key: value\n  invalid: indentation\n- broken')
        
        generator = HAContextGenerator(temp_dir)
        result = generator.safe_yaml_load(str(yaml_file))
        
        # Should return a dict with _parse_error or None
        if result is not None:
            assert '_parse_error' in result or '_raw_content' in result
    
    def test_safe_yaml_load_nonexistent_file(self, temp_dir):
        """Test loading non-existent file returns None"""
        generator = HAContextGenerator(temp_dir)
        result = generator.safe_yaml_load(str(Path(temp_dir) / 'nonexistent.yaml'))
        
        assert result is None


class TestAnalyzeConfiguration:
    """Test configuration analysis"""
    
    def test_analyze_configuration_with_valid_config(self, temp_dir):
        """Test analyzing valid configuration.yaml"""
        config_dir = Path(temp_dir) / 'config'
        config_dir.mkdir(parents=True)
        
        config_content = """
homeassistant:
  name: Test Home
  unit_system: metric
  time_zone: Europe/Berlin
light:
switch:
sensor:
automation: !include automations.yaml
"""
        (config_dir / 'configuration.yaml').write_text(config_content)
        
        generator = HAContextGenerator(temp_dir)
        generator.analyze_configuration()
        
        assert 'configured_platforms' in generator.context['system_overview']
        # Should find top-level keys
        platforms = generator.context['system_overview']['configured_platforms']
        assert 'homeassistant' in platforms
    
    def test_analyze_configuration_missing_file(self, temp_dir):
        """Test analyzing when configuration.yaml doesn't exist"""
        generator = HAContextGenerator(temp_dir)
        generator.analyze_configuration()
        
        # Should not crash, context should remain empty or minimal
        assert generator.context['system_overview'] == {} or 'configured_platforms' not in generator.context['system_overview']


class TestAnalyzeEntities:
    """Test entity analysis"""
    
    def test_analyze_entities_with_data(self, temp_dir):
        """Test analyzing entities from registry file"""
        diagnostics_dir = Path(temp_dir) / 'diagnostics'
        diagnostics_dir.mkdir(parents=True)
        
        entities_data = {
            'total_entities': 5,
            'entities_by_domain': {
                'light': ['light.living_room', 'light.bedroom'],
                'sensor': ['sensor.temperature', 'sensor.humidity'],
                'switch': ['switch.outlet']
            },
            'entities_by_platform': {
                'hue': ['light.living_room', 'light.bedroom'],
                'mqtt': ['sensor.temperature', 'sensor.humidity', 'switch.outlet']
            },
            'disabled_entities': ['sensor.humidity']
        }
        
        (diagnostics_dir / 'entities_registry.json').write_text(json.dumps(entities_data))
        
        generator = HAContextGenerator(temp_dir)
        generator.analyze_entities()
        
        assert generator.context['entities']['total'] == 5
        assert generator.context['entities']['by_domain']['light'] == 2
        assert generator.context['entities']['by_domain']['sensor'] == 2
        assert generator.context['entities']['disabled_count'] == 1
        assert generator.context['entities']['active_count'] == 4
    
    def test_analyze_entities_missing_file(self, temp_dir):
        """Test analyzing entities when file doesn't exist"""
        generator = HAContextGenerator(temp_dir)
        generator.analyze_entities()
        
        # Should not crash
        assert generator.context['entities'] == {}


class TestAnalyzeDevices:
    """Test device analysis"""
    
    def test_analyze_devices_with_data(self, temp_dir):
        """Test analyzing devices from registry file"""
        diagnostics_dir = Path(temp_dir) / 'diagnostics'
        diagnostics_dir.mkdir(parents=True)
        
        devices_data = {
            'total_devices': 3,
            'devices_by_manufacturer': {
                'Philips': 2,
                'IKEA': 1
            },
            'devices_by_integration': {
                'hue': 2,
                'tradfri': 1
            }
        }
        
        (diagnostics_dir / 'devices_registry.json').write_text(json.dumps(devices_data))
        
        generator = HAContextGenerator(temp_dir)
        generator.analyze_devices()
        
        assert generator.context['devices']['total'] == 3
        assert generator.context['devices']['by_manufacturer']['Philips'] == 2
        assert generator.context['devices']['by_integration']['hue'] == 2


class TestAnalyzeAutomations:
    """Test automation analysis"""
    
    def test_analyze_automations_with_data(self, temp_dir):
        """Test analyzing automations from YAML file"""
        config_dir = Path(temp_dir) / 'config'
        config_dir.mkdir(parents=True)
        
        automations = [
            {
                'id': '1234',
                'alias': 'Turn on lights at sunset',
                'mode': 'single',
                'trigger': [{'platform': 'sun', 'event': 'sunset'}],
                'condition': [],
                'action': [{'service': 'light.turn_on'}]
            },
            {
                'id': '5678',
                'alias': 'Turn off lights at midnight',
                'trigger': {'platform': 'time', 'at': '00:00:00'},
                'action': {'service': 'light.turn_off'}
            }
        ]
        
        (config_dir / 'automations.yaml').write_text(yaml.dump(automations))
        
        generator = HAContextGenerator(temp_dir)
        generator.analyze_automations()
        
        assert generator.context['automations']['total'] == 2
        assert len(generator.context['automations']['list']) == 2
        assert generator.context['automations']['list'][0]['alias'] == 'Turn on lights at sunset'


class TestAnalyzeScripts:
    """Test script analysis"""
    
    def test_analyze_scripts_with_data(self, temp_dir):
        """Test analyzing scripts from YAML file"""
        config_dir = Path(temp_dir) / 'config'
        config_dir.mkdir(parents=True)
        
        scripts = {
            'morning_routine': {
                'alias': 'Morning Routine',
                'sequence': [
                    {'service': 'light.turn_on'},
                    {'delay': '00:00:05'},
                    {'service': 'media_player.play_media'}
                ]
            },
            'goodnight': {
                'alias': 'Goodnight',
                'sequence': [{'service': 'light.turn_off'}]
            }
        }
        
        (config_dir / 'scripts.yaml').write_text(yaml.dump(scripts))
        
        generator = HAContextGenerator(temp_dir)
        generator.analyze_scripts()
        
        assert generator.context['scripts']['total'] == 2
        assert 'morning_routine' in generator.context['scripts']['list']
        assert 'goodnight' in generator.context['scripts']['list']


class TestDetermineCapabilities:
    """Test capability determination"""
    
    def test_determine_capabilities_with_integrations(self, temp_dir):
        """Test capability determination based on integrations"""
        generator = HAContextGenerator(temp_dir)
        
        # Set up context with integrations
        generator.context['integrations'] = {
            'configured': [
                {'domain': 'light'},
                {'domain': 'media_player'},
                {'domain': 'climate'},
                {'domain': 'person'},
                {'domain': 'weather'},
                {'domain': 'sensor'}
            ],
            'by_category': {
                'media': ['cast'],
                'lighting': [],
                'climate': [],
                'security': [],
                'network': [],
                'voice': [],
                'other': []
            }
        }
        generator.context['addons'] = {'installed': []}
        
        generator.determine_capabilities()
        
        capabilities = generator.context['capabilities']['available']
        assert 'media_control' in capabilities
        assert 'lighting_control' in capabilities
        assert 'climate_control' in capabilities
        assert 'presence_detection' in capabilities
        assert 'weather_monitoring' in capabilities
        assert 'sensor_monitoring' in capabilities


class TestGenerateRecommendations:
    """Test recommendation generation"""
    
    def test_generate_recommendations_no_automations(self, temp_dir):
        """Test that recommendations suggest automations when none exist"""
        generator = HAContextGenerator(temp_dir)
        
        generator.context['integrations'] = {
            'configured': [{'domain': 'light'}],
            'by_category': {'media': [], 'lighting': [], 'climate': [], 'security': [], 'network': [], 'voice': [], 'other': []}
        }
        generator.context['automations'] = {'total': 0}
        generator.context['addons'] = {'installed': []}
        
        generator.generate_recommendations()
        
        assert len(generator.context['recommendations']) > 0
        # Should recommend creating automations
        assert any('automation' in rec['type'].lower() for rec in generator.context['recommendations'])


class TestGenerateAIPrompt:
    """Test AI prompt generation"""
    
    def test_generate_ai_prompt(self, temp_dir):
        """Test AI prompt generation produces valid markdown"""
        generator = HAContextGenerator(temp_dir)
        
        # Set up minimal context
        generator.context = {
            'system_overview': {'configured_platforms': ['light', 'switch']},
            'integrations': {
                'configured': [{'domain': 'light'}],
                'custom_components': [],
                'by_category': {'media': [], 'lighting': ['light'], 'climate': [], 'security': [], 'network': [], 'voice': [], 'other': []}
            },
            'entities': {'total': 10, 'active_count': 8, 'disabled_count': 2, 'by_domain': {'light': 5, 'switch': 5}},
            'devices': {'total': 3, 'by_manufacturer': {'Philips': 3}},
            'automations': {'total': 2, 'list': [{'alias': 'Test', 'triggers': 1, 'actions': 1}]},
            'scripts': {'total': 1},
            'addons': {'total': 2, 'by_category': {'database': [], 'network': [], 'media': [], 'automation': [], 'monitoring': [], 'other': []}},
            'capabilities': {'available': ['lighting_control']},
            'recommendations': []
        }
        
        prompt = generator.generate_ai_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert 'Home Assistant Configuration Context' in prompt
        assert 'Total Integrations' in prompt
        assert 'Total Entities' in prompt


class TestHAYAMLLoader:
    """Test custom YAML loader"""
    
    def test_include_tag(self, temp_dir):
        """Test !include tag handling"""
        yaml_content = "automation: !include automations.yaml"
        result = yaml.load(yaml_content, Loader=HAYAMLLoader)
        
        assert 'automation' in result
        assert '!include' in str(result['automation'])
    
    def test_secret_tag(self, temp_dir):
        """Test !secret tag handling"""
        yaml_content = "password: !secret my_password"
        result = yaml.load(yaml_content, Loader=HAYAMLLoader)
        
        assert 'password' in result
        assert '!secret' in str(result['password'])
    
    def test_input_tag(self, temp_dir):
        """Test !input tag handling"""
        yaml_content = "brightness: !input brightness_level"
        result = yaml.load(yaml_content, Loader=HAYAMLLoader)
        
        assert 'brightness' in result
        assert '!input' in str(result['brightness'])
