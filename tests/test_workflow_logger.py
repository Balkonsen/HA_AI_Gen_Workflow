#!/usr/bin/env python3
"""
Unit tests for workflow_logger module.
"""

import os
import sys
import json
from pathlib import Path

import pytest

# Add bin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

from workflow_logger import (  # noqa: E402
    WorkflowLogger,
    LogLevel,
    configure_logger,
    get_logger,
)


@pytest.fixture(autouse=True)
def reset_fixed_logger_files():
    """Remove fixed logger artifacts before each test for deterministic assertions."""
    for file_name in ["workflow.log", "workflow_trace.log"]:
        fixed_path = Path(os.path.abspath("./exports")) / file_name
        if fixed_path.exists():
            fixed_path.unlink()


@pytest.mark.unit
class TestLogLevel:
    """Test LogLevel enum."""

    def test_log_levels_ordered(self):
        """Test that log levels are correctly ordered."""
        assert LogLevel.DEBUG.value < LogLevel.VERBOSE.value
        assert LogLevel.VERBOSE.value < LogLevel.INFO.value
        assert LogLevel.INFO.value < LogLevel.CONDENSED.value
        assert LogLevel.CONDENSED.value < LogLevel.WARNING.value
        assert LogLevel.WARNING.value < LogLevel.ERROR.value
        assert LogLevel.ERROR.value < LogLevel.CRITICAL.value


