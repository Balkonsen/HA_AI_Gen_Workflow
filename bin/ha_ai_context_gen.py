#!/usr/bin/env python3
"""
Home Assistant AI Context Generator
Generates optimized context files for AI assistants to understand your HA setup
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
import re

# Custom YAML loader to handle Home Assistant's !include directives
class HAYAMLLoader(yaml.SafeLoader):
    """Custom YAML loader that handles HA-specific tags"""
    pass

# Register custom constructors for HA tags
def include_constructor(loader, node):
    """Handle !include tags"""
    return f"!include {loader.construct_scalar(node)}"

def secret_constructor(loader, node):
    """Handle !secret tags"""
    return f"!secret {loader.construct_scalar(node)}"

def input_constructor(loader, node):
    """Handle !input tags"""
    return f"!input {loader.construct_scalar(node)}"

def env_var_constructor(loader, node):
    """Handle !env_var tags"""
    return f"!env_var {loader.construct_scalar(node)}"

# Register all common HA YAML tags
HAYAMLLoader.add_constructor('!include', include_constructor)
HAYAMLLoader.add_constructor('!include_dir_list', include_constructor)
HAYAMLLoader.add_constructor('!include_dir_named', include_constructor)
HAYAMLLoader.add_constructor('!include_dir_merge_list', include_constructor)
HAYAMLLoader.add_constructor('!include_dir_merge_named', include_constructor)
HAYAMLLoader.add_constructor('!secret', secret_constructor)
HAYAMLLoader.add_constructor('!input', input_constructor)
HAYAMLLoader.add_constructor('!env_var', env_var_constructor)

class HAContextGenerator:
    def __init__(self, export_path):
        self.export_path = export_path
        self.context = {
            'system_overview': {},
            'integrations': {},
            'entities': {},
            'devices': {},
            'automations': {},
            'scripts': {},
            'addons': {},
            'capabilities': {},
            'recommendations': []
        }
    
    def safe_yaml_load(self, file_path):
        """Safely load YAML file with HA-specific tags"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.load(f, Loader=HAYAMLLoader)
        except yaml.YAMLError as e:
            print(f"  Warning: YAML parsing error in {file_path}: {e}")
            # Try to load as plain text and extract what we can
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Return a minimal structure
                return {'_raw_content': content, '_parse_error': str(e)}
            except:
                return None
        except Exception as e:
            print(f"  Warning: Could not read {file_path}: {e}")
            return None
    
    def analyze_configuration(self):
        """Analyze configuration.yaml"""
        config_file = os.path.join(self.export_path, 'config', 'configuration.yaml')
        if os.path.exists(config_file):
            config = self.safe_yaml_load(config_file)
            
            if config and '_parse_error' not in config:
                self.context['system_overview']['configured_platforms'] = [
                    k for k in config.keys() if not k.startswith('_')
                ]
                
                # Extract key configurations
                if 'homeassistant' in config:
                    ha_config = config['homeassistant']
                    if isinstance(ha_config, dict):
                        self.context['system_overview']['unit_system'] = ha_config.get('unit_system', 'metric')
                        self.context['system_overview']['time_zone'] = ha_config.get('time_zone', 'Unknown')
                        self.context['system_overview']['external_url'] = ha_config.get('external_url', 'Not configured')
            elif config and '_parse_error' in config:
                print(f"  Note: configuration.yaml has custom tags - extracting basic info")
                # Extract platforms from raw content
                raw = config.get('_raw_content', '')
                platforms = re.findall(r'^([a-z_]+):', raw, re.MULTILINE)
                self.context['system_overview']['configured_platforms'] = list(set(platforms))
    
    def analyze_entities(self):
        """Analyze entity registry"""
        entities_file = os.path.join(self.export_path, 'diagnostics', 'entities_registry.json')
        if os.path.exists(entities_file):
            try:
                with open(entities_file, 'r') as f:
                    entity_data = json.load(f)
                
                self.context['entities'] = {
                    'total': entity_data.get('total_entities', 0),
                    'by_domain': {k: len(v) for k, v in entity_data.get('entities_by_domain', {}).items()},
                    'by_platform': {k: len(v) for k, v in entity_data.get('entities_by_platform', {}).items()},
                    'disabled_count': len(entity_data.get('disabled_entities', [])),
                    'active_count': entity_data.get('total_entities', 0) - len(entity_data.get('disabled_entities', [])),
                }
                
                print(f"  ✓ Loaded {self.context['entities']['total']} entities")
                
            except Exception as e:
                print(f"  Warning: Could not parse entities registry: {e}")
    
    def analyze_devices(self):
        """Analyze device registry"""
        devices_file = os.path.join(self.export_path, 'diagnostics', 'devices_registry.json')
        if os.path.exists(devices_file):
            try:
                with open(devices_file, 'r') as f:
                    device_data = json.load(f)
                
                self.context['devices'] = {
                    'total': device_data.get('total_devices', 0),
                    'by_manufacturer': device_data.get('devices_by_manufacturer', {}),
                    'by_integration': device_data.get('devices_by_integration', {}),
                }
                
                print(f"  ✓ Loaded {self.context['devices']['total']} devices")
                
            except Exception as e:
                print(f"  Warning: Could not parse devices registry: {e}")
    
    def analyze_integrations(self):
        """Analyze configured integrations"""
        integrations_file = os.path.join(self.export_path, 'diagnostics', 'integrations.json')
        if os.path.exists(integrations_file):
            try:
                with open(integrations_file, 'r') as f:
                    integ_data = json.load(f)
                
                self.context['integrations']['configured'] = integ_data.get('configured_integrations', [])
                self.context['integrations']['custom_components'] = integ_data.get('custom_components', [])
                
                # Categorize integrations
                categories = {
                    'media': [],
                    'lighting': [],
                    'climate': [],
                    'security': [],
                    'network': [],
                    'voice': [],
                    'other': []
                }
                
                for integration in integ_data.get('configured_integrations', []):
                    domain = integration.get('domain', '')
                    if any(x in domain for x in ['media', 'cast', 'spotify', 'plex']):
                        categories['media'].append(domain)
                    elif any(x in domain for x in ['light', 'hue', 'lifx']):
                        categories['lighting'].append(domain)
                    elif any(x in domain for x in ['climate', 'thermostat', 'nest']):
                        categories['climate'].append(domain)
                    elif any(x in domain for x in ['alarm', 'camera', 'lock', 'ring']):
                        categories['security'].append(domain)
                    elif any(x in domain for x in ['unifi', 'network', 'router']):
                        categories['network'].append(domain)
                    elif any(x in domain for x in ['alexa', 'google', 'siri']):
                        categories['voice'].append(domain)
                    else:
                        categories['other'].append(domain)
                
                self.context['integrations']['by_category'] = categories
                
            except Exception as e:
                print(f"Warning: Could not parse integrations: {e}")
    
    def analyze_automations(self):
        """Analyze automations"""
        auto_file = os.path.join(self.export_path, 'config', 'automations.yaml')
        if os.path.exists(auto_file):
            automations = self.safe_yaml_load(auto_file)
            
            if automations and not isinstance(automations, dict) or '_parse_error' not in automations:
                if not isinstance(automations, list):
                    automations = []
                
                auto_summary = []
                for auto in automations:
                    if isinstance(auto, dict):
                        summary = {
                            'id': auto.get('id', 'unknown'),
                            'alias': auto.get('alias', 'Unnamed'),
                            'mode': auto.get('mode', 'single'),
                            'triggers': len(auto.get('trigger', [])) if isinstance(auto.get('trigger'), list) else 1,
                            'conditions': len(auto.get('condition', [])) if isinstance(auto.get('condition'), list) else 0,
                            'actions': len(auto.get('action', [])) if isinstance(auto.get('action'), list) else 1
                        }
                        auto_summary.append(summary)
                
                self.context['automations']['total'] = len(auto_summary)
                self.context['automations']['list'] = auto_summary
                
                print(f"  ✓ Loaded {len(auto_summary)} automations")
    
    def analyze_scripts(self):
        """Analyze scripts"""
        script_file = os.path.join(self.export_path, 'config', 'scripts.yaml')
        if os.path.exists(script_file):
            scripts = self.safe_yaml_load(script_file)
            
            if scripts and isinstance(scripts, dict) and '_parse_error' not in scripts:
                self.context['scripts']['total'] = len(scripts)
                self.context['scripts']['list'] = list(scripts.keys())
                
                print(f"  ✓ Loaded {len(scripts)} scripts")
    
    def analyze_addons(self):
        """Analyze add-ons"""
        addon_file = os.path.join(self.export_path, 'addons', 'addons_summary.json')
        if os.path.exists(addon_file):
            try:
                with open(addon_file, 'r') as f:
                    addon_data = json.load(f)
                
                self.context['addons']['installed'] = addon_data.get('installed_addons', [])
                self.context['addons']['total'] = len(addon_data.get('installed_addons', []))
                
                # Categorize add-ons
                addon_categories = {
                    'database': [],
                    'network': [],
                    'media': [],
                    'automation': [],
                    'monitoring': [],
                    'other': []
                }
                
                for addon in addon_data.get('installed_addons', []):
                    name = addon.get('name', '').lower()
                    if any(x in name for x in ['mysql', 'postgres', 'influx', 'maria']):
                        addon_categories['database'].append(addon['name'])
                    elif any(x in name for x in ['mqtt', 'ssh', 'dns', 'wireguard', 'vpn']):
                        addon_categories['network'].append(addon['name'])
                    elif any(x in name for x in ['plex', 'music', 'cast', 'media']):
                        addon_categories['media'].append(addon['name'])
                    elif any(x in name for x in ['node', 'appdaemon', 'python']):
                        addon_categories['automation'].append(addon['name'])
                    elif any(x in name for x in ['grafana', 'log', 'monitor']):
                        addon_categories['monitoring'].append(addon['name'])
                    else:
                        addon_categories['other'].append(addon['name'])
                
                self.context['addons']['by_category'] = addon_categories
                
            except Exception as e:
                print(f"Warning: Could not parse add-ons: {e}")
    
    def determine_capabilities(self):
        """Determine system capabilities based on configuration"""
        capabilities = []
        
        # Check for specific capabilities
        integrations = self.context.get('integrations', {}).get('configured', [])
        integration_domains = [i.get('domain', '') for i in integrations]
        
        if 'media_player' in integration_domains or self.context['integrations']['by_category']['media']:
            capabilities.append('media_control')
        
        if any(x in integration_domains for x in ['light', 'switch']):
            capabilities.append('lighting_control')
        
        if 'climate' in integration_domains:
            capabilities.append('climate_control')
        
        if any(x in integration_domains for x in ['camera', 'alarm_control_panel']):
            capabilities.append('security_monitoring')
        
        if 'person' in integration_domains or 'device_tracker' in integration_domains:
            capabilities.append('presence_detection')
        
        if any(x in integration_domains for x in ['tts', 'stt']):
            capabilities.append('voice_interaction')
        
        if 'weather' in integration_domains:
            capabilities.append('weather_monitoring')
        
        if 'sensor' in integration_domains:
            capabilities.append('sensor_monitoring')
        
        # Check add-on capabilities
        addons = self.context.get('addons', {}).get('installed', [])
        addon_names = [a.get('name', '').lower() for a in addons]
        
        if any('mqtt' in name for name in addon_names):
            capabilities.append('mqtt_integration')
        
        if any('node' in name for name in addon_names):
            capabilities.append('advanced_automation')
        
        if any(x in addon_names for x in ['influxdb', 'grafana']):
            capabilities.append('advanced_monitoring')
        
        self.context['capabilities']['available'] = list(set(capabilities))
    
    def generate_recommendations(self):
        """Generate AI recommendations based on setup"""
        recommendations = []
        
        # Check for common missing elements
        integrations = self.context.get('integrations', {}).get('configured', [])
        integration_domains = [i.get('domain', '') for i in integrations]
        
        auto_count = self.context.get('automations', {}).get('total', 0)
        if auto_count == 0:
            recommendations.append({
                'type': 'automation',
                'priority': 'high',
                'suggestion': 'No automations configured. Consider creating basic automations for lighting, climate, or security.'
            })
        
        if 'media_player' in integration_domains and auto_count < 5:
            recommendations.append({
                'type': 'automation',
                'priority': 'medium',
                'suggestion': 'Media players detected. Consider automations for: movie mode, bedtime routine, morning playlist.'
            })
        
        if 'light' in integration_domains:
            recommendations.append({
                'type': 'dashboard',
                'priority': 'medium',
                'suggestion': 'Create a centralized lighting control dashboard with scenes and brightness controls.'
            })
        
        if 'climate' in integration_domains:
            recommendations.append({
                'type': 'automation',
                'priority': 'high',
                'suggestion': 'Climate control available. Consider: temperature schedules, away mode, weather-based adjustments.'
            })
        
        if 'person' in integration_domains or 'device_tracker' in integration_domains:
            recommendations.append({
                'type': 'automation',
                'priority': 'high',
                'suggestion': 'Presence detection available. Consider: arrival/departure automations, home/away modes.'
            })
        
        # Check for monitoring capabilities
        addons = self.context.get('addons', {}).get('installed', [])
        has_influx = any('influx' in a.get('name', '').lower() for a in addons)
        has_grafana = any('grafana' in a.get('name', '').lower() for a in addons)
        
        if 'sensor' in integration_domains and not (has_influx or has_grafana):
            recommendations.append({
                'type': 'addon',
                'priority': 'low',
                'suggestion': 'Many sensors available. Consider InfluxDB + Grafana for advanced data visualization.'
            })
        
        self.context['recommendations'] = recommendations
    
    def generate_ai_prompt(self):
        """Generate AI-friendly prompt"""
        prompt = f"""# Home Assistant Configuration Context

## System Overview
- **Total Integrations**: {len(self.context.get('integrations', {}).get('configured', []))}
- **Custom Components**: {len(self.context.get('integrations', {}).get('custom_components', []))}
- **Total Entities**: {self.context.get('entities', {}).get('total', 0)}
- **Active Entities**: {self.context.get('entities', {}).get('active_count', 0)}
- **Disabled Entities**: {self.context.get('entities', {}).get('disabled_count', 0)}
- **Total Devices**: {self.context.get('devices', {}).get('total', 0)}
- **Automations**: {self.context.get('automations', {}).get('total', 0)}
- **Scripts**: {self.context.get('scripts', {}).get('total', 0)}
- **Add-ons**: {self.context.get('addons', {}).get('total', 0)}

## Entity Breakdown by Domain
"""
        
        entity_domains = self.context.get('entities', {}).get('by_domain', {})
        for domain, count in sorted(entity_domains.items(), key=lambda x: x[1], reverse=True):
            prompt += f"- **{domain}**: {count} entities\n"
        
        prompt += f"\n## Device Manufacturers\n"
        manufacturers = self.context.get('devices', {}).get('by_manufacturer', {})
        for mfr, count in sorted(manufacturers.items(), key=lambda x: x[1], reverse=True)[:15]:
            prompt += f"- **{mfr}**: {count} devices\n"
        
        prompt += f"\n## Integration Categories\n"
        categories = self.context.get('integrations', {}).get('by_category', {})
        for cat, items in categories.items():
            if items:
                prompt += f"### {cat.title()}\n"
                prompt += f"{', '.join(items[:10])}\n"
                if len(items) > 10:
                    prompt += f"... and {len(items) - 10} more\n"
                prompt += "\n"
        
        prompt += f"## Add-on Categories\n"
        addon_cats = self.context.get('addons', {}).get('by_category', {})
        for cat, items in addon_cats.items():
            if items:
                prompt += f"- **{cat.title()}**: {', '.join(items)}\n"
        
        prompt += f"\n## System Capabilities\n"
        capabilities = self.context.get('capabilities', {}).get('available', [])
        for cap in capabilities:
            prompt += f"- {cap.replace('_', ' ').title()}\n"
        
        prompt += f"\n## Existing Automations\n"
        autos = self.context.get('automations', {}).get('list', [])
        for auto in autos[:20]:  # Limit to first 20
            prompt += f"- **{auto.get('alias')}**: {auto.get('triggers')} triggers, {auto.get('actions')} actions\n"
        
        if len(autos) > 20:
            prompt += f"- ... and {len(autos) - 20} more\n"
        
        prompt += f"\n## Recommendations for AI Development\n"
        recommendations = self.context.get('recommendations', [])
        for rec in recommendations:
            prompt += f"### {rec['type'].title()} - Priority: {rec['priority'].upper()}\n"
            prompt += f"{rec['suggestion']}\n\n"
        
        prompt += f"""
## How to Use This Context

You can help with:
1. **Creating Automations**: Based on the available integrations and capabilities
2. **Designing Dashboards**: Leveraging all configured devices and sensors
3. **Writing Scripts**: For complex multi-step operations
4. **Binary Sensors**: Creating template sensors and helpers
5. **Optimization**: Improving existing automations and configurations
6. **Integration**: Connecting different systems together

## Available Entity Domains
{', '.join(sorted(entity_domains.keys()))}

## Top Device Types
Based on {self.context.get('devices', {}).get('total', 0)} devices across {len(manufacturers)} manufacturers.

## Configuration Files Available
- configuration.yaml (with {len(self.context.get('system_overview', {}).get('configured_platforms', []))} platforms)
- automations.yaml ({self.context.get('automations', {}).get('total', 0)} automations)
- scripts.yaml ({self.context.get('scripts', {}).get('total', 0)} scripts)
- Entity registry (all {self.context.get('entities', {}).get('total', 0)} entities)
- Device registry (all {self.context.get('devices', {}).get('total', 0)} devices)

Please ask me to:
- Create specific automations
- Design dashboard layouts
- Write helper scripts
- Add binary sensors or template sensors
- Optimize existing configurations
- Suggest improvements

All configurations will be provided with placeholder values for security.
"""
        
        return prompt
    
    def generate_context_file(self):
        """Generate complete context file for AI"""
        print("\n=== Generating AI Context ===")
        
        print("Analyzing configuration...")
        self.analyze_configuration()
        print("Analyzing integrations...")
        self.analyze_integrations()
        print("Analyzing entities...")
        self.analyze_entities()
        print("Analyzing devices...")
        self.analyze_devices()
        print("Analyzing automations...")
        self.analyze_automations()
        print("Analyzing scripts...")
        self.analyze_scripts()
        print("Analyzing add-ons...")
        self.analyze_addons()
        print("Determining capabilities...")
        self.determine_capabilities()
        print("Generating recommendations...")
        self.generate_recommendations()
        
        # Save detailed JSON context
        context_file = os.path.join(self.export_path, 'AI_CONTEXT.json')
        with open(context_file, 'w') as f:
            json.dump(self.context, f, indent=2)
        
        print(f"✓ Saved detailed context: AI_CONTEXT.json")
        
        # Generate AI prompt
        prompt = self.generate_ai_prompt()
        prompt_file = os.path.join(self.export_path, 'AI_PROMPT.md')
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        
        print(f"✓ Saved AI prompt: AI_PROMPT.md")
        
        # Print summary
        print("\n" + "="*70)
        print("Context Summary")
        print("="*70)
        print(f"Integrations: {len(self.context.get('integrations', {}).get('configured', []))}")
        print(f"Entities: {self.context.get('entities', {}).get('total', 0)} ({self.context.get('entities', {}).get('active_count', 0)} active)")
        print(f"Devices: {self.context.get('devices', {}).get('total', 0)}")
        print(f"Automations: {self.context.get('automations', {}).get('total', 0)}")
        print(f"Scripts: {self.context.get('scripts', {}).get('total', 0)}")
        print(f"Add-ons: {self.context.get('addons', {}).get('total', 0)}")
        print(f"Capabilities: {len(self.context.get('capabilities', {}).get('available', []))}")
        print(f"Recommendations: {len(self.context.get('recommendations', []))}")
        
        return context_file, prompt_file


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ha_ai_context_gen.py <export_directory>")
        sys.exit(1)
    
    export_path = sys.argv[1]
    
    if not os.path.exists(export_path):
        print(f"Error: Export directory not found: {export_path}")
        sys.exit(1)
    
    generator = HAContextGenerator(export_path)
    context_file, prompt_file = generator.generate_context_file()
    
    print("\n" + "="*70)
    print("✓ Context Generation Complete!")
    print("="*70)
    print(f"\nFiles created:")
    print(f"1. {context_file} - Detailed JSON context")
    print(f"2. {prompt_file} - AI-friendly prompt")
    print(f"\nYou can now share these files with AI assistants to get help with:")
    print("- Creating new automations")
    print("- Designing dashboards")
    print("- Writing scripts and helpers")
    print("- Optimizing your setup")


if __name__ == "__main__":
    main()
