#!/usr/bin/env python3
"""
HA AI Workflow Orchestrator
Main entry point for the complete workflow: Export → AI Context → Import → Validate
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add bin directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow_config import WorkflowConfig
from secrets_manager import SecretsManager, SecretsSanitizer
from ssh_transfer import SSHTransfer, HARemoteManager
from ha_diagnostic_export import HAConfigExporter
from ha_ai_context_gen import HAContextGenerator
from ha_config_import import HAConfigImporter
from ha_export_verifier import ExportVerifier


class WorkflowOrchestrator:
    """Orchestrates the complete HA AI workflow."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize orchestrator.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = WorkflowConfig(config_path)
        self.secrets_manager = SecretsManager(
            secrets_dir=self.config.get('paths.secrets_dir'),
            label_prefix=self.config.get('secrets.label_prefix')
        )
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        for path_key in ['export_dir', 'import_dir', 'secrets_dir', 'backup_dir', 'ai_context_dir']:
            path = self.config.get(f'paths.{path_key}')
            if path:
                Path(path).mkdir(parents=True, exist_ok=True)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for naming."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def export_from_remote(self) -> Optional[str]:
        """Export configuration from remote Home Assistant.
        
        Returns:
            Path to exported directory or None on failure
        """
        if not self.config.get('ssh.enabled'):
            print("⚠ SSH not enabled. Configure SSH settings first.")
            return None
        
        ssh_config = self.config.get('ssh')
        remote_manager = HARemoteManager(ssh_config)
        
        timestamp = self._get_timestamp()
        export_dir = Path(self.config.get('paths.export_dir')) / f"export_{timestamp}"
        
        success = remote_manager.export_config(
            str(export_dir),
            self.config.get('export.exclude_patterns', [])
        )
        
        return str(export_dir) if success else None
    
    def export_local(self, source_path: str) -> Optional[str]:
        """Export from local Home Assistant configuration.
        
        Args:
            source_path: Path to local HA config
            
        Returns:
            Path to exported directory
        """
        timestamp = self._get_timestamp()
        export_dir = Path(self.config.get('paths.export_dir')) / f"export_{timestamp}"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        exporter = HAConfigExporter(output_dir=str(export_dir.parent))
        exporter.export_path = str(export_dir)
        
        print(f"\n📤 Exporting local configuration...")
        print(f"   Source: {source_path}")
        print(f"   Destination: {export_dir}")
        
        # Copy configuration files
        source = Path(source_path)
        if not source.exists():
            print(f"✗ Source path does not exist: {source_path}")
            return None
        
        # Export with sanitization
        config_dir = export_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        sanitizer = SecretsSanitizer(self.secrets_manager)
        
        for pattern in self.config.get('export.include_patterns', ['*.yaml']):
            for file_path in source.glob(pattern):
                if file_path.is_file():
                    relative = file_path.relative_to(source)
                    dest = config_dir / relative
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Sanitize YAML files
                    if file_path.suffix in ['.yaml', '.yml']:
                        sanitizer.sanitize_file(str(file_path), str(dest))
                    else:
                        shutil.copy2(file_path, dest)
        
        # Save secrets
        self.secrets_manager.save()
        
        print(f"✓ Export complete: {export_dir}")
        return str(export_dir)
    
    def sanitize_export(self, export_path: str) -> bool:
        """Sanitize an existing export directory.
        
        Args:
            export_path: Path to export directory
            
        Returns:
            True if successful
        """
        print(f"\n🔐 Sanitizing export: {export_path}")
        
        sanitizer = SecretsSanitizer(self.secrets_manager)
        export_dir = Path(export_path)
        
        # Find all YAML files
        yaml_files = list(export_dir.rglob('*.yaml')) + list(export_dir.rglob('*.yml'))
        
        sanitized_count = 0
        for yaml_file in yaml_files:
            if sanitizer.sanitize_file(str(yaml_file)):
                sanitized_count += 1
        
        # Save secrets
        self.secrets_manager.save()
        
        print(f"✓ Sanitized {sanitized_count} files")
        self.secrets_manager.print_summary()
        
        return True
    
    def generate_ai_context(self, export_path: str) -> Optional[str]:
        """Generate AI context from export.
        
        Args:
            export_path: Path to sanitized export
            
        Returns:
            Path to AI context directory
        """
        print(f"\n🤖 Generating AI context...")
        
        ai_context_dir = Path(self.config.get('paths.ai_context_dir'))
        timestamp = self._get_timestamp()
        context_dir = ai_context_dir / f"context_{timestamp}"
        context_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate context using HAContextGenerator
        generator = HAContextGenerator(export_path)
        
        # Generate context file
        context_file = context_dir / "AI_CONTEXT.md"
        generator.generate_context_file(str(context_file))
        
        # Generate AI prompt
        prompt_file = context_dir / "AI_PROMPT.md"
        generator.generate_ai_prompt(str(prompt_file))
        
        # Export secrets mapping for AI
        secrets_info_file = context_dir / "SECRETS_INFO.json"
        self.secrets_manager.export_for_ai(str(secrets_info_file))
        
        # Create instructions file
        self._create_ai_instructions(context_dir)
        
        print(f"✓ AI context generated: {context_dir}")
        return str(context_dir)
    
    def _create_ai_instructions(self, context_dir: Path):
        """Create AI instructions file."""
        instructions = """# AI Code Generation Instructions

## Important: Secret Placeholders

This export contains placeholder labels for sensitive data:

- Labels follow the format: `<<HA_SECRET_TYPE_NNN>>`
- Example: `<<HA_SECRET_PASSWORD_001>>`, `<<HA_SECRET_API_KEY_002>>`

**CRITICAL**: When generating or modifying code:
1. **PRESERVE** all `<<HA_SECRET_*>>` placeholders exactly as shown
2. Do NOT replace them with actual values or dummy data
3. Do NOT modify the label format
4. These placeholders will be automatically replaced during import

## Context Files

- `AI_CONTEXT.md` - Complete analysis of the Home Assistant configuration
- `AI_PROMPT.md` - Suggested prompts for AI assistance
- `SECRETS_INFO.json` - Metadata about secret placeholders (no actual secrets)

## Workflow

1. Use the context to understand the current HA setup
2. Generate code/modifications as requested
3. Ensure all secret placeholders are preserved
4. Export generated code for import back to HA

## Best Practices

- Maintain YAML formatting compatible with Home Assistant
- Use proper entity_id naming conventions
- Include comments for complex automations
- Test automation logic before deploying
"""
        
        with open(context_dir / "INSTRUCTIONS.md", 'w') as f:
            f.write(instructions)
    
    def import_to_remote(self, import_path: str, dry_run: bool = False) -> bool:
        """Import configuration to remote Home Assistant.
        
        Args:
            import_path: Path to configuration to import
            dry_run: If True, don't actually make changes
            
        Returns:
            True if successful
        """
        if not self.config.get('ssh.enabled'):
            print("⚠ SSH not enabled. Configure SSH settings first.")
            return False
        
        print(f"\n📥 Importing to remote Home Assistant...")
        
        # First restore secrets
        if self.config.get('secrets.auto_restore'):
            print("🔐 Restoring secrets...")
            self._restore_secrets_in_directory(import_path)
        
        if dry_run:
            print("ℹ Dry run mode - no changes will be made")
            return True
        
        ssh_config = self.config.get('ssh')
        remote_manager = HARemoteManager(ssh_config)
        
        return remote_manager.import_config(
            import_path,
            create_backup=True,
            restart=False
        )
    
    def import_local(self, import_path: str, target_path: str, 
                    dry_run: bool = False) -> bool:
        """Import configuration to local Home Assistant.
        
        Args:
            import_path: Path to configuration to import
            target_path: Target HA configuration path
            dry_run: If True, don't actually make changes
            
        Returns:
            True if successful
        """
        print(f"\n📥 Importing to local Home Assistant...")
        print(f"   Source: {import_path}")
        print(f"   Target: {target_path}")
        
        # First restore secrets in a temp directory
        temp_import = Path(import_path).parent / "temp_import"
        if temp_import.exists():
            shutil.rmtree(temp_import)
        shutil.copytree(import_path, temp_import)
        
        if self.config.get('secrets.auto_restore'):
            print("🔐 Restoring secrets...")
            self._restore_secrets_in_directory(str(temp_import))
        
        if dry_run:
            print("ℹ Dry run mode - changes prepared in:", temp_import)
            return True
        
        # Use HAConfigImporter for actual import
        secrets_file = Path(target_path) / "secrets.yaml"
        importer = HAConfigImporter(str(temp_import), str(secrets_file))
        
        return importer.run()
    
    def _restore_secrets_in_directory(self, directory: str):
        """Restore secrets in all files in a directory.
        
        Args:
            directory: Path to directory
        """
        dir_path = Path(directory)
        
        for yaml_file in list(dir_path.rglob('*.yaml')) + list(dir_path.rglob('*.yml')):
            self.secrets_manager.restore_secrets_in_file(str(yaml_file))
        
        print(f"✓ Secrets restored in {directory}")
    
    def validate_export(self, export_path: str) -> Dict[str, Any]:
        """Validate an export.
        
        Args:
            export_path: Path to export directory
            
        Returns:
            Validation results
        """
        print(f"\n🔍 Validating export: {export_path}")
        
        verifier = ExportVerifier(export_path)
        verifier.run()
        
        return verifier.generate_report()
    
    def run_full_workflow(self, source: str, mode: str = "local") -> bool:
        """Run the complete workflow.
        
        Args:
            source: Source path (local) or empty for SSH
            mode: "local" or "remote"
            
        Returns:
            True if successful
        """
        print("\n" + "=" * 60)
        print("🏠 HA AI Gen Workflow - Full Pipeline")
        print("=" * 60)
        
        # Step 1: Export
        print("\n[1/4] Exporting configuration...")
        if mode == "remote":
            export_path = self.export_from_remote()
        else:
            export_path = self.export_local(source)
        
        if not export_path:
            print("✗ Export failed")
            return False
        
        # Step 2: Sanitize
        print("\n[2/4] Sanitizing secrets...")
        if not self.sanitize_export(export_path):
            print("✗ Sanitization failed")
            return False
        
        # Step 3: Generate AI Context
        print("\n[3/4] Generating AI context...")
        context_path = self.generate_ai_context(export_path)
        
        if not context_path:
            print("✗ Context generation failed")
            return False
        
        # Step 4: Validate
        print("\n[4/4] Validating export...")
        validation = self.validate_export(export_path)
        
        print("\n" + "=" * 60)
        print("✓ Workflow Complete!")
        print("=" * 60)
        print(f"\n📁 Export Location: {export_path}")
        print(f"🤖 AI Context: {context_path}")
        print(f"🔐 Secrets: {self.config.get('paths.secrets_dir')}")
        print("\nNext Steps:")
        print("  1. Share AI context files with your AI assistant")
        print("  2. Generate modifications/automations")
        print("  3. Place results in import directory")
        print("  4. Run import workflow")
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='HA AI Gen Workflow Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  setup         Interactive configuration setup
  export        Export HA configuration
  sanitize      Sanitize secrets in export
  context       Generate AI context
  import        Import configuration to HA
  validate      Validate export/import
  full          Run complete workflow
  
