#!/usr/bin/env python3
"""
Unit tests for workflow_config module.
"""

import os
import sys

import pytest
import yaml

# Add bin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

from workflow_config import WorkflowConfig  # noqa: E402


@pytest.mark.unit
class TestPathExpansion:
    """Test that _expand_paths resolves relative paths to absolute."""

    def test_default_paths_are_absolute(self):
        """Default relative paths like ./exports should be resolved to absolute."""
        config = WorkflowConfig()
        for key in [
            "export_dir",
            "import_dir",
            "secrets_dir",
            "backup_dir",
            "ai_context_dir",
        ]:
            path = config.get(f"paths.{key}")
            assert os.path.isabs(path), f"paths.{key} is not absolute: {path}"

    def test_default_secrets_key_file_is_absolute(self):
        """Default secrets.key_file should be resolved to absolute."""
        config = WorkflowConfig()
        key_file = config.get("secrets.key_file")
        assert os.path.isabs(key_file), f"secrets.key_file is not absolute: {key_file}"

    def test_relative_paths_resolve_to_cwd(self):
        """Relative paths should be resolved relative to the current working directory."""
        config = WorkflowConfig()
        export_dir = config.get("paths.export_dir")
        expected = os.path.join(os.getcwd(), "exports")
        assert export_dir == expected

    def test_absolute_paths_preserved(self, tmp_path):
        """Absolute paths in config should be preserved as-is."""
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            "paths": {
                "export_dir": "/tmp/my_ha_exports",
                "import_dir": "/tmp/my_ha_imports",
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = WorkflowConfig(str(config_file))
        assert config.get("paths.export_dir") == os.path.abspath("/tmp/my_ha_exports")
        assert config.get("paths.import_dir") == os.path.abspath("/tmp/my_ha_imports")

    def test_tilde_expansion(self, tmp_path):
        """Paths with ~ should be expanded to the home directory."""
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            "paths": {
                "export_dir": "~/ha_exports",
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = WorkflowConfig(str(config_file))
        export_dir = config.get("paths.export_dir")
        assert os.path.isabs(export_dir)
        assert "~" not in export_dir
        assert export_dir.startswith(os.path.expanduser("~"))

    def test_env_var_expansion(self, tmp_path, monkeypatch):
        """Paths with environment variables should be expanded."""
        monkeypatch.setenv("HA_TEST_DIR", "/tmp/ha_test")
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            "paths": {
                "export_dir": "$HA_TEST_DIR/exports",
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = WorkflowConfig(str(config_file))
        assert config.get("paths.export_dir") == os.path.abspath("/tmp/ha_test/exports")


@pytest.mark.unit
class TestWorkflowConfigBasics:
    """Test basic WorkflowConfig functionality."""

    def test_default_config_loaded(self):
        """Test that default config is loaded when no file exists."""
        config = WorkflowConfig()
        assert config.get("ssh.enabled") is False
        assert config.get("ssh.port") == 22
        assert config.get("secrets.label_prefix") == "HA_SECRET"

    def test_get_with_default(self):
        """Test get with default value for missing keys."""
        config = WorkflowConfig()
        assert config.get("nonexistent.key", "fallback") == "fallback"

    def test_set_and_get(self):
        """Test setting and getting values."""
        config = WorkflowConfig()
        config.set("ssh.host", "192.168.1.100")
        assert config.get("ssh.host") == "192.168.1.100"

    def test_deep_merge(self):
        """Test that user config is merged over defaults."""
        config = WorkflowConfig()
        # Default ssh.port should be 22
        assert config.get("ssh.port") == 22
        # Default export patterns should exist
        assert len(config.get("export.include_patterns", [])) > 0

    def test_save_and_load(self, tmp_path):
        """Test saving and loading config."""
        config = WorkflowConfig()
        config.set("ssh.host", "test-host")
        save_path = str(tmp_path / "test_config.yaml")
        config.save(save_path)

        config2 = WorkflowConfig(save_path)
        assert config2.get("ssh.host") == "test-host"

    def test_validate_creates_directories(self, tmp_path):
        """Test that validate creates configured directories."""
        config_file = tmp_path / "test_config.yaml"
        export_dir = str(tmp_path / "test_exports")
        config_data = {"paths": {"export_dir": export_dir}}
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = WorkflowConfig(str(config_file))
        is_valid, issues = config.validate()
        assert os.path.isdir(export_dir)
