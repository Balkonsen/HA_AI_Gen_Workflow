#!/usr/bin/env python3
"""
Home Assistant Configuration Export Tool
Exports complete HA configuration with sensitive data sanitization
Creates a comprehensive diagnostic report for AI-assisted development
"""

import os
import sys
import json
import yaml
import tarfile
import hashlib
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import shutil

class HAConfigExporter:
    def __init__(self, output_dir="/tmp/ha_export"):
        self.output_dir = output_dir
        self.secrets_map = {}
        self.secret_counter = 0
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.export_name = f"ha_config_export_{self.timestamp}"
        self.export_path = os.path.join(output_dir, self.export_name)
        
        # Patterns to identify sensitive data
        self.sensitive_patterns = {
            'password': r'password["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)',
            'token': r'token["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)',
            'api_key': r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)',
            'secret': r'secret["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)',
            'webhook': r'webhook["\']?\s*[:=]\s*["\']?(https?://[^"\'}\s,]+)',
            'latitude': r'latitude["\']?\s*[:=]\s*["\']?(-?\d+\.\d+)',
            'longitude': r'longitude["\']?\s*[:=]\s*["\']?(-?\d+\.\d+)',
            'email': r'[\w\.-]+@[\w\.-]+\.\w+',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'mac_address': r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b',
            'ssid': r'ssid["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)',
            'username': r'username["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)',
        }
        
        # HA paths to export
        self.config_paths = {
            'config': '/config',
            'addons': '/data/addons',
            'supervisor': '/data/supervisor',
        }

    def create_export_structure(self):
        """Create export directory structure"""
        print(f"Creating export structure: {self.export_path}")
        os.makedirs(self.export_path, exist_ok=True)
        os.makedirs(f"{self.export_path}/config", exist_ok=True)
        os.makedirs(f"{self.export_path}/diagnostics", exist_ok=True)
        os.makedirs(f"{self.export_path}/addons", exist_ok=True)
        os.makedirs(f"{self.export_path}/secrets", exist_ok=True)

    def run_command(self, cmd, shell=True):
        """Run shell command and return output"""
        try:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=30)
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), 1

    def generate_secret_placeholder(self, secret_type, value):
        """Generate unique placeholder for sensitive data"""
        if value in self.secrets_map:
            return self.secrets_map[value]
        
        self.secret_counter += 1
        placeholder = f"<<{secret_type.upper()}_{self.secret_counter}>>"
        self.secrets_map[value] = placeholder
        return placeholder

    def sanitize_text(self, text, filename=""):
        """Replace sensitive data with placeholders"""
        if not isinstance(text, str):
            return text
        
        sanitized = text
        
        # Apply all sensitive patterns
        for secret_type, pattern in self.sensitive_patterns.items():
            matches = re.finditer(pattern, sanitized, re.IGNORECASE)
            for match in matches:
                if match.groups():
                    original_value = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    # Skip obvious placeholders and examples
                    if any(x in original_value.lower() for x in ['example', 'placeholder', 'xxx', '***']):
                        continue
                    if len(original_value) < 3:  # Skip very short matches
                        continue
                    placeholder = self.generate_secret_placeholder(secret_type, original_value)
                    sanitized = sanitized.replace(original_value, placeholder)
        
        return sanitized

    def export_yaml_file(self, source_path, dest_path):
        """Export and sanitize YAML file"""
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sanitized = self.sanitize_text(content, os.path.basename(source_path))
            
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write(sanitized)
            
            return True
        except Exception as e:
            print(f"  Error exporting {source_path}: {e}")
            return False

    def export_json_file(self, source_path, dest_path):
        """Export and sanitize JSON file"""
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sanitized = self.sanitize_text(content, os.path.basename(source_path))
            
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write(sanitized)
            
            return True
        except Exception as e:
            print(f"  Error exporting {source_path}: {e}")
            return False

    def export_entities_registry(self):
        """Export entities from core.entity_registry"""
        print("\n=== Exporting Entity Registry ===")
        entity_registry_path = "/config/.storage/core.entity_registry"
        
        entities_data = {
            'total_entities': 0,
            'entities_by_domain': {},
            'entities_by_platform': {},
            'disabled_entities': [],
            'all_entities': []
        }
        
        if os.path.exists(entity_registry_path):
            try:
                with open(entity_registry_path, 'r') as f:
                    registry = json.load(f)
                
                entities = registry.get('data', {}).get('entities', [])
                entities_data['total_entities'] = len(entities)
                
                for entity in entities:
                    entity_id = entity.get('entity_id', '')
                    domain = entity_id.split('.')[0] if '.' in entity_id else 'unknown'
                    platform = entity.get('platform', 'unknown')
                    
                    # Sanitize entity details
                    sanitized_entity = {
                        'entity_id': entity_id,
                        'domain': domain,
                        'platform': platform,
                        'name': entity.get('name'),
                        'original_name': entity.get('original_name'),
                        'disabled': entity.get('disabled_by') is not None,
                        'hidden': entity.get('hidden_by') is not None,
                        'device_id': entity.get('device_id'),
                        'config_entry_id': entity.get('config_entry_id'),
                        'has_entity_name': entity.get('has_entity_name'),
                        'original_device_class': entity.get('original_device_class'),
                    }
                    
                    entities_data['all_entities'].append(sanitized_entity)
                    
                    # Count by domain
                    if domain not in entities_data['entities_by_domain']:
                        entities_data['entities_by_domain'][domain] = []
                    entities_data['entities_by_domain'][domain].append(entity_id)
                    
                    # Count by platform
                    if platform not in entities_data['entities_by_platform']:
                        entities_data['entities_by_platform'][platform] = []
                    entities_data['entities_by_platform'][platform].append(entity_id)
                    
                    # Track disabled
                    if entity.get('disabled_by'):
                        entities_data['disabled_entities'].append(entity_id)
                
                # Save entity registry export
                dest_path = f"{self.export_path}/diagnostics/entities_registry.json"
                with open(dest_path, 'w') as f:
                    json.dump(entities_data, f, indent=2)
                
                print(f"✓ Exported {entities_data['total_entities']} entities")
                print(f"  - Active: {entities_data['total_entities'] - len(entities_data['disabled_entities'])}")
                print(f"  - Disabled: {len(entities_data['disabled_entities'])}")
                print(f"  - Domains: {len(entities_data['entities_by_domain'])}")
                
                return True
            except Exception as e:
                print(f"  Error exporting entity registry: {e}")
                return False
        else:
            print("  Entity registry not found")
            return False

    def export_device_registry(self):
        """Export devices from core.device_registry"""
        print("\n=== Exporting Device Registry ===")
        device_registry_path = "/config/.storage/core.device_registry"
        
        devices_data = {
            'total_devices': 0,
            'devices_by_manufacturer': {},
            'devices_by_integration': {},
            'all_devices': []
        }
        
        if os.path.exists(device_registry_path):
            try:
                with open(device_registry_path, 'r') as f:
                    registry = json.load(f)
                
                devices = registry.get('data', {}).get('devices', [])
                devices_data['total_devices'] = len(devices)
                
                for device in devices:
                    manufacturer = device.get('manufacturer', 'Unknown')
                    
                    # Get primary integration
                    identifiers = device.get('identifiers', [])
                    integration = identifiers[0][0] if identifiers and len(identifiers[0]) > 0 else 'unknown'
                    
                    sanitized_device = {
                        'id': device.get('id'),
                        'name': self.sanitize_text(device.get('name', '')),
                        'manufacturer': manufacturer,
                        'model': device.get('model'),
                        'sw_version': device.get('sw_version'),
                        'integration': integration,
                        'disabled': device.get('disabled_by') is not None,
                    }
                    
                    devices_data['all_devices'].append(sanitized_device)
                    
                    # Count by manufacturer
                    if manufacturer not in devices_data['devices_by_manufacturer']:
                        devices_data['devices_by_manufacturer'][manufacturer] = 0
                    devices_data['devices_by_manufacturer'][manufacturer] += 1
                    
                    # Count by integration
                    if integration not in devices_data['devices_by_integration']:
                        devices_data['devices_by_integration'][integration] = 0
                    devices_data['devices_by_integration'][integration] += 1
                
                # Save device registry export
                dest_path = f"{self.export_path}/diagnostics/devices_registry.json"
                with open(dest_path, 'w') as f:
                    json.dump(devices_data, f, indent=2)
                
                print(f"✓ Exported {devices_data['total_devices']} devices")
                print(f"  - Manufacturers: {len(devices_data['devices_by_manufacturer'])}")
                print(f"  - Integrations: {len(devices_data['devices_by_integration'])}")
                
                return True
            except Exception as e:
                print(f"  Error exporting device registry: {e}")
                return False
        else:
            print("  Device registry not found")
            return False

    def export_config_directory(self):
        """Export main configuration directory"""
        print("\n=== Exporting Configuration Files ===")
        config_dir = "/config"
        dest_dir = f"{self.export_path}/config"
        
        # Files and patterns to export
        export_patterns = [
            "*.yaml",
            "*.yml",
            "*.json",
            "automations.yaml",
            "scripts.yaml",
            "scenes.yaml",
            "configuration.yaml",
            "ui-lovelace.yaml",
            ".storage/*.json",
            "custom_components/**/*.py",
            "custom_components/**/*.yaml",
            "www/**/*",
            "packages/*.yaml",
            "packages/**/*.yaml",
            "themes/*.yaml",
            "blueprints/**/*.yaml",
        ]
        
        # Files to exclude
        exclude_patterns = [
            "*.db",
            "*.db-wal",
            "*.db-shm",
            "*.log",
            "home-assistant.log*",
            "home-assistant_v2.db*",
            "*.sqlite",
            ".cloud",
            ".storage/lovelace*",
            "deps",
            "tts",
            "__pycache__",
            ".DS_Store",
        ]
        
        exported_count = 0
        
        for root, dirs, files in os.walk(config_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(excl in d for excl in ['deps', '__pycache__', '.cloud', 'tts'])]
            
            for file in files:
                source_path = os.path.join(root, file)
                rel_path = os.path.relpath(source_path, config_dir)
                dest_path = os.path.join(dest_dir, rel_path)
                
                # Check if file should be excluded
                if any(re.match(excl.replace('*', '.*'), file) for excl in exclude_patterns):
                    continue
                
                # Export based on file type
                if file.endswith(('.yaml', '.yml')):
                    if self.export_yaml_file(source_path, dest_path):
                        exported_count += 1
                elif file.endswith('.json'):
                    if self.export_json_file(source_path, dest_path):
                        exported_count += 1
                elif file.endswith('.py'):
                    if self.export_yaml_file(source_path, dest_path):  # Python can use same sanitization
                        exported_count += 1
        
        print(f"✓ Exported {exported_count} configuration files")

    def export_addon_configs(self):
        """Export add-on configurations"""
        print("\n=== Exporting Add-on Configurations ===")
        
        addon_data = {
            'installed_addons': [],
            'addon_configs': {}
        }
        
        # Get list of installed add-ons via API
        stdout, _, _ = self.run_command("ha addons --raw-json 2>/dev/null || echo '{}'")
        try:
            addons_info = json.loads(stdout) if stdout.strip() else {}
            if 'data' in addons_info and 'addons' in addons_info['data']:
                for addon in addons_info['data']['addons']:
                    addon_data['installed_addons'].append({
                        'slug': addon.get('slug', ''),
                        'name': addon.get('name', ''),
                        'version': addon.get('version', ''),
                        'state': addon.get('state', ''),
                        'repository': addon.get('repository', ''),
                    })
        except:
            pass
        
        # Export addon configs from /data/addon_configs
        addon_config_dir = "/data/addon_configs"
        if os.path.exists(addon_config_dir):
            for addon_name in os.listdir(addon_config_dir):
                addon_path = os.path.join(addon_config_dir, addon_name)
                if os.path.isdir(addon_path):
                    config_file = os.path.join(addon_path, "options.json")
                    if os.path.exists(config_file):
                        dest_path = f"{self.export_path}/addons/{addon_name}_options.json"
                        self.export_json_file(config_file, dest_path)
        
        # Save addon summary
        with open(f"{self.export_path}/addons/addons_summary.json", 'w') as f:
            json.dump(addon_data, f, indent=2)
        
        print(f"✓ Exported {len(addon_data['installed_addons'])} add-on configurations")

    def collect_system_info(self):
        """Collect system diagnostic information"""
        print("\n=== Collecting System Information ===")
        
        diagnostics = {
            'export_timestamp': self.timestamp,
            'system_info': {},
            'docker_info': {},
            'network_info': {},
            'hardware_info': {},
        }
        
        # System info
        commands = {
            'ha_version': 'ha core info --raw-json',
            'supervisor_version': 'ha supervisor info --raw-json',
            'host_info': 'ha host info --raw-json',
            'docker_version': 'docker --version',
            'disk_usage': 'df -h',
            'memory_info': 'free -h',
            'uptime': 'uptime',
        }
        
        for name, cmd in commands.items():
            stdout, stderr, code = self.run_command(cmd)
            try:
                # Try to parse as JSON first
                diagnostics['system_info'][name] = json.loads(stdout)
            except:
                # Store as text if not JSON
                diagnostics['system_info'][name] = stdout if code == 0 else stderr
        
        # Docker containers
        stdout, _, _ = self.run_command("docker ps -a --format '{{json .}}'")
        containers = []
        for line in stdout.strip().split('\n'):
            if line:
                try:
                    containers.append(json.loads(line))
                except:
                    pass
        diagnostics['docker_info']['containers'] = containers
        
        # Network info (sanitized)
        stdout, _, _ = self.run_command("ip addr show")
        diagnostics['network_info']['interfaces'] = self.sanitize_text(stdout)
        
        # Save diagnostics
        sanitized_diag = self.sanitize_text(json.dumps(diagnostics, indent=2))
        with open(f"{self.export_path}/diagnostics/system_info.json", 'w') as f:
            f.write(sanitized_diag)
        
        print("✓ Collected system diagnostics")

    def export_integrations_info(self):
        """Export information about configured integrations"""
        print("\n=== Exporting Integrations Information ===")
        
        integrations_info = {
            'configured_integrations': [],
            'custom_components': [],
            'devices': [],
            'entities': []
        }
        
        # Check .storage for integration configs
        storage_path = "/config/.storage"
        if os.path.exists(storage_path):
            core_config_entries = os.path.join(storage_path, "core.config_entries")
            if os.path.exists(core_config_entries):
                try:
                    with open(core_config_entries, 'r') as f:
                        config_entries = json.load(f)
                    
                    for entry in config_entries.get('data', {}).get('entries', []):
                        integrations_info['configured_integrations'].append({
                            'domain': entry.get('domain', ''),
                            'title': entry.get('title', ''),
                            'source': entry.get('source', ''),
                            'version': entry.get('version', 1),
                        })
                except Exception as e:
                    print(f"  Warning: Could not read config entries: {e}")
        
        # Check custom components
        custom_comp_path = "/config/custom_components"
        if os.path.exists(custom_comp_path):
            for comp in os.listdir(custom_comp_path):
                comp_path = os.path.join(custom_comp_path, comp)
                if os.path.isdir(comp_path):
                    manifest = os.path.join(comp_path, "manifest.json")
                    if os.path.exists(manifest):
                        try:
                            with open(manifest, 'r') as f:
                                manifest_data = json.load(f)
                            integrations_info['custom_components'].append({
                                'domain': manifest_data.get('domain', comp),
                                'name': manifest_data.get('name', comp),
                                'version': manifest_data.get('version', 'unknown'),
                                'documentation': manifest_data.get('documentation', ''),
                            })
                        except:
                            integrations_info['custom_components'].append({'domain': comp})
        
        # Save integrations info
        with open(f"{self.export_path}/diagnostics/integrations.json", 'w') as f:
            json.dump(integrations_info, f, indent=2)
        
        print(f"✓ Found {len(integrations_info['configured_integrations'])} integrations")
        print(f"✓ Found {len(integrations_info['custom_components'])} custom components")

    def save_secrets_map(self):
        """Save the secrets mapping file"""
        print("\n=== Saving Secrets Mapping ===")
        
        # Create reverse map for easier lookup
        reverse_map = {v: k for k, v in self.secrets_map.items()}
        
        secrets_data = {
            'export_timestamp': self.timestamp,
            'total_secrets': len(self.secrets_map),
            'secrets': reverse_map,
            'instructions': {
                'usage': 'Use the import script to restore these secrets',
                'format': 'Each placeholder maps to the original sensitive value',
                'security': 'Store this file securely and do not commit to version control'
            }
        }
        
        secrets_file = f"{self.export_path}/secrets/secrets_map.json"
        with open(secrets_file, 'w') as f:
            json.dump(secrets_data, f, indent=2)
        
        print(f"✓ Saved {len(self.secrets_map)} secret mappings to secrets/secrets_map.json")
        print(f"⚠️  IMPORTANT: Keep secrets_map.json secure!")

    def create_metadata(self):
        """Create export metadata file"""
        metadata = {
            'export_version': '1.0',
            'export_timestamp': self.timestamp,
            'export_date': datetime.now().isoformat(),
            'total_secrets_replaced': len(self.secrets_map),
            'structure': {
                'config/': 'Sanitized Home Assistant configuration files',
                'addons/': 'Add-on configurations',
                'diagnostics/': 'System diagnostic information',
                'secrets/': 'Secrets mapping (KEEP SECURE)',
            },
            'instructions': {
                'ai_usage': 'This export can be provided to AI assistants for configuration analysis',
                'restoration': 'Use ha_config_import.py to restore configuration with secrets',
                'security': 'The secrets_map.json file contains sensitive data - do not share it'
            }
        }
        
        with open(f"{self.export_path}/METADATA.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create README
        readme = f"""# Home Assistant Configuration Export
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Export Version: 1.0

## Contents

- **config/**: Your Home Assistant configuration files (sanitized)
- **addons/**: Add-on configurations
- **diagnostics/**: System information and diagnostics
- **secrets/**: Secrets mapping file (KEEP SECURE!)

## Security Notice

The `secrets/secrets_map.json` file contains mappings of all sensitive data that was replaced with placeholders. This file should be:
- Stored securely
- Never committed to version control
- Never shared with untrusted parties

## Using with AI Assistants

You can safely share all files EXCEPT `secrets/` with AI assistants for:
- Configuration analysis
- Creating new automations
- Designing dashboards
- Troubleshooting issues
- Generating new integrations

## Restoration

To restore this configuration to a Home Assistant instance:
1. Use the `ha_config_import.py` script
2. Provide the secrets_map.json file when prompted
3. Review all changes before applying

## Files Sanitized

Total secrets replaced: {len(self.secrets_map)}

Sensitive data types replaced:
- Passwords and tokens
- API keys
- Email addresses
- IP addresses and MAC addresses
- Geographic coordinates
- Webhooks and URLs
- Usernames and SSIDs
"""
        
        with open(f"{self.export_path}/README.md", 'w') as f:
            f.write(readme)

    def create_tarball(self):
        """Create compressed tarball of export"""
        print("\n=== Creating Tarball ===")
        
        tarball_path = f"{self.output_dir}/{self.export_name}.tar.gz"
        
        with tarfile.open(tarball_path, "w:gz") as tar:
            tar.add(self.export_path, arcname=self.export_name)
        
        # Calculate size and hash
        size_mb = os.path.getsize(tarball_path) / (1024 * 1024)
        
        with open(tarball_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        print(f"✓ Created tarball: {tarball_path}")
        print(f"  Size: {size_mb:.2f} MB")
        print(f"  SHA256: {file_hash}")
        
        return tarball_path

    def cleanup_temp_files(self):
        """Remove temporary export directory"""
        try:
            shutil.rmtree(self.export_path)
        except:
            pass

    def run(self):
        """Execute full export process"""
        print("="*70)
        print("Home Assistant Configuration Export Tool")
        print("="*70)
        
        try:
            self.create_export_structure()
            self.export_config_directory()
            self.export_addon_configs()
            self.export_entities_registry()  # NEW: Export entities
            self.export_device_registry()    # NEW: Export devices
            self.collect_system_info()
            self.export_integrations_info()
            self.save_secrets_map()
            self.create_metadata()
            tarball = self.create_tarball()
            self.cleanup_temp_files()
            
            print("\n" + "="*70)
            print("✓ Export Complete!")
            print("="*70)
            print(f"\nExport file: {tarball}")
            print(f"\nNext steps:")
            print(f"1. Download the tarball to your local machine")
            print(f"2. Extract it: tar -xzf {os.path.basename(tarball)}")
            print(f"3. Review contents (especially README.md)")
            print(f"4. Use with AI assistants (exclude secrets/ directory)")
            print(f"5. Use import script to restore configuration")
            print(f"\n⚠️  Security Reminder:")
            print(f"Keep secrets/secrets_map.json secure and private!")
            
            return tarball
            
        except Exception as e:
            print(f"\n✗ Export failed: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Export Home Assistant configuration with sanitization'
    )
    parser.add_argument('--output-dir', default='/tmp/ha_export',
                       help='Output directory for export')
    parser.add_argument('--name', help='Custom export name')
    parser.add_argument('--quiet', action='store_true',
                       help='Minimize output')
    
    args = parser.parse_args()
    
    if os.geteuid() != 0 and not args.quiet:
        print("⚠️  Warning: Running without root privileges")
        print("   Some system information may not be accessible")
        print()
    
    # Check if /config exists
    if not os.path.exists('/config'):
        print("✗ Error: /config directory not found")
        print("  This script must be run on a Home Assistant host")
        sys.exit(1)
    
    # Create custom exporter with args
    output_dir = args.output_dir
    if args.name:
        # Use custom name for export
        exporter = HAConfigExporter(output_dir=output_dir)
        exporter.export_name = args.name
        exporter.export_path = os.path.join(output_dir, args.name)
    else:
        exporter = HAConfigExporter(output_dir=output_dir)
    
    result = exporter.run()
    
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
