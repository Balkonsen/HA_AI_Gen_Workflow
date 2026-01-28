#!/usr/bin/env python3
"""
Home Assistant Configuration Import Tool
Restores sanitized configuration files with original secrets
"""

import os
import sys
import json
import tarfile
import shutil
import re
from pathlib import Path
from datetime import datetime
import subprocess


class HAConfigImporter:
    def __init__(self, import_path, secrets_file):
        self.import_path = import_path
        self.secrets_file = secrets_file
        self.secrets_map = {}
        self.reverse_map = {}
        self.config_backup_path = f"/config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.dry_run = True
        self.changes_log = []

    def load_secrets(self):
        """Load secrets mapping file"""
        print("\n=== Loading Secrets ===")
        try:
            with open(self.secrets_file, "r") as f:
                secrets_data = json.load(f)

            self.secrets_map = secrets_data.get("secrets", {})
            # Create reverse map for replacement
            self.reverse_map = {v: k for k, v in self.secrets_map.items()}

            print(f"✓ Loaded {len(self.secrets_map)} secret mappings")
            return True
        except Exception as e:
            print(f"✗ Error loading secrets file: {e}")
            return False

    def restore_secrets(self, text):
        """Replace placeholders with original secrets"""
        if not isinstance(text, str):
            return text

        restored = text

        # Replace all placeholders with original values
        for placeholder, original in self.secrets_map.items():
            if placeholder in restored:
                restored = restored.replace(placeholder, original)
                self.changes_log.append(f"Restored secret: {placeholder}")

        return restored

    def backup_current_config(self):
        """Create backup of current configuration"""
        print("\n=== Creating Backup ===")

        if not os.path.exists("/config"):
            print("✗ /config directory not found")
            return False

        try:
            print(f"Backing up /config to {self.config_backup_path}")
            shutil.copytree(
                "/config",
                self.config_backup_path,
                ignore=shutil.ignore_patterns("*.db", "*.db-wal", "*.db-shm", "*.log", "deps", "tts", "__pycache__"),
            )
            print(f"✓ Backup created at {self.config_backup_path}")
            return True
        except Exception as e:
            print(f"✗ Backup failed: {e}")
            return False

    def process_file(self, source_file, dest_file):
        """Process and restore a single file"""
        try:
            with open(source_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Restore secrets
            restored_content = self.restore_secrets(content)

            # Create destination directory if needed
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)

            if self.dry_run:
                print(f"  [DRY RUN] Would write: {dest_file}")
                return True
            else:
                with open(dest_file, "w", encoding="utf-8") as f:
                    f.write(restored_content)
                print(f"  ✓ Restored: {dest_file}")
                return True

        except Exception as e:
            print(f"  ✗ Error processing {source_file}: {e}")
            return False

    def import_config_files(self):
        """Import configuration files"""
        print("\n=== Importing Configuration Files ===")

        config_source = os.path.join(self.import_path, "config")
        if not os.path.exists(config_source):
            print("✗ No config directory found in import")
            return False

        imported_count = 0

        for root, dirs, files in os.walk(config_source):
            for file in files:
                source_path = os.path.join(root, file)
                rel_path = os.path.relpath(source_path, config_source)
                dest_path = os.path.join("/config", rel_path)

                if self.process_file(source_path, dest_path):
                    imported_count += 1

        print(f"✓ {'Would import' if self.dry_run else 'Imported'} {imported_count} files")
        return True

    def import_addon_configs(self):
        """Import add-on configurations"""
        print("\n=== Importing Add-on Configurations ===")

        addon_source = os.path.join(self.import_path, "addons")
        if not os.path.exists(addon_source):
            print("⚠️  No addon configurations found in import")
            return True

        imported_count = 0

        for file in os.listdir(addon_source):
            if file.endswith("_options.json"):
                addon_name = file.replace("_options.json", "")
                source_file = os.path.join(addon_source, file)
                dest_dir = f"/data/addon_configs/{addon_name}"
                dest_file = os.path.join(dest_dir, "options.json")

                if self.process_file(source_file, dest_file):
                    imported_count += 1

        print(f"✓ {'Would import' if self.dry_run else 'Imported'} {imported_count} add-on configs")
        return True

    def show_changes_summary(self):
        """Display summary of changes"""
        print("\n" + "=" * 70)
        print("Changes Summary")
        print("=" * 70)

        if self.changes_log:
            print(f"\nTotal secret restorations: {len([c for c in self.changes_log if 'Restored secret' in c])}")

            # Show unique secret types
            secret_types = set()
            for log in self.changes_log:
                if "Restored secret" in log:
                    placeholder = log.split(": ")[1]
                    secret_type = placeholder.split("_")[0].replace("<<", "")
                    secret_types.add(secret_type)

            if secret_types:
                print(f"\nSecret types restored:")
                for stype in sorted(secret_types):
                    count = len([c for c in self.changes_log if stype in c])
                    print(f"  - {stype}: {count}")
        else:
            print("\nNo secrets were restored (none found in files)")

    def verify_import(self):
        """Verify imported configuration"""
        print("\n=== Verifying Import ===")

        checks = {
            "configuration.yaml": "/config/configuration.yaml",
            "automations": "/config/automations.yaml",
            "scripts": "/config/scripts.yaml",
        }

        all_ok = True
        for name, path in checks.items():
            if os.path.exists(path):
                print(f"✓ {name} exists")
            else:
                print(f"⚠️  {name} not found")
                all_ok = False

        return all_ok

    def generate_import_report(self):
        """Generate detailed import report"""
        report_path = f"/config/import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        report = f"""Home Assistant Configuration Import Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Import Source: {self.import_path}
