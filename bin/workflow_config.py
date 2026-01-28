#!/usr/bin/env python3
"""
Workflow Configuration Manager
Handles loading, validation and management of workflow configuration.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional


class WorkflowConfig:
    """Manages workflow configuration with defaults and validation."""

    DEFAULT_CONFIG = {
        "ssh": {
            "enabled": False,
            "host": "",
            "port": 22,
            "user": "root",
            "auth_method": "key",
            "key_path": "~/.ssh/id_rsa",
            "remote_config_path": "/config",
        },
        "paths": {
            "export_dir": "./exports",
            "import_dir": "./imports",
            "secrets_dir": "./secrets",
            "backup_dir": "./backups",
            "ai_context_dir": "./ai_context",
        },
        "export": {
            "include_patterns": ["*.yaml", "*.yml", "*.json"],
            "exclude_patterns": ["secrets.yaml", "*.log", "*.db"],
            "sensitive_fields": ["password", "token", "api_key", "secret"],
        },
        "secrets": {
            "encryption_method": "fernet",
            "key_file": "./secrets/.encryption_key",
            "label_prefix": "HA_SECRET",
            "auto_restore": True,
        },
        "ai": {
            "context": {
                "include_entities": True,
                "include_devices": True,
                "include_automations": True,
                "include_integrations": True,
                "max_size_kb": 500,
            },
            "prompt_template": "templates/example_ai_prompts.md",
        },
        "validation": {
            "check_yaml_syntax": True,
            "check_secrets_references": True,
            "check_entity_ids": True,
            "run_ha_check": False,
        },
        "vscode": {"notifications": True, "auto_open_files": True, "use_integrated_terminal": True},
    }

    CONFIG_LOCATIONS = [
        "workflow_config.yaml",
        "config/workflow_config.yaml",
        ".ha_workflow_config.yaml",
        os.path.expanduser("~/.ha_workflow_config.yaml"),
    ]

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_path: Optional explicit path to config file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._expand_paths()

    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in standard locations."""
        if self.config_path and os.path.exists(self.config_path):
            return self.config_path

        for location in self.CONFIG_LOCATIONS:
            if os.path.exists(location):
                return location

        return None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        config = self.DEFAULT_CONFIG.copy()

        config_file = self._find_config_file()
        if config_file:
            try:
                with open(config_file, "r") as f:
                    user_config = yaml.safe_load(f) or {}
                config = self._deep_merge(config, user_config)
                self.config_path = config_file
                print(f"✓ Configuration loaded from: {config_file}")
            except Exception as e:
                print(f"⚠ Error loading config: {e}, using defaults")
        else:
            print("ℹ No config file found, using defaults")

        return config

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _expand_paths(self):
        """Expand ~ and environment variables in paths."""
        if "paths" in self.config:
            for key, value in self.config["paths"].items():
                if isinstance(value, str):
                    self.config["paths"][key] = os.path.expanduser(os.path.expandvars(value))

        if "ssh" in self.config and "key_path" in self.config["ssh"]:
            self.config["ssh"]["key_path"] = os.path.expanduser(self.config["ssh"]["key_path"])

        if "secrets" in self.config and "key_file" in self.config["secrets"]:
            self.config["secrets"]["key_file"] = os.path.expanduser(self.config["secrets"]["key_file"])

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.

        Args:
            key: Dot-notation key like 'ssh.host'
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value by dot-notation key.

        Args:
            key: Dot-notation key like 'ssh.host'
            value: Value to set
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: Optional[str] = None):
        """Save current configuration to file.

        Args:
            path: Optional path to save to (defaults to loaded path)
        """
        save_path = path or self.config_path or "workflow_config.yaml"

        # Ensure directory exists
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

        print(f"✓ Configuration saved to: {save_path}")

    def validate(self) -> tuple:
        """Validate configuration.

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        # Check SSH config if enabled
        if self.get("ssh.enabled"):
            if not self.get("ssh.host"):
                issues.append("SSH enabled but no host specified")
            if self.get("ssh.auth_method") == "key":
                key_path = self.get("ssh.key_path")
                if not os.path.exists(key_path):
                    issues.append(f"SSH key not found: {key_path}")

        # Check paths exist or can be created
        for path_key in ["export_dir", "import_dir", "secrets_dir", "backup_dir"]:
            path = self.get(f"paths.{path_key}")
            if path:
                try:
                    Path(path).mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create {path_key}: {e}")

        return len(issues) == 0, issues

    def print_summary(self):
        """Print configuration summary."""
        print("\n" + "=" * 60)
        print("Workflow Configuration Summary")
        print("=" * 60)

        print(f"\n📡 SSH Connection:")
        if self.get("ssh.enabled"):
            print(f"   Host: {self.get('ssh.user')}@{self.get('ssh.host')}:{self.get('ssh.port')}")
            print(f"   Auth: {self.get('ssh.auth_method')}")
            print(f"   Remote Path: {self.get('ssh.remote_config_path')}")
        else:
            print("   Disabled (local mode)")

        print(f"\n📁 Paths:")
        print(f"   Export: {self.get('paths.export_dir')}")
        print(f"   Import: {self.get('paths.import_dir')}")
        print(f"   Secrets: {self.get('paths.secrets_dir')}")
        print(f"   Backups: {self.get('paths.backup_dir')}")

        print(f"\n🔐 Secrets:")
        print(f"   Encryption: {self.get('secrets.encryption_method')}")
        print(f"   Label Prefix: {self.get('secrets.label_prefix')}")
        print(f"   Auto-restore: {self.get('secrets.auto_restore')}")

        print("\n" + "=" * 60)

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self.config.copy()

    def to_json(self) -> str:
        """Return configuration as JSON string."""
        return json.dumps(self.config, indent=2)


def interactive_setup():
    """Interactive configuration setup wizard."""
    print("\n" + "=" * 60)
    print("🏠 HA AI Workflow Configuration Setup")
    print("=" * 60)

    config = WorkflowConfig()

    # SSH Setup
    print("\n📡 SSH Connection Setup")
    print("-" * 40)

    use_ssh = input("Connect to remote Home Assistant via SSH? (y/n) [n]: ").lower().strip()
    config.set("ssh.enabled", use_ssh == "y")

    if use_ssh == "y":
        host = input("SSH Host (IP or hostname): ").strip()
        if host:
            config.set("ssh.host", host)

        port = input(f"SSH Port [{config.get('ssh.port')}]: ").strip()
        if port:
            config.set("ssh.port", int(port))

        user = input(f"SSH Username [{config.get('ssh.user')}]: ").strip()
        if user:
            config.set("ssh.user", user)

        auth = input("Authentication method (key/password) [key]: ").strip().lower()
        if auth in ["key", "password"]:
            config.set("ssh.auth_method", auth)

        if config.get("ssh.auth_method") == "key":
            key_path = input(f"SSH Key Path [{config.get('ssh.key_path')}]: ").strip()
            if key_path:
                config.set("ssh.key_path", key_path)

        remote_path = input(f"Remote HA Config Path [{config.get('ssh.remote_config_path')}]: ").strip()
        if remote_path:
            config.set("ssh.remote_config_path", remote_path)

    # Path Setup
    print("\n📁 Local Path Setup")
    print("-" * 40)

    for path_key, description in [
        ("export_dir", "Export directory"),
        ("import_dir", "Import directory"),
        ("secrets_dir", "Secrets directory"),
        ("backup_dir", "Backup directory"),
    ]:
        current = config.get(f"paths.{path_key}")
        new_path = input(f"{description} [{current}]: ").strip()
        if new_path:
            config.set(f"paths.{path_key}", new_path)

    # Secrets Setup
    print("\n🔐 Secrets Encryption Setup")
    print("-" * 40)

    label_prefix = input(f"Secret label prefix [{config.get('secrets.label_prefix')}]: ").strip()
    if label_prefix:
        config.set("secrets.label_prefix", label_prefix)

    # Validate and save
    print("\n✓ Validating configuration...")
    is_valid, issues = config.validate()

    if not is_valid:
        print("⚠ Configuration issues found:")
        for issue in issues:
            print(f"   - {issue}")

    config.print_summary()

    save = input("\nSave configuration? (y/n) [y]: ").lower().strip()
    if save != "n":
        config.save("workflow_config.yaml")
        print("\n✓ Setup complete! Configuration saved to workflow_config.yaml")

    return config


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        interactive_setup()
    else:
        config = WorkflowConfig()
        config.print_summary()
