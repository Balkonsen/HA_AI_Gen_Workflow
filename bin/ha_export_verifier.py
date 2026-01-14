#!/usr/bin/env python3
"""
Home Assistant Export Verification Tool
Verifies completeness of exported configuration
"""

import os
import sys
import json
import tarfile
from pathlib import Path

class ExportVerifier:
    def __init__(self, export_path):
        self.export_path = export_path
        self.issues = []
        self.warnings = []
        self.stats = {}
    
    def verify_structure(self):
        """Verify directory structure"""
        print("\n=== Verifying Export Structure ===")
        
        required_dirs = ['config', 'diagnostics', 'secrets', 'addons']
        required_files = ['METADATA.json', 'README.md']
        
        all_ok = True
        
        for dir_name in required_dirs:
            dir_path = os.path.join(self.export_path, dir_name)
            if os.path.exists(dir_path):
                print(f"✓ {dir_name}/ directory exists")
            else:
                print(f"✗ {dir_name}/ directory missing")
                self.issues.append(f"Missing directory: {dir_name}/")
                all_ok = False
        
        for file_name in required_files:
            file_path = os.path.join(self.export_path, file_name)
            if os.path.exists(file_path):
                print(f"✓ {file_name} exists")
            else:
                print(f"✗ {file_name} missing")
                self.issues.append(f"Missing file: {file_name}")
                all_ok = False
        
        return all_ok
    
    def verify_entities(self):
        """Verify entity registry export"""
        print("\n=== Verifying Entity Registry ===")
        
        entities_file = os.path.join(self.export_path, 'diagnostics', 'entities_registry.json')
        
        if not os.path.exists(entities_file):
            print("✗ entities_registry.json not found")
            self.issues.append("Entity registry not exported")
            return False
        
        try:
            with open(entities_file, 'r') as f:
                entity_data = json.load(f)
            
            total = entity_data.get('total_entities', 0)
            active = total - len(entity_data.get('disabled_entities', []))
            domains = len(entity_data.get('entities_by_domain', {}))
            platforms = len(entity_data.get('entities_by_platform', {}))
            
            print(f"✓ Entity registry exported successfully")
            print(f"  Total entities: {total}")
            print(f"  Active entities: {active}")
            print(f"  Disabled entities: {len(entity_data.get('disabled_entities', []))}")
            print(f"  Entity domains: {domains}")
            print(f"  Platforms: {platforms}")
            
            # Store stats
            self.stats['entities'] = {
                'total': total,
                'active': active,
                'domains': domains,
                'platforms': platforms
            }
            
            # Check for common entity types
            entities_by_domain = entity_data.get('entities_by_domain', {})
            common_domains = ['light', 'switch', 'sensor', 'binary_sensor', 'automation', 'script']
            
            print(f"\n  Entity breakdown:")
            for domain in common_domains:
                count = len(entities_by_domain.get(domain, []))
                if count > 0:
                    print(f"    - {domain}: {count}")
            
            # Show top 5 domains
            top_domains = sorted(entities_by_domain.items(), key=lambda x: len(x[1]), reverse=True)[:5]
            if top_domains:
                print(f"\n  Top 5 entity types:")
                for domain, entities in top_domains:
                    print(f"    - {domain}: {len(entities)} entities")
            
            return True
            
        except Exception as e:
            print(f"✗ Error reading entity registry: {e}")
            self.issues.append(f"Entity registry parse error: {e}")
            return False
    
    def verify_devices(self):
        """Verify device registry export"""
        print("\n=== Verifying Device Registry ===")
        
        devices_file = os.path.join(self.export_path, 'diagnostics', 'devices_registry.json')
        
        if not os.path.exists(devices_file):
            print("✗ devices_registry.json not found")
            self.issues.append("Device registry not exported")
            return False
        
        try:
            with open(devices_file, 'r') as f:
                device_data = json.load(f)
            
            total = device_data.get('total_devices', 0)
            manufacturers = len(device_data.get('devices_by_manufacturer', {}))
            integrations = len(device_data.get('devices_by_integration', {}))
            
            print(f"✓ Device registry exported successfully")
            print(f"  Total devices: {total}")
            print(f"  Manufacturers: {manufacturers}")
            print(f"  Integrations: {integrations}")
            
            # Store stats
            self.stats['devices'] = {
                'total': total,
                'manufacturers': manufacturers,
                'integrations': integrations
            }
            
            # Show top manufacturers
            by_manufacturer = device_data.get('devices_by_manufacturer', {})
            top_manufacturers = sorted(by_manufacturer.items(), key=lambda x: x[1], reverse=True)[:5]
            
            if top_manufacturers:
                print(f"\n  Top 5 manufacturers:")
                for mfr, count in top_manufacturers:
                    print(f"    - {mfr}: {count} devices")
            
            return True
            
        except Exception as e:
            print(f"✗ Error reading device registry: {e}")
            self.issues.append(f"Device registry parse error: {e}")
            return False
    
    def verify_config_files(self):
        """Verify configuration files"""
        print("\n=== Verifying Configuration Files ===")
        
        config_dir = os.path.join(self.export_path, 'config')
        
        if not os.path.exists(config_dir):
            print("✗ config/ directory not found")
            self.issues.append("Configuration directory missing")
            return False
        
        # Check for key files
        key_files = {
            'configuration.yaml': 'Main configuration',
            'automations.yaml': 'Automations',
            'scripts.yaml': 'Scripts',
            'scenes.yaml': 'Scenes',
        }
        
        found_files = []
        
        for file_name, description in key_files.items():
            file_path = os.path.join(config_dir, file_name)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"✓ {file_name} ({description}) - {size} bytes")
                found_files.append(file_name)
            else:
                print(f"⚠️  {file_name} not found (may not exist in your setup)")
                self.warnings.append(f"{file_name} not found")
        
        # Count all YAML files
        yaml_files = list(Path(config_dir).rglob('*.yaml')) + list(Path(config_dir).rglob('*.yml'))
        json_files = list(Path(config_dir).rglob('*.json'))
        
        print(f"\n  Total YAML files: {len(yaml_files)}")
        print(f"  Total JSON files: {len(json_files)}")
        
        self.stats['config_files'] = {
            'yaml': len(yaml_files),
            'json': len(json_files),
            'key_files_found': len(found_files)
        }
        
        # Check .storage directory
        storage_dir = os.path.join(config_dir, '.storage')
        if os.path.exists(storage_dir):
            storage_files = list(Path(storage_dir).glob('*.json'))
            print(f"  Storage files: {len(storage_files)}")
        
        return len(found_files) > 0
    
    def verify_secrets(self):
        """Verify secrets mapping"""
        print("\n=== Verifying Secrets Mapping ===")
        
        secrets_file = os.path.join(self.export_path, 'secrets', 'secrets_map.json')
        
        if not os.path.exists(secrets_file):
            print("✗ secrets_map.json not found")
            self.issues.append("Secrets mapping file missing")
            return False
        
        try:
            with open(secrets_file, 'r') as f:
                secrets_data = json.load(f)
            
            total_secrets = secrets_data.get('total_secrets', 0)
            secrets = secrets_data.get('secrets', {})
            
            print(f"✓ Secrets mapping exported")
            print(f"  Total secrets replaced: {total_secrets}")
            
            # Count by type
            secret_types = {}
            for placeholder in secrets.keys():
                stype = placeholder.split('_')[0].replace('<<', '')
                secret_types[stype] = secret_types.get(stype, 0) + 1
            
            if secret_types:
                print(f"\n  Secret types:")
                for stype, count in sorted(secret_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"    - {stype}: {count}")
            
            self.stats['secrets'] = {
                'total': total_secrets,
                'types': len(secret_types)
            }
            
            return True
            
        except Exception as e:
            print(f"✗ Error reading secrets: {e}")
            self.issues.append(f"Secrets parse error: {e}")
            return False
    
    def verify_addons(self):
        """Verify add-on configurations"""
        print("\n=== Verifying Add-on Configurations ===")
        
        addons_file = os.path.join(self.export_path, 'addons', 'addons_summary.json')
        
        if not os.path.exists(addons_file):
            print("⚠️  addons_summary.json not found (may not have add-ons)")
            self.warnings.append("Add-on summary not found")
            return True
        
        try:
            with open(addons_file, 'r') as f:
                addon_data = json.load(f)
            
            installed = addon_data.get('installed_addons', [])
            
            print(f"✓ Add-on configurations exported")
            print(f"  Total add-ons: {len(installed)}")
            
            if installed:
                print(f"\n  Installed add-ons:")
                for addon in installed[:10]:
                    name = addon.get('name', 'Unknown')
                    version = addon.get('version', '?')
                    state = addon.get('state', '?')
                    print(f"    - {name} v{version} ({state})")
                
                if len(installed) > 10:
                    print(f"    ... and {len(installed) - 10} more")
            
            self.stats['addons'] = {
                'total': len(installed)
            }
            
            return True
            
        except Exception as e:
            print(f"✗ Error reading add-ons: {e}")
            self.issues.append(f"Add-on parse error: {e}")
            return False
    
    def verify_integrations(self):
        """Verify integrations export"""
        print("\n=== Verifying Integrations ===")
        
        integrations_file = os.path.join(self.export_path, 'diagnostics', 'integrations.json')
        
        if not os.path.exists(integrations_file):
            print("✗ integrations.json not found")
            self.issues.append("Integrations file missing")
            return False
        
        try:
            with open(integrations_file, 'r') as f:
                integ_data = json.load(f)
            
            configured = integ_data.get('configured_integrations', [])
            custom = integ_data.get('custom_components', [])
            
            print(f"✓ Integrations exported")
            print(f"  Configured integrations: {len(configured)}")
            print(f"  Custom components: {len(custom)}")
            
            if configured:
                print(f"\n  Sample integrations:")
                for integ in configured[:10]:
                    domain = integ.get('domain', 'unknown')
                    title = integ.get('title', domain)
                    print(f"    - {title} ({domain})")
            
            self.stats['integrations'] = {
                'configured': len(configured),
                'custom': len(custom)
            }
            
            return True
            
        except Exception as e:
            print(f"✗ Error reading integrations: {e}")
            self.issues.append(f"Integrations parse error: {e}")
            return False
    
    def generate_report(self):
        """Generate verification report"""
        print("\n" + "="*70)
        print("Verification Summary")
        print("="*70)
        
        print(f"\n📊 Export Statistics:")
        if 'entities' in self.stats:
            print(f"  Entities: {self.stats['entities']['total']} ({self.stats['entities']['active']} active)")
        if 'devices' in self.stats:
            print(f"  Devices: {self.stats['devices']['total']}")
        if 'integrations' in self.stats:
            print(f"  Integrations: {self.stats['integrations']['configured']}")
            print(f"  Custom Components: {self.stats['integrations']['custom']}")
        if 'addons' in self.stats:
            print(f"  Add-ons: {self.stats['addons']['total']}")
        if 'config_files' in self.stats:
            print(f"  Config Files: {self.stats['config_files']['yaml']} YAML, {self.stats['config_files']['json']} JSON")
        if 'secrets' in self.stats:
            print(f"  Secrets Replaced: {self.stats['secrets']['total']}")
        
        if self.issues:
            print(f"\n❌ Critical Issues Found: {len(self.issues)}")
            for issue in self.issues:
                print(f"  - {issue}")
        else:
            print(f"\n✅ No critical issues found")
        
        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # Overall status
        print("\n" + "="*70)
        if not self.issues:
            print("✅ Export verification PASSED")
            print("\nYour export is complete and ready to use with AI assistants!")
        else:
            print("❌ Export verification FAILED")
            print("\nPlease re-run the export script to fix issues.")
        print("="*70)
        
        return len(self.issues) == 0
    
    def run(self):
        """Run all verification checks"""
        print("="*70)
        print("Home Assistant Export Verification Tool")
        print("="*70)
        print(f"\nVerifying: {self.export_path}")
        
        checks = [
            self.verify_structure(),
            self.verify_entities(),
            self.verify_devices(),
            self.verify_config_files(),
            self.verify_integrations(),
            self.verify_secrets(),
            self.verify_addons(),
        ]
        
        return self.generate_report()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify Home Assistant export completeness')
    parser.add_argument('export_path', help='Path to extracted export directory or tarball')
    
    args = parser.parse_args()
    
    export_path = args.export_path
    
    # Check if it's a tarball
    if export_path.endswith('.tar.gz') or export_path.endswith('.tgz'):
        print("Extracting tarball...")
        extract_dir = "/tmp/ha_verify_temp"
        os.makedirs(extract_dir, exist_ok=True)
        
        try:
            with tarfile.open(export_path, 'r:gz') as tar:
                tar.extractall(extract_dir)
            
            # Find extracted directory
            extracted_dirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
            if extracted_dirs:
                export_path = os.path.join(extract_dir, extracted_dirs[0])
            else:
                print("Error: No directory found in tarball")
                sys.exit(1)
        except Exception as e:
            print(f"Error extracting tarball: {e}")
            sys.exit(1)
    
    if not os.path.exists(export_path):
        print(f"Error: Export path not found: {export_path}")
        sys.exit(1)
    
    verifier = ExportVerifier(export_path)
    success = verifier.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