@pytest.mark.unit
class TestWorkflowLogger:
    """Test WorkflowLogger class."""

    def test_logger_initialization(self, tmp_path):
        """Test logger initialization."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=str(log_file),
            enable_console=True,
            enable_colors=False,
        )

        assert logger.log_level == LogLevel.INFO
        assert logger.log_file is not None
        assert logger.log_file.endswith("workflow.log")
        assert logger.enable_console is True
        assert logger.enable_colors is False

    def test_should_log(self, tmp_path):
        """Test log level filtering."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(log_level=LogLevel.WARNING, log_file=str(log_file))

        # Should not log DEBUG, VERBOSE, INFO, CONDENSED
        assert not logger._should_log(LogLevel.DEBUG)
        assert not logger._should_log(LogLevel.VERBOSE)
        assert not logger._should_log(LogLevel.INFO)
        assert not logger._should_log(LogLevel.CONDENSED)

        # Should log WARNING, ERROR, CRITICAL
        assert logger._should_log(LogLevel.WARNING)
        assert logger._should_log(LogLevel.ERROR)
        assert logger._should_log(LogLevel.CRITICAL)

    def test_log_to_file(self, tmp_path):
        """Test logging to file."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=str(log_file),
            enable_console=False,
        )

        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")

        # Check file exists and has content
        effective_log_file = Path(logger.log_file)
        assert effective_log_file.exists()
        content = effective_log_file.read_text(encoding="utf-8")
        assert "Test info message" in content
        assert "Test warning message" in content
        assert "Test error message" in content
        assert "[INFO" in content
        assert "[WARNING" in content
        assert "[ERROR" in content

    def test_log_methods(self, tmp_path):
        """Test all log methods."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.DEBUG,
            log_file=str(log_file),
            enable_console=False,
        )

        logger.debug("Debug message")
        logger.verbose("Verbose message")
        logger.info("Info message")
        logger.condensed("Condensed message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        logger.success("Success message")
        logger.progress("Progress message")

        content = Path(logger.log_file).read_text(encoding="utf-8")
        assert "Debug message" in content
        assert "Verbose message" in content
        assert "Info message" in content
        assert "Condensed message" in content
        assert "Warning message" in content
        assert "Error message" in content
        assert "Critical message" in content
        assert "Success message" in content
        assert "Progress message" in content

    def test_json_format(self, tmp_path):
        """Test JSON log format."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=str(log_file),
            enable_console=False,
            log_format="json",
        )

        logger.info("Test JSON message")

        content = Path(logger.log_file).read_text(encoding="utf-8")
        lines = content.strip().split("\n")

        # Parse first line as JSON
        log_entry = json.loads(lines[0])
        assert log_entry["level"] == "INFO"
        assert log_entry["message"] == "Test JSON message"
        assert "timestamp" in log_entry
        assert "context" in log_entry

    def test_trace_log_captures_filtered_messages(self, tmp_path):
        """Trace log should capture all log calls including filtered entries."""
        log_file = tmp_path / "test.log"
        trace_file = tmp_path / "trace.jsonl"
        logger = WorkflowLogger(
            log_level=LogLevel.WARNING,
            log_file=str(log_file),
            trace_enabled=True,
            trace_log_file=str(trace_file),
            enable_console=False,
        )

        logger.info("Filtered info message")
        logger.error("Emitted error message")

        # Normal log should include only emitted messages based on level.
        content = Path(logger.log_file).read_text(encoding="utf-8")
        assert "Filtered info message" not in content
        assert "Emitted error message" in content

        # Trace log should include both calls with emitted flags.
        trace_lines = Path(logger.trace_log_file).read_text(encoding="utf-8").strip().split("\n")
        assert len(trace_lines) == 2

        first = json.loads(trace_lines[0])
        second = json.loads(trace_lines[1])
        assert first["message"] == "Filtered info message"
        assert first["emitted"] is False
        assert second["message"] == "Emitted error message"
        assert second["emitted"] is True

    def test_trace_event_writes_structured_record(self, tmp_path):
        """trace_event should write machine-readable event records."""
        trace_file = tmp_path / "trace.jsonl"
        logger = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=None,
            trace_enabled=True,
            trace_log_file=str(trace_file),
            enable_console=False,
        )

        logger.trace_event("integrated_agent_workflow.phase", {"phase": "phase_1", "status": "started"})

        trace_lines = Path(logger.trace_log_file).read_text(encoding="utf-8").strip().split("\n")
        assert len(trace_lines) == 1

        record = json.loads(trace_lines[0])
        assert record["type"] == "trace_event"
        assert record["event"] == "integrated_agent_workflow.phase"
        assert record["details"]["phase"] == "phase_1"
        assert record["details"]["status"] == "started"

    def test_context_stack(self, tmp_path):
        """Test context stack functionality."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=str(log_file),
            enable_console=False,
            log_format="json",
        )

        logger.push_context("Context1")
        logger.push_context("Context2")
        logger.info("Test with context")

        # Read first log entry
        with open(logger.log_file, "r", encoding="utf-8") as f:
            content = f.read()
        log_entry = json.loads(content.strip())
        assert log_entry["context"] == ["Context1", "Context2"]

        logger.pop_context()
        logger.info("Test after pop")

        # Re-read file to verify second entry
        with open(logger.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Check second line has correct context (only Context1 after pop)
        second_entry = json.loads(lines[1].strip())
        assert second_entry["context"] == ["Context1"]
        assert second_entry["message"] == "Test after pop"

    def test_set_log_level(self, tmp_path):
        """Test changing log level."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=str(log_file),
            enable_console=False,
        )

        logger.debug("Should not appear")
        assert not logger._should_log(LogLevel.DEBUG)

        logger.set_log_level(LogLevel.DEBUG)
        assert logger._should_log(LogLevel.DEBUG)

        logger.debug("Should appear")
        content = Path(logger.log_file).read_text(encoding="utf-8")
        assert "Should appear" in content
        assert "Should not appear" not in content

    def test_log_exception(self, tmp_path):
        """Test exception logging."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.DEBUG,
            log_file=str(log_file),
            enable_console=False,
        )

        try:
            raise ValueError("Test exception")
        except Exception as e:
            logger.log_exception(e, "Test context")

        content = Path(logger.log_file).read_text(encoding="utf-8")
        assert "ValueError" in content
        assert "Test exception" in content

    def test_create_diagnostic_report(self, tmp_path):
        """Test diagnostic report creation."""
        log_file = tmp_path / "test.log"
        report_file = tmp_path / "diagnostic.md"

        logger = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=str(log_file),
            enable_console=False,
        )

        logger.info("Test log entry")
        logger.push_context("Test context")

        report_path = logger.create_diagnostic_report(str(report_file))

        assert Path(report_path).exists()
        report_content = Path(report_path).read_text(encoding="utf-8")

        assert "# Diagnostic Report" in report_content
        assert "## Configuration" in report_content
        assert "Log Level: INFO" in report_content
        assert "## Current Context" in report_content
        assert "Test context" in report_content

    def test_banner(self, tmp_path, capsys):
        """Test banner method."""
        logger = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=None,
            enable_console=True,
        )

        logger.banner("Test Banner")
        captured = capsys.readouterr()

        assert "Test Banner" in captured.out
        assert "=" in captured.out


