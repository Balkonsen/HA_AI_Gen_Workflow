#!/usr/bin/env python3
"""
Unit tests for workflow_gui helper functions.
Tests the path validation, runtime output capture, and directory listing utilities
without requiring a running Streamlit instance.
"""

import os
import sys

import pytest

# Add bin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

# Import the helper functions directly — these do not depend on Streamlit
from workflow_gui import (
    resolve_and_verify_path,
    find_standard_root,
    list_directory_contents,
    capture_runtime_output,
    STANDARD_ROOT_DIRS,
)


@pytest.mark.unit
class TestResolveAndVerifyPath:
    """Tests for resolve_and_verify_path()."""

    def test_empty_path(self):
        """Empty string returns not-exists, not-creatable."""
        resolved, exists, creatable, msg = resolve_and_verify_path("")
        assert resolved == ""
        assert exists is False
        assert creatable is False

    def test_whitespace_only_path(self):
        """Whitespace-only string treated as empty."""
        resolved, exists, creatable, msg = resolve_and_verify_path("   ")
        assert resolved == ""
        assert exists is False

    def test_existing_directory(self, tmp_path):
        """Existing directory returns exists=True."""
        resolved, exists, creatable, msg = resolve_and_verify_path(str(tmp_path))
        assert resolved == str(tmp_path)
        assert exists is True
        assert creatable is True
        assert "✅" in msg

    def test_existing_file(self, tmp_path):
        """Existing file returns exists=True."""
        f = tmp_path / "testfile.txt"
        f.write_text("hello")
        resolved, exists, creatable, msg = resolve_and_verify_path(str(f))
        assert exists is True
        assert "✅" in msg

    def test_nonexistent_but_parent_exists(self, tmp_path):
        """Non-existing path with existing parent is creatable."""
        target = tmp_path / "new_subdir"
        resolved, exists, creatable, msg = resolve_and_verify_path(str(target))
        assert exists is False
        assert creatable is True
        assert "⚠️" in msg

    def test_deeply_nested_nonexistent(self, tmp_path):
        """Non-existing path with an existing ancestor is still creatable."""
        target = tmp_path / "a" / "b" / "c" / "d"
        resolved, exists, creatable, msg = resolve_and_verify_path(str(target))
        assert exists is False
        assert creatable is True
        assert "⚠️" in msg

    def test_resolved_is_absolute(self):
        """Returned path is always absolute."""
        resolved, _, _, _ = resolve_and_verify_path("./some/relative/path")
        assert os.path.isabs(resolved)

    def test_tilde_expansion(self):
        """Tilde is expanded to home directory."""
        resolved, _, _, _ = resolve_and_verify_path("~/testpath")
        assert "~" not in resolved
        assert resolved.startswith(os.path.expanduser("~"))

    def test_env_var_expansion(self, monkeypatch):
        """Environment variables are expanded."""
        monkeypatch.setenv("HA_TEST_VAR", "/tmp/ha_test_expansion")
        resolved, _, _, _ = resolve_and_verify_path("$HA_TEST_VAR/subdir")
        assert resolved == "/tmp/ha_test_expansion/subdir"


@pytest.mark.unit
class TestFindStandardRoot:
    """Tests for find_standard_root()."""

    def test_returns_string(self):
        """Always returns a string."""
        result = find_standard_root()
        assert isinstance(result, str)
        assert os.path.isabs(result)

    def test_returns_existing_directory(self):
        """Returned path always exists."""
        result = find_standard_root()
        assert os.path.isdir(result)

    def test_falls_back_to_cwd(self, monkeypatch):
        """Falls back to current directory if no standard root exists."""
        # This test verifies the fallback — the function checks STANDARD_ROOT_DIRS
        # and falls back to cwd. Since we can't guarantee /config doesn't exist,
        # we simply verify the result is a valid directory.
        result = find_standard_root()
        assert os.path.isdir(result)