Secrets File: {self.secrets_file}
Backup Location: {self.config_backup_path}

=== Import Statistics ===
Total secrets restored: {len([c for c in self.changes_log if 'Restored secret' in c])}
Total files processed: {len([c for c in self.changes_log if 'file' in c])}

=== Changes Log ===
"""
        for log in self.changes_log:
            report += f"{log}\n"

        report += f"""

=== Next Steps ===
1. Review the imported configuration files
2. Check Home Assistant configuration: ha core check
3. Restart Home Assistant: ha core restart
4. Monitor logs for any errors
5. If issues occur, restore from backup: {self.config_backup_path}

=== Rollback Instructions ===
If you need to rollback:
1. Stop Home Assistant
2. Remove /config directory
3. Restore from backup: mv {self.config_backup_path} /config
4. Restart Home Assistant
"""

        if self.dry_run:
            print("\n" + "=" * 70)
            print("DRY RUN REPORT")
            print("=" * 70)
            print(report)
        else:
            with open(report_path, "w") as f:
                f.write(report)
            print(f"\n✓ Import report saved to: {report_path}")

    def run(self, apply_changes=False):
        """Execute import process"""
        self.dry_run = not apply_changes

        print("=" * 70)
        print("Home Assistant Configuration Import Tool")
        print("=" * 70)

        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No changes will be made")
            print("Run with --apply to actually import configuration")

        # Load secrets
        if not self.load_secrets():
            return False

        # Create backup (only if applying changes)
        if not self.dry_run:
            if not self.backup_current_config():
                print("\n⚠️  Backup failed. Continue anyway?")
                response = input("Type 'yes' to continue: ")
                if response.lower() != "yes":
                    print("Import cancelled")
                    return False

        # Import files
        if not self.import_config_files():
            return False

        if not self.import_addon_configs():
            return False

        # Show results
        self.show_changes_summary()
        self.generate_import_report()

        if not self.dry_run:
            self.verify_import()

            print("\n" + "=" * 70)
            print("✓ Import Complete!")
            print("=" * 70)
            print("\nNext steps:")
            print("1. Check configuration: ha core check")
            print("2. Review import_report_*.txt in /config")
            print("3. Restart Home Assistant: ha core restart")
            print("4. Monitor logs for any errors")
            print(f"\n📦 Backup location: {self.config_backup_path}")
        else:
            print("\n" + "=" * 70)
            print("✓ Dry Run Complete!")
            print("=" * 70)
            print("\nTo apply these changes, run:")
            print(f"  {sys.argv[0]} --apply {self.import_path} {self.secrets_file}")

        return True


def extract_tarball(tarball_path):
    """Extract tarball and return path to extracted directory"""
    print(f"\n=== Extracting Tarball ===")
    print(f"Source: {tarball_path}")

    extract_dir = "/tmp/ha_import_temp"
    os.makedirs(extract_dir, exist_ok=True)

    try:
        with tarfile.open(tarball_path, "r:gz") as tar:
            tar.extractall(extract_dir)

        # Find the extracted directory
        extracted_dirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
        if extracted_dirs:
            extracted_path = os.path.join(extract_dir, extracted_dirs[0])
            print(f"✓ Extracted to: {extracted_path}")
            return extracted_path
        else:
            print("✗ No directory found in tarball")
            return None
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Import Home Assistant configuration with secret restoration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview changes)
  %(prog)s /path/to/export secrets_map.json
  
  # Actually apply changes
  %(prog)s --apply /path/to/export secrets_map.json
  
  # Import from tarball
  %(prog)s --apply /path/to/export.tar.gz secrets_map.json
        """,
    )

    parser.add_argument("import_path", help="Path to extracted export directory or tarball")
    parser.add_argument("secrets_file", help="Path to secrets_map.json file")
    parser.add_argument("--apply", action="store_true", help="Actually apply changes (default is dry run)")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation (not recommended)")

    args = parser.parse_args()

    # Check if running on HA host
    if not os.path.exists("/config"):
        print("✗ Error: /config directory not found")
        print("  This script must be run on a Home Assistant host")
        sys.exit(1)

    # Check if import path is a tarball
    import_path = args.import_path
    if import_path.endswith(".tar.gz") or import_path.endswith(".tgz"):
        extracted_path = extract_tarball(import_path)
        if not extracted_path:
            sys.exit(1)
        import_path = extracted_path

    # Verify import path exists
    if not os.path.exists(import_path):
        print(f"✗ Error: Import path not found: {import_path}")
        sys.exit(1)

    # Verify secrets file exists
    secrets_file = args.secrets_file
    if not os.path.exists(secrets_file):
        print(f"✗ Error: Secrets file not found: {secrets_file}")
        sys.exit(1)

    # Confirm if applying changes
    if args.apply:
        print("\n⚠️  WARNING: This will modify your Home Assistant configuration!")
        print(f"Import source: {import_path}")
        print(f"Secrets file: {secrets_file}")
        response = input("\nAre you sure you want to proceed? (type 'yes' to continue): ")
        if response.lower() != "yes":
            print("Import cancelled")
            sys.exit(0)

    # Run import
    importer = HAConfigImporter(import_path, secrets_file)
    success = importer.run(apply_changes=args.apply)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
