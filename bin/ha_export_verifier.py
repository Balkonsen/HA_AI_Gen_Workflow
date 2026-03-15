#!/usr/bin/env python3
"""
Home Assistant Export Verification Tool
Verifies completeness of exported configuration

Supports both export formats:
- v1.0 (legacy): config/, diagnostics/, secrets/, addons/ structure
- v2.0 (current): ai_upload/, secrets/ structure with consolidated files
"""

import os
import sys
import json
import tarfile
import tempfile
from pathlib import Path


def _safe_extract_tar(tar: tarfile.TarFile, destination: str) -> None:
    """Safely extract tar members and block path traversal/link attacks."""
    destination_abs = os.path.abspath(destination)
    safe_members = []
    for member in tar.getmembers():
        if member.issym() or member.islnk():
            raise ValueError(f"Refusing to extract link member: {member.name}")
        member_path = os.path.abspath(os.path.join(destination_abs, member.name))
        if os.path.commonpath([destination_abs, member_path]) != destination_abs:
            raise ValueError(f"Refusing to extract unsafe member path: {member.name}")
        safe_members.append(member)

    for member in safe_members:
        tar.extract(member, destination_abs)


class ExportVerifier:
    def __init__(self, export_path):
        self.export_path = export_path
        self.issues = []
        self.warnings = []
        self.stats = {}
        self.export_version = self._detect_export_version()

    def _detect_export_version(self):
        """Detect export format version from METADATA.json"""
        metadata_file = os.path.join(self.export_path, "METADATA.json")
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                version = metadata.get("export_version", "1.0")
                return version
            except (OSError, TypeError, ValueError, json.JSONDecodeError):
                pass

        # Check for new format indicators
        if os.path.exists(os.path.join(self.export_path, "ai_upload")):
            return "2.0"

        # Default to old format
        return "1.0"

    def verify_structure(self):
        """Verify directory structure (supports both v1.0 and v2.0 formats)"""
        print("\n=== Verifying Export Structure ===")

        if self.export_version == "2.0":
            # New format: ai_upload/ and secrets/
            required_dirs = ["ai_upload", "secrets"]
            required_files = ["METADATA.json", "README.md"]
        else:
            # Old format: config/, diagnostics/, secrets/, addons/
            required_dirs = ["config", "diagnostics", "secrets", "addons"]
            required_files = ["METADATA.json", "README.md"]

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
        """Verify entity registry export (supports both v1.0 and v2.0 formats)"""
        print("\n=== Verifying Entity Registry ===")

        if self.export_version == "2.0":
            # New format: entities are in ha_entities.json in ai_upload/
            entities_file = os.path.join(self.export_path, "ai_upload", "ha_entities.json")

            if not os.path.exists(entities_file):
                print("✗ ha_entities.json not found in ai_upload/")
                self.issues.append("Entity file not exported")
                return False

            try:
                with open(entities_file, "r") as f:
                    entity_data = json.load(f)

                total = entity_data.get("total_entities", 0)
                all_ids = entity_data.get("all_entity_ids", [])
                domains = entity_data.get("entities_by_domain", {})

                print("✓ Entity data exported successfully")
                print(f"  Total entities: {total}")
                print(f"  Entity IDs: {len(all_ids)}")
                print(f"  Entity domains: {len(domains)}")

                # Store stats
                self.stats["entities"] = {
                    "total": total,
                    "domains": len(domains),
                    "ids_count": len(all_ids),
                }

                # Show domain breakdown
                if domains:
                    print("\n  Entity breakdown:")
                    # Sort by count (domains might be dict of counts or dict of lists)
                    sorted_domains = []
                    for domain, value in domains.items():
                        count = (
                            value
                            if isinstance(value, int)
                            else (len(value) if isinstance(value, list) else value.get("count", 0))
                        )
                        sorted_domains.append((domain, count))
                    sorted_domains.sort(key=lambda x: x[1], reverse=True)

                    for domain, count in sorted_domains[:10]:
                        print(f"    - {domain}: {count}")

                return True

            except Exception as e:
                print(f"✗ Error reading entity data: {e}")
                self.issues.append(f"Entity data parse error: {e}")
                return False
        else:
            # Old format: diagnostics/entities_registry.json
            entities_file = os.path.join(self.export_path, "diagnostics", "entities_registry.json")

        if not os.path.exists(entities_file):
            print("✗ entities_registry.json not found")
            self.issues.append("Entity registry not exported")
            return False

        try:
            with open(entities_file, "r") as f:
                entity_data = json.load(f)

            total = entity_data.get("total_entities", 0)
            active = total - len(entity_data.get("disabled_entities", []))
            domains = len(entity_data.get("entities_by_domain", {}))
            platforms = len(entity_data.get("entities_by_platform", {}))

            print("✓ Entity registry exported successfully")
            print(f"  Total entities: {total}")
            print(f"  Active entities: {active}")
            print(f"  Disabled entities: {len(entity_data.get('disabled_entities', []))}")
            print(f"  Entity domains: {domains}")
            print(f"  Platforms: {platforms}")

            # Store stats
            self.stats["entities"] = {
                "total": total,
                "active": active,
                "domains": domains,
                "platforms": platforms,
            }

            # Check for common entity types
            entities_by_domain = entity_data.get("entities_by_domain", {})
            common_domains = [
                "light",
                "switch",
                "sensor",
                "binary_sensor",
                "automation",
                "script",
            ]

            print("\n  Entity breakdown:")
            for domain in common_domains:
                count = len(entities_by_domain.get(domain, []))
                if count > 0:
                    print(f"    - {domain}: {count}")

            # Show top 5 domains
            top_domains = sorted(entities_by_domain.items(), key=lambda x: len(x[1]), reverse=True)[:5]
            if top_domains:
                print("\n  Top 5 entity types:")
                for domain, entities in top_domains:
                    print(f"    - {domain}: {len(entities)} entities")

            return True

        except Exception as e:
            print(f"✗ Error reading entity registry: {e}")
            self.issues.append(f"Entity registry parse error: {e}")
            return False

    def verify_devices(self):
        """Verify device registry export (v1.0 only, embedded in v2.0)"""
        print("\n=== Verifying Device Registry ===")

        if self.export_version == "2.0":
            # In v2.0, device info is embedded in ha_context.md, not separate file
            print("ℹ Device info embedded in ha_context.md (v2.0 format)")
            return True

        devices_file = os.path.join(self.export_path, "diagnostics", "devices_registry.json")

        if not os.path.exists(devices_file):
            print("✗ devices_registry.json not found")
            self.issues.append("Device registry not exported")
            return False

        try:
            with open(devices_file, "r") as f:
                device_data = json.load(f)

            total = device_data.get("total_devices", 0)
            manufacturers = len(device_data.get("devices_by_manufacturer", {}))
            integrations = len(device_data.get("devices_by_integration", {}))

            print("✓ Device registry exported successfully")
            print(f"  Total devices: {total}")
            print(f"  Manufacturers: {manufacturers}")
            print(f"  Integrations: {integrations}")

            # Store stats
            self.stats["devices"] = {
                "total": total,
                "manufacturers": manufacturers,
                "integrations": integrations,
            }

            # Show top manufacturers
            by_manufacturer = device_data.get("devices_by_manufacturer", {})
            top_manufacturers = sorted(by_manufacturer.items(), key=lambda x: x[1], reverse=True)[:5]

            if top_manufacturers:
                print("\n  Top 5 manufacturers:")
                for mfr, count in top_manufacturers:
                    print(f"    - {mfr}: {count} devices")

            return True

        except Exception as e:
            print(f"✗ Error reading device registry: {e}")
            self.issues.append(f"Device registry parse error: {e}")
            return False

    def verify_config_files(self):
        """Verify configuration files (supports both v1.0 and v2.0 formats)"""
        print("\n=== Verifying Configuration Files ===")

        if self.export_version == "2.0":
            # New format: config is in ha_config.yaml in ai_upload/
            config_file = os.path.join(self.export_path, "ai_upload", "ha_config.yaml")

            if not os.path.exists(config_file):
                print("✗ ha_config.yaml not found in ai_upload/")
                self.issues.append("Configuration file missing")
                return False

            try:
                size = os.path.getsize(config_file)
                print(f"✓ ha_config.yaml exists ({size} bytes)")

                # Check for context file too
                context_file = os.path.join(self.export_path, "ai_upload", "ha_context.md")
                if os.path.exists(context_file):
                    context_size = os.path.getsize(context_file)
                    print(f"✓ ha_context.md exists ({context_size} bytes)")

                self.stats["config_files"] = {
                    "yaml": 1,
                    "has_context": os.path.exists(context_file),
                }
                return True
            except Exception as e:
                print(f"✗ Error checking config files: {e}")
                self.issues.append(f"Config file error: {e}")
                return False

        # Old format: config/ directory
        config_dir = os.path.join(self.export_path, "config")

        if not os.path.exists(config_dir):
            print("✗ config/ directory not found")
            self.issues.append("Configuration directory missing")
            return False

        # Check for key files
        key_files = {
            "configuration.yaml": "Main configuration",
            "automations.yaml": "Automations",
            "scripts.yaml": "Scripts",
            "scenes.yaml": "Scenes",
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
        yaml_files = list(Path(config_dir).rglob("*.yaml")) + list(Path(config_dir).rglob("*.yml"))
        json_files = list(Path(config_dir).rglob("*.json"))

        print(f"\n  Total YAML files: {len(yaml_files)}")
        print(f"  Total JSON files: {len(json_files)}")

        self.stats["config_files"] = {
            "yaml": len(yaml_files),
            "json": len(json_files),
            "key_files_found": len(found_files),
        }

        # Check .storage directory
        storage_dir = os.path.join(config_dir, ".storage")
        if os.path.exists(storage_dir):
            storage_files = list(Path(storage_dir).glob("*.json"))
            print(f"  Storage files: {len(storage_files)}")

        return len(found_files) > 0

    def verify_secrets(self):
        """Verify secrets mapping"""
        print("\n=== Verifying Secrets Mapping ===")

        secrets_file = os.path.join(self.export_path, "secrets", "secrets_map.json")

        if not os.path.exists(secrets_file):
            print("✗ secrets_map.json not found")
            self.issues.append("Secrets mapping file missing")
            return False

        try:
            with open(secrets_file, "r") as f:
                secrets_data = json.load(f)

            total_secrets = secrets_data.get("total_secrets", 0)
            secrets = secrets_data.get("secrets", {})

            print("✓ Secrets mapping exported")
            print(f"  Total secrets replaced: {total_secrets}")

            # Count by type
            secret_types = {}
            for placeholder in secrets.keys():
                stype = placeholder.split("_")[0].replace("<<", "")
                secret_types[stype] = secret_types.get(stype, 0) + 1

            if secret_types:
                print("\n  Secret types:")
                for stype, count in sorted(secret_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"    - {stype}: {count}")

            self.stats["secrets"] = {"total": total_secrets, "types": len(secret_types)}

            return True

        except Exception as e:
            print(f"✗ Error reading secrets: {e}")
            self.issues.append(f"Secrets parse error: {e}")
            return False

    def verify_addons(self):
        """Verify add-on configurations (v1.0 only, embedded in v2.0)"""
        print("\n=== Verifying Add-on Configurations ===")

        if self.export_version == "2.0":
            # In v2.0, addon info is embedded in ha_context.md
            print("ℹ Add-on info embedded in ha_context.md (v2.0 format)")
            return True

        addons_file = os.path.join(self.export_path, "addons", "addons_summary.json")

        if not os.path.exists(addons_file):
            print("⚠️  addons_summary.json not found (may not have add-ons)")
            self.warnings.append("Add-on summary not found")
            return True

        try:
            with open(addons_file, "r") as f:
                addon_data = json.load(f)

            installed = addon_data.get("installed_addons", [])

            print("✓ Add-on configurations exported")
            print(f"  Total add-ons: {len(installed)}")

            if installed:
                print("\n  Installed add-ons:")
                for addon in installed[:10]:
                    name = addon.get("name", "Unknown")
                    version = addon.get("version", "?")
                    state = addon.get("state", "?")
                    print(f"    - {name} v{version} ({state})")

                if len(installed) > 10:
                    print(f"    ... and {len(installed) - 10} more")

            self.stats["addons"] = {"total": len(installed)}

            return True

        except Exception as e:
            print(f"✗ Error reading add-ons: {e}")
            self.issues.append(f"Add-on parse error: {e}")
            return False

    def verify_integrations(self):
        """Verify integrations export (v1.0 only, embedded in v2.0)"""
        print("\n=== Verifying Integrations ===")

        if self.export_version == "2.0":
            # In v2.0, integration info is embedded in ha_context.md
            print("ℹ Integration info embedded in ha_context.md (v2.0 format)")
            return True

        integrations_file = os.path.join(self.export_path, "diagnostics", "integrations.json")

        if not os.path.exists(integrations_file):
            print("✗ integrations.json not found")
            self.issues.append("Integrations file missing")
            return False

        try:
            with open(integrations_file, "r") as f:
                integ_data = json.load(f)

            configured = integ_data.get("configured_integrations", [])
            custom = integ_data.get("custom_components", [])

            print("✓ Integrations exported")
            print(f"  Configured integrations: {len(configured)}")
            print(f"  Custom components: {len(custom)}")

            if configured:
                print("\n  Sample integrations:")
                for integ in configured[:10]:
                    domain = integ.get("domain", "unknown")
                    title = integ.get("title", domain)
                    print(f"    - {title} ({domain})")

            self.stats["integrations"] = {
                "configured": len(configured),
                "custom": len(custom),
            }

            return True

        except Exception as e:
            print(f"✗ Error reading integrations: {e}")
            self.issues.append(f"Integrations parse error: {e}")
            return False

    def generate_report(self):
        """Generate verification report"""
        print("\n" + "=" * 70)
        print("Verification Summary")
        print("=" * 70)

        print(f"\nℹ Export Format: v{self.export_version}")
        print("\n📊 Export Statistics:")
        if "entities" in self.stats:
            if "active" in self.stats["entities"]:
                print(f"  Entities: {self.stats['entities']['total']} ({self.stats['entities']['active']} active)")
            else:
                print(f"  Entities: {self.stats['entities']['total']}")
        if "devices" in self.stats:
            print(f"  Devices: {self.stats['devices']['total']}")
        if "integrations" in self.stats:
            print(f"  Integrations: {self.stats['integrations']['configured']}")
            print(f"  Custom Components: {self.stats['integrations']['custom']}")
        if "addons" in self.stats:
            print(f"  Add-ons: {self.stats['addons']['total']}")
        if "config_files" in self.stats:
            if "json" in self.stats["config_files"]:
                print(
                    "  Config Files: "
                    f"{self.stats['config_files']['yaml']} YAML, {self.stats['config_files']['json']} JSON"
                )
            else:
                print(f"  Config Files: {self.stats['config_files']['yaml']} YAML")
        if "secrets" in self.stats:
            print(f"  Secrets Replaced: {self.stats['secrets']['total']}")

        if self.issues:
            print(f"\n❌ Critical Issues Found: {len(self.issues)}")
            for issue in self.issues:
                print(f"  - {issue}")
        else:
            print("\n✅ No critical issues found")

        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  - {warning}")

        # Overall status
        print("\n" + "=" * 70)
        if not self.issues:
            print("✅ Export verification PASSED")
            print("\nYour export is complete and ready to use with AI assistants!")
        else:
            print("❌ Export verification FAILED")
            print("\nPlease re-run the export script to fix issues.")
        print("=" * 70)

        return {
            "success": len(self.issues) == 0,
            "export_version": self.export_version,
            "stats": self.stats,
            "issues": self.issues,
            "warnings": self.warnings,
        }

    def run(self):
        """Run all verification checks"""
        print("=" * 70)
        print("Home Assistant Export Verification Tool")
        print("=" * 70)
        print(f"\nVerifying: {self.export_path}")
        print(f"Export Format: v{self.export_version}")

        self.verify_structure()
        self.verify_entities()
        self.verify_devices()
        self.verify_config_files()
        self.verify_integrations()
        self.verify_secrets()
        self.verify_addons()

        report = self.generate_report()
        return report.get("success", False)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Verify Home Assistant export completeness")
    parser.add_argument("export_path", help="Path to extracted export directory or tarball")

    args = parser.parse_args()

    export_path = args.export_path

    # Check if it's a tarball
    if export_path.endswith(".tar.gz") or export_path.endswith(".tgz"):
        print("Extracting tarball...")
        extract_dir = os.path.join(tempfile.gettempdir(), "ha_verify_temp")
        os.makedirs(extract_dir, exist_ok=True)

        try:
            with tarfile.open(export_path, "r:gz") as tar:
                _safe_extract_tar(tar, extract_dir)

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