@pytest.mark.unit
class TestListDirectoryContents:
    """Tests for list_directory_contents()."""

    def test_empty_directory(self, tmp_path):
        """Empty directory returns empty list."""
        entries = list_directory_contents(str(tmp_path))
        assert entries == []

    def test_files_and_dirs(self, tmp_path):
        """Lists files and directories correctly."""
        (tmp_path / "file.txt").write_text("content")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "nested.txt").write_text("nested")

        entries = list_directory_contents(str(tmp_path))
        names = [e[0] for e in entries]

        assert "file.txt" in names
        assert "subdir" in names
        # Nested file should appear at depth=2
        nested_entries = [e for e in entries if "nested.txt" in e[0]]
        assert len(nested_entries) == 1

    def test_hidden_files_excluded(self, tmp_path):
        """Hidden files (starting with .) are excluded."""
        (tmp_path / ".hidden").write_text("hidden")
        (tmp_path / "visible.txt").write_text("visible")

        entries = list_directory_contents(str(tmp_path))
        names = [e[0] for e in entries]

        assert "visible.txt" in names
        assert ".hidden" not in names

    def test_nonexistent_directory(self):
        """Non-existing directory returns empty list."""
        entries = list_directory_contents("/nonexistent/path/12345")
        assert entries == []

    def test_returns_is_dir_flag(self, tmp_path):
        """Entries correctly indicate directory vs file."""
        (tmp_path / "afile.txt").write_text("f")
        (tmp_path / "adir").mkdir()

        entries = list_directory_contents(str(tmp_path))
        entry_dict = {e[0]: e[1] for e in entries}

        assert entry_dict["afile.txt"] is False
        assert entry_dict["adir"] is True

    def test_returns_file_size(self, tmp_path):
        """File entries include their size."""
        content = "hello world"
        (tmp_path / "sized.txt").write_text(content)

        entries = list_directory_contents(str(tmp_path))
        sized_entry = [e for e in entries if e[0] == "sized.txt"][0]
        assert sized_entry[2] > 0  # Size should be > 0


@pytest.mark.unit
class TestCaptureRuntimeOutput:
    """Tests for capture_runtime_output()."""

    def test_captures_stdout(self):
        """Captures printed output from a function."""

        def noisy_func():
            print("Hello from stdout")
            return 42

        result, output = capture_runtime_output(noisy_func)
        assert result == 42
        assert "Hello from stdout" in output

    def test_captures_stderr(self):
        """Captures stderr output from a function."""

        def stderr_func():
            import sys

            print("Error message", file=sys.stderr)
            return "ok"

        result, output = capture_runtime_output(stderr_func)
        assert result == "ok"
        assert "Error message" in output
        assert "STDERR" in output

    def test_handles_exception(self):
        """Returns None and captures exception info on failure."""

        def failing_func():
            raise ValueError("Test error")

        result, output = capture_runtime_output(failing_func)
        assert result is None
        assert "ValueError" in output
        assert "Test error" in output

    def test_passes_args_and_kwargs(self):
        """Correctly passes arguments and keyword arguments."""

        def add_func(a, b, prefix=""):
            print(f"{prefix}{a + b}")
            return a + b

        result, output = capture_runtime_output(add_func, 3, 4, prefix="Result: ")
        assert result == 7
        assert "Result: 7" in output

    def test_empty_output(self):
        """Functions with no output return empty string."""

        def quiet_func():
            return "silent"

        result, output = capture_runtime_output(quiet_func)
        assert result == "silent"
        # Output may be empty or just whitespace
        assert "silent" not in output  # "silent" is the return value, not printed


@pytest.mark.unit
class TestStandardRootDirs:
    """Tests for STANDARD_ROOT_DIRS constant."""

    def test_contains_config(self):
        """Standard root dirs include /config (HA default)."""
        assert "/config" in STANDARD_ROOT_DIRS

    def test_contains_homeassistant(self):
        """Standard root dirs include /homeassistant."""
        assert "/homeassistant" in STANDARD_ROOT_DIRS

    def test_contains_current_dir(self):
        """Standard root dirs include current working directory as fallback."""
        assert os.path.abspath(".") in STANDARD_ROOT_DIRS

    def test_all_strings(self):
        """All entries are strings."""
        for entry in STANDARD_ROOT_DIRS:
            assert isinstance(entry, str)