Examples:
  %(prog)s setup
  %(prog)s export --source /config
  %(prog)s full --source /config
  %(prog)s import --source ./imports/my_config
        """
    )
    
    parser.add_argument('command', choices=[
        'setup', 'export', 'sanitize', 'context', 'import', 'validate', 'full'
    ], help='Command to run')
    
    parser.add_argument('--config', '-c', help='Path to configuration file')
    parser.add_argument('--source', '-s', help='Source path for export/import')
    parser.add_argument('--target', '-t', help='Target path for import')
    parser.add_argument('--remote', '-r', action='store_true', help='Use SSH for remote HA')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Dry run (no changes)')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        from workflow_config import interactive_setup
        interactive_setup()
        return 0
    
    orchestrator = WorkflowOrchestrator(args.config)
    
    if args.command == 'export':
        if args.remote:
            result = orchestrator.export_from_remote()
        else:
            if not args.source:
                print("Error: --source required for local export")
                return 1
            result = orchestrator.export_local(args.source)
        return 0 if result else 1
    
    elif args.command == 'sanitize':
        if not args.source:
            print("Error: --source required")
            return 1
        result = orchestrator.sanitize_export(args.source)
        return 0 if result else 1
    
    elif args.command == 'context':
        if not args.source:
            print("Error: --source required")
            return 1
        result = orchestrator.generate_ai_context(args.source)
        return 0 if result else 1
    
    elif args.command == 'import':
        if not args.source:
            print("Error: --source required")
            return 1
        
        if args.remote:
            result = orchestrator.import_to_remote(args.source, args.dry_run)
        else:
            if not args.target:
                print("Error: --target required for local import")
                return 1
            result = orchestrator.import_local(args.source, args.target, args.dry_run)
        return 0 if result else 1
    
    elif args.command == 'validate':
        if not args.source:
            print("Error: --source required")
            return 1
        orchestrator.validate_export(args.source)
        return 0
    
    elif args.command == 'full':
        mode = "remote" if args.remote else "local"
        if mode == "local" and not args.source:
            print("Error: --source required for local workflow")
            return 1
        result = orchestrator.run_full_workflow(args.source or "", mode)
        return 0 if result else 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