@pytest.mark.unit
class TestGlobalLogger:
    """Test global logger functions."""

    def test_get_logger(self, tmp_path, monkeypatch):
        """Test getting global logger instance."""
        # Reset global logger
        import workflow_logger

        workflow_logger._global_logger = None

        # Set environment to use tmp_path
        log_dir = str(tmp_path)
        monkeypatch.setenv("HA_AI_LOG_DIR", log_dir)

        logger = get_logger()
        assert isinstance(logger, WorkflowLogger)

        # Should return same instance
        logger2 = get_logger()
        assert logger is logger2

    def test_configure_logger(self, tmp_path):
        """Test configuring global logger."""
        log_file = tmp_path / "global.log"

        logger = configure_logger(
            log_level="DEBUG",
            log_file=str(log_file),
            enable_console=False,
        )

        assert isinstance(logger, WorkflowLogger)
        assert logger.log_level == LogLevel.DEBUG
        assert logger.log_file is not None
        assert logger.log_file.endswith("workflow.log")

        # Test invalid log level
        logger2 = configure_logger(log_level="INVALID")
        assert logger2.log_level == LogLevel.INFO  # Should default to INFO

    def test_environment_variables(self, tmp_path, monkeypatch):
        """Test logger configuration from environment variables."""
        # Reset global logger
        import workflow_logger

        workflow_logger._global_logger = None

        log_dir = str(tmp_path)
        monkeypatch.setenv("HA_AI_LOG_DIR", log_dir)
        monkeypatch.setenv("HA_AI_LOG_LEVEL", "WARNING")

        logger = get_logger()

        assert logger.log_level == LogLevel.WARNING
        assert logger.log_file is not None
        assert logger.log_file.endswith("workflow.log")

    def test_trace_environment_variables(self, tmp_path, monkeypatch):
        """Test trace logger configuration from environment variables."""
        import workflow_logger

        workflow_logger._global_logger = None

        log_dir = str(tmp_path)
        trace_path = os.path.join(log_dir, "workflow_trace.jsonl")
        monkeypatch.setenv("HA_AI_LOG_DIR", log_dir)
        monkeypatch.setenv("HA_AI_TRACE_LOG", "true")
        monkeypatch.setenv("HA_AI_TRACE_FILE", trace_path)

        logger = get_logger()

        assert logger.trace_enabled is True
        assert logger.trace_log_file is not None
        assert logger.trace_log_file.endswith("workflow_trace.log")


@pytest.mark.unit
class TestLoggerIntegration:
    """Integration tests for logger."""

    def test_multiple_loggers_same_file(self, tmp_path):
        """Test multiple loggers writing to same file."""
        log_file = tmp_path / "shared.log"

        logger1 = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=str(log_file),
            enable_console=False,
        )

        logger2 = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=str(log_file),
            enable_console=False,
        )

        logger1.info("From logger1")
        logger2.info("From logger2")

        content = Path(logger1.log_file).read_text(encoding="utf-8")
        assert "From logger1" in content
        assert "From logger2" in content

    def test_logger_with_no_file(self, capsys):
        """Test logger without file output."""
        logger = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=None,
            enable_console=True,
        )

        logger.info("Console only message")

        captured = capsys.readouterr()
        assert "Console only message" in captured.out

    def test_logger_file_permissions(self, tmp_path):
        """Test logger handles file permission errors gracefully."""
        # Create a directory that we'll make read-only
        log_dir = tmp_path / "readonly"
        log_dir.mkdir()
        log_file = log_dir / "test.log"

        logger = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=str(log_file),
            enable_console=False,
        )

        # This should work initially
        logger.info("Test message")
        assert Path(logger.log_file).exists()

        # Make directory read-only
        log_dir.chmod(0o444)

        # Try to write again - should handle error gracefully
        try:
            logger2 = WorkflowLogger(
                log_level=LogLevel.INFO,
                log_file=str(log_dir / "another.log"),
                enable_console=False,
            )
            logger2.info("Should fail gracefully")
        finally:
            # Restore permissions for cleanup
            log_dir.chmod(0o755)
