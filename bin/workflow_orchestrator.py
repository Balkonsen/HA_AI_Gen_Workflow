#!/usr/bin/env python3
"""
HA AI Workflow Orchestrator
Main entry point for the complete workflow: Export → AI Context → Import → Validate
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add bin directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow_config import WorkflowConfig  # noqa: E402
from workflow_logger import get_logger, configure_logger, trace_calls  # noqa: E402
from secrets_manager import SecretsManager, SecretsSanitizer  # noqa: E402
from ssh_transfer import HARemoteManager  # noqa: E402
from ha_diagnostic_export import HAConfigExporter  # noqa: E402
from ha_ai_context_gen import HAContextGenerator  # noqa: E402
from ha_config_import import HAConfigImporter  # noqa: E402
from ha_export_verifier import ExportVerifier  # noqa: E402


class WorkflowOrchestrator:
    """Orchestrates the complete HA AI workflow."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        ssh_timeout: Optional[int] = None,
        transfer_timeout: Optional[int] = None,
        log_level: Optional[str] = None,
        log_file: Optional[str] = None,
        trace_enabled: Optional[bool] = None,
        trace_log_file: Optional[str] = None,
        strict_warnings: bool = False,
    ):
        """Initialize orchestrator.

        Args:
            config_path: Optional path to configuration file
            ssh_timeout: Override SSH connection timeout from CLI
            transfer_timeout: Override file transfer timeout from CLI
            log_level: Log level (DEBUG, VERBOSE, INFO, CONDENSED, WARNING, ERROR)
            log_file: Path to log file
            trace_enabled: Enable structured trace logging
            trace_log_file: Optional path to trace log output file
            strict_warnings: Treat warnings as failures in integrated workflow mode
        """
        # Configure logger first
        if log_level or log_file or trace_enabled is not None or trace_log_file:
            self.logger = configure_logger(
                log_level=log_level,
                log_file=log_file,
                trace_enabled=trace_enabled,
                trace_log_file=trace_log_file,
            )
        else:
            self.logger = get_logger()

        self.config = WorkflowConfig(config_path)
        self.secrets_manager = SecretsManager(
            secrets_dir=self.config.get("paths.secrets_dir"),
            label_prefix=self.config.get("secrets.label_prefix"),
        )

        # Store CLI overrides for timeouts
        self.ssh_timeout_override = ssh_timeout
        self.transfer_timeout_override = transfer_timeout
        self.strict_warnings = strict_warnings

        self._ensure_directories()

        self._trace_integrated_phase(
            "phase_0_intake_and_risk",
            "initialized",
            {
                "strict_warnings": self.strict_warnings,
                "trace_enabled": self.logger.trace_enabled,
                "skills": [
                    "ha-ai-export-pipeline",
                    "ha-pr-quality-gate",
                    "ha-release-version-sync",
                ],
            },
        )

    def _trace_integrated_phase(
        self,
        phase: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Emit a structured event for integrated agent workflow visibility."""
        self.logger.trace_event(
            "integrated_agent_workflow.phase",
            {
                "phase": phase,
                "status": status,
                "details": details or {},
            },
        )

    def _ensure_directories(self):
        """Ensure all required directories exist."""
        for path_key in [
            "export_dir",
            "import_dir",
            "secrets_dir",
            "backup_dir",
            "ai_context_dir",
        ]:
            path = self.config.get(f"paths.{path_key}")
            if path:
                Path(path).mkdir(parents=True, exist_ok=True)

    def _get_timestamp(self) -> str:
        """Get current timestamp for naming."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    @trace_calls()
    def export_from_remote(self) -> Optional[str]:
        """Export configuration from remote Home Assistant.

        Returns:
            Path to exported directory or None on failure
        """
        if not self.config.get("ssh.enabled"):
            self.logger.warning("SSH not enabled. Configure SSH settings first.")
            return None

        self.logger.push_context("Remote Export")
        try:
            ssh_config = self.config.get("ssh")

            # Apply CLI overrides for timeouts
            if self.ssh_timeout_override:
                ssh_config["connection_timeout"] = self.ssh_timeout_override
            if self.transfer_timeout_override:
                ssh_config["transfer_timeout"] = self.transfer_timeout_override

            remote_manager = HARemoteManager(ssh_config)

            timestamp = self._get_timestamp()
            export_dir = Path(self.config.get("paths.export_dir")) / f"export_{timestamp}"

            self.logger.info(f"Starting remote export to {export_dir}")
            success = remote_manager.export_config(str(export_dir), self.config.get("export.exclude_patterns", []))

            if success:
                self.logger.success(f"Remote export completed: {export_dir}")
            else:
                self.logger.error("Remote export failed")

            return str(export_dir) if success else None
        except Exception as e:
            self.logger.log_exception(e, "Remote export failed")
            return None
        finally:
            self.logger.pop_context()

    @trace_calls()
    def export_local(self, source_path: str) -> Optional[str]:
        """Export from local Home Assistant configuration.

        Args:
            source_path: Path to local HA config

        Returns:
            Path to exported directory
        """
        self.logger.push_context("Local Export")
        try:
            timestamp = self._get_timestamp()
            export_name = f"export_{timestamp}"
            export_base_dir = Path(self.config.get("paths.export_dir"))
            export_base_dir.mkdir(parents=True, exist_ok=True)

            exporter = HAConfigExporter(output_dir=str(export_base_dir), config_dir=source_path)
            exporter.export_name = export_name
            exporter._update_paths()
            export_dir = Path(exporter.export_path)

            self.logger.banner("Exporting Local Configuration")
            self.logger.info(f"Source: {source_path}")
            self.logger.info(f"Destination: {export_dir}")

            source = Path(source_path)
            if not source.exists():
                self.logger.error(f"Source path does not exist: {source_path}")
                return None

            # Run the native exporter to produce verifier-compatible v2.0 output.
            result_tarball = exporter.run()
            if not result_tarball or not export_dir.exists():
                self.logger.error("Local export failed to create output artifacts")
                return None

            self.logger.success(f"Export complete: {export_dir}")
            return str(export_dir)
        except Exception as e:
            self.logger.log_exception(e, "Local export failed")
            return None
        finally:
            self.logger.pop_context()

    @trace_calls()
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

        # v2.0 exports are already sanitized by HAConfigExporter.
        if (export_dir / "ai_upload").exists():
            print("ℹ Export appears to be v2.0 and already sanitized; skipping additional sanitization")
            return True

        # Find all YAML files
        yaml_files = list(export_dir.rglob("*.yaml")) + list(export_dir.rglob("*.yml"))

        sanitized_count = 0
        for yaml_file in yaml_files:
            if sanitizer.sanitize_file(str(yaml_file)):
                sanitized_count += 1

        # Save secrets
        self.secrets_manager.save()

        print(f"✓ Sanitized {sanitized_count} files")
        self.secrets_manager.print_summary()

        return True

    @trace_calls()
    def generate_ai_context(self, export_path: str) -> Optional[str]:
        """Generate AI context from export.

        Args:
            export_path: Path to sanitized export

        Returns:
            Path to export directory containing AI context files
        """
        print("\n🤖 Generating AI context...")

        export_dir = Path(export_path)
        if (export_dir / "ai_upload").exists():
            print("ℹ Export appears to be v2.0; AI context is already generated in ai_upload/")
            self._create_ai_instructions(export_dir)
            return export_path

        # Generate context using HAContextGenerator
        # It will create AI_CONTEXT.json and AI_PROMPT.md in the export_path
        generator = HAContextGenerator(export_path)

        try:
            # Generate context file - returns tuple of (context_file, prompt_file) paths
            context_file, prompt_file = generator.generate_context_file()

            # Export secrets mapping for AI (optional, only if secrets exist)
            secrets_info_file = os.path.join(export_path, "SECRETS_INFO.json")
            try:
                self.secrets_manager.export_for_ai(secrets_info_file)
            except Exception as e:
                print(f"  Note: Could not export secrets info: {e}")

            # Create instructions file
            self._create_ai_instructions(export_dir)

            print(f"✓ AI context generated in: {export_path}")
            print(f"  - {os.path.basename(context_file)}")
            print(f"  - {os.path.basename(prompt_file)}")
            return export_path

        except Exception as e:
            print(f"✗ Failed to generate AI context: {e}")
            import traceback

            traceback.print_exc()
            return None

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

        with open(context_dir / "INSTRUCTIONS.md", "w") as f:
            f.write(instructions)

    @trace_calls()
    def import_to_remote(self, import_path: str, dry_run: bool = False) -> bool:
        """Import configuration to remote Home Assistant.

        Args:
            import_path: Path to configuration to import
            dry_run: If True, don't actually make changes

        Returns:
            True if successful
        """
        if not self.config.get("ssh.enabled"):
            print("⚠ SSH not enabled. Configure SSH settings first.")
            return False

        print("\n📥 Importing to remote Home Assistant...")

        # First restore secrets
        if self.config.get("secrets.auto_restore"):
            print("🔐 Restoring secrets...")
            self._restore_secrets_in_directory(import_path)

        if dry_run:
            print("ℹ Dry run mode - no changes will be made")
            return True

        ssh_config = self.config.get("ssh")

        # Apply CLI overrides for timeouts
        if self.ssh_timeout_override:
            ssh_config["connection_timeout"] = self.ssh_timeout_override
        if self.transfer_timeout_override:
            ssh_config["transfer_timeout"] = self.transfer_timeout_override

        remote_manager = HARemoteManager(ssh_config)

        return remote_manager.import_config(import_path, create_backup=True, restart=False)

    @trace_calls()
    def import_local(self, import_path: str, target_path: str, dry_run: bool = False) -> bool:
        """Import configuration to local Home Assistant.

        Args:
            import_path: Path to configuration to import
            target_path: Target HA configuration path
            dry_run: If True, don't actually make changes

        Returns:
            True if successful
        """
        print("\n📥 Importing to local Home Assistant...")
        print(f"   Source: {import_path}")
        print(f"   Target: {target_path}")

        # First restore secrets in a temp directory
        temp_import = Path(import_path).parent / "temp_import"
        if temp_import.exists():
            shutil.rmtree(temp_import)
        shutil.copytree(import_path, temp_import)

        if self.config.get("secrets.auto_restore"):
            print("🔐 Restoring secrets...")
            self._restore_secrets_in_directory(str(temp_import))

        if dry_run:
            print("ℹ Dry run mode - changes prepared in:", temp_import)
            return True

        # v2 exports contain aggregated AI upload files; apply them directly to local target.
        v2_config_file = temp_import / "ai_upload" / "ha_config.yaml"
        if v2_config_file.exists():
            return self._apply_v2_local_import(v2_config_file, target_path)

        # Use HAConfigImporter for actual import
        secrets_file = Path(target_path) / "secrets.yaml"
        importer = HAConfigImporter(str(temp_import), str(secrets_file))

        return importer.run()

    def _apply_v2_local_import(self, v2_config_file: Path, target_path: str) -> bool:
        """Apply a v2 exported configuration file into a local HA target directory."""
        try:
            target_dir = Path(target_path)
            target_dir.mkdir(parents=True, exist_ok=True)
            raw_content = v2_config_file.read_text(encoding="utf-8")

            section_map = {
                "CONFIGURATION.YAML": "configuration.yaml",
                "AUTOMATIONS.YAML": "automations.yaml",
                "SCRIPTS.YAML": "scripts.yaml",
            }

            extracted_sections: Dict[str, list[str]] = {name: [] for name in section_map}
            current_section: Optional[str] = None

            for line in raw_content.splitlines():
                if line.startswith("# ======") and line.endswith("======"):
                    marker = line.replace("#", "").replace("=", "").strip()
                    current_section = marker if marker in extracted_sections else None
                    continue
                if current_section:
                    extracted_sections[current_section].append(line)

            files_written = 0
            for section_name, file_name in section_map.items():
                section_lines = extracted_sections.get(section_name, [])
                if not section_lines:
                    continue

                destination = target_dir / file_name
                if destination.exists():
                    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = target_dir / f"{file_name}.pre_import_{stamp}.bak"
                    shutil.copy2(destination, backup_path)
                    print(f"💾 Backup created: {backup_path}")

                rendered = "\n".join(section_lines).strip() + "\n"
                destination.write_text(rendered, encoding="utf-8")
                files_written += 1
                print(f"✓ Applied v2 section to: {destination}")

            # Fallback: if section markers are missing, write the full file as configuration.yaml.
            if files_written == 0:
                destination = target_dir / "configuration.yaml"
                destination.write_text(raw_content, encoding="utf-8")
                files_written = 1
                print(f"✓ Applied raw v2 configuration to: {destination}")

            print(f"✓ Applied {files_written} v2 configuration file(s) to local target")
            return True
        except OSError as exc:
            self.logger.error(f"✗ Failed to write v2 configuration: {exc}")
            return False

    def _restore_secrets_in_directory(self, directory: str):
        """Restore secrets in all files in a directory.

        Args:
            directory: Path to directory
        """
        dir_path = Path(directory)

        for yaml_file in list(dir_path.rglob("*.yaml")) + list(dir_path.rglob("*.yml")):
            self.secrets_manager.restore_secrets_in_file(str(yaml_file))

        print(f"✓ Secrets restored in {directory}")

    @trace_calls()
    def validate_export(self, export_path: str) -> Dict[str, Any]:
        """Validate an export.

        Args:
            export_path: Path to export directory

        Returns:
            Validation results
        """
        print(f"\n🔍 Validating export: {export_path}")

        verifier = ExportVerifier(export_path)
        success = verifier.run()

        return {
            "success": success,
            "export_version": verifier.export_version,
            "stats": verifier.stats,
            "issues": verifier.issues,
            "warnings": verifier.warnings,
        }

    @trace_calls()
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

        self._trace_integrated_phase(
            "phase_1_targeted_context_bootstrap",
            "started",
            {"mode": mode, "source": source or "<remote>"},
        )

        self._trace_integrated_phase(
            "phase_2_reproduce_smallest_safe_scope",
            "completed",
            {
                "strategy": "full_pipeline_first_then_stepwise_fallback",
                "selected_skill": "ha-ai-export-pipeline",
            },
        )

        self._trace_integrated_phase(
            "phase_3_minimal_change_and_local_validation",
            "started",
            {"strict_warnings": self.strict_warnings},
        )

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
        validation_report = self.validate_export(export_path)

        if self.strict_warnings and validation_report.get("warnings"):
            warning_count = len(validation_report.get("warnings", []))
            self.logger.error(
                f"Validation produced {warning_count} warning(s); strict mode treats warnings as failures"
            )
            self._trace_integrated_phase(
                "phase_5_quality_gate_ladder",
                "failed",
                {
                    "gate": "validate_export",
                    "reason": "warnings_present",
                    "warning_count": warning_count,
                },
            )
            return False

        if not validation_report.get("success", False):
            self._trace_integrated_phase(
                "phase_5_quality_gate_ladder",
                "failed",
                {"gate": "validate_export", "reason": "validation_failed"},
            )
            print("✗ Validation failed")
            return False

        self._trace_integrated_phase(
            "phase_4_iterative_api_validation",
            "completed",
            {
                "validated": True,
                "export_version": validation_report.get("export_version"),
            },
        )

        self._trace_integrated_phase(
            "phase_5_quality_gate_ladder",
            "passed",
            {
                "gates": [
                    "export",
                    "sanitize",
                    "context",
                    "validate",
                ],
            },
        )

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
        description="HA AI Gen Workflow Orchestrator",
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
        """,
    )

    parser.add_argument(
        "command",
        choices=[
            "setup",
            "export",
            "sanitize",
            "context",
            "import",
            "validate",
            "full",
        ],
        help="Command to run",
    )

    parser.add_argument("--config", "-c", help="Path to configuration file")
    parser.add_argument("--source", "-s", help="Source path for export/import")
    parser.add_argument("--target", "-t", help="Target path for import")
    parser.add_argument("--remote", "-r", action="store_true", help="Use SSH for remote HA")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Dry run (no changes)")
    parser.add_argument(
        "--ssh-timeout",
        type=int,
        default=30,
        help="SSH connection timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--transfer-timeout",
        type=int,
        default=600,
        help="File transfer timeout in seconds (default: 600)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "VERBOSE", "INFO", "CONDENSED", "WARNING", "ERROR", "CRITICAL"],
        help="Set workflow log level",
    )
    parser.add_argument("--log-file", help="Path to workflow log file")
    parser.add_argument(
        "--trace-log",
        action="store_true",
        help="Enable full structured trace logging (JSONL)",
    )
    parser.add_argument(
        "--trace-log-file",
        help="Path to structured trace log file (JSONL)",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Treat warnings as failures during integrated workflow execution",
    )

    args = parser.parse_args()

    if args.command == "setup":
        from workflow_config import interactive_setup

        interactive_setup()
        return 0

    orchestrator = WorkflowOrchestrator(
        args.config,
        ssh_timeout=args.ssh_timeout,
        transfer_timeout=args.transfer_timeout,
        log_level=args.log_level,
        log_file=args.log_file,
        trace_enabled=args.trace_log,
        trace_log_file=args.trace_log_file,
        strict_warnings=args.strict_warnings,
    )

    if args.command == "export":
        if args.remote:
            result = orchestrator.export_from_remote()
        else:
            if not args.source:
                print("Error: --source required for local export")
                return 1
            result = orchestrator.export_local(args.source)
        return 0 if result else 1

    elif args.command == "sanitize":
        if not args.source:
            print("Error: --source required")
            return 1
        result = orchestrator.sanitize_export(args.source)
        return 0 if result else 1

    elif args.command == "context":
        if not args.source:
            print("Error: --source required")
            return 1
        result = orchestrator.generate_ai_context(args.source)
        return 0 if result else 1

    elif args.command == "import":
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

    elif args.command == "validate":
        if not args.source:
            print("Error: --source required")
            return 1
        result = orchestrator.validate_export(args.source)
        return 0 if result.get("success", False) else 1

    elif args.command == "full":
        mode = "remote" if args.remote else "local"
        if mode == "local" and not args.source:
            print("Error: --source required for local workflow")
            return 1
        result = orchestrator.run_full_workflow(args.source or "", mode)
        return 0 if result else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
