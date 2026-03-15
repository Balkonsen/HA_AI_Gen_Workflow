#!/usr/bin/env python3
"""
Tests for enhanced debug logging features in workflow_logger.py
"""

import sys
from pathlib import Path

import pytest

# Add bin directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "bin"))

from workflow_logger import WorkflowLogger, LogLevel, trace_calls  # noqa: E402


class TestEnhancedDebugMethods:
    """Test enhanced debug methods."""

    def test_debug_var(self, tmp_path):
        """Test debug_var method."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.DEBUG,
            log_file=str(log_file),
        )

        # Test with simple value
        logger.debug_var("test_var", "test_value")

        # Test with dict
        logger.debug_var("test_dict", {"key": "value"})

        # Test with list
        logger.debug_var("test_list", [1, 2, 3])

        # Verify log file
        log_content = log_file.read_text(encoding="utf-8")
        assert "Variable: test_var = 'test_value'" in log_content
        assert "Variable: test_dict" in log_content
        assert '"key": "value"' in log_content
        assert "Variable: test_list" in log_content

    def test_debug_call(self, tmp_path):
        """Test debug_call method."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.DEBUG,
            log_file=str(log_file),
        )

        # Test with args only
        logger.debug_call("test_func", args=(1, 2))

        # Test with kwargs only
        logger.debug_call("test_func2", kwargs={"key": "value"})

        # Test with both
        logger.debug_call("test_func3", args=(1,), kwargs={"key": "value"})

        log_content = log_file.read_text(encoding="utf-8")
        assert "Calling: test_func(1, 2)" in log_content
        assert "Calling: test_func2(key='value')" in log_content
        assert "Calling: test_func3(1, key='value')" in log_content

    def test_debug_return(self, tmp_path):
        """Test debug_return method."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.DEBUG,
            log_file=str(log_file),
        )

        logger.debug_return("test_func", 42)
        logger.debug_return("test_func2", {"result": "success"})

        log_content = log_file.read_text(encoding="utf-8")
        assert "Returned from test_func: 42" in log_content
        assert "Returned from test_func2" in log_content
        assert '"result": "success"' in log_content

    def test_debug_enter_exit(self, tmp_path):
        """Test debug_enter and debug_exit methods."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.DEBUG,
            log_file=str(log_file),
        )

        logger.debug_enter("test_func", args=(1, 2), kwargs={"key": "value"})
        logger.debug_exit("test_func", return_value=42)

        log_content = log_file.read_text(encoding="utf-8")
        assert "Entering: test_func(1, 2, key='value')" in log_content
        assert "Exiting: test_func -> 42" in log_content

    def test_debug_stack(self, tmp_path):
        """Test debug_stack method."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.DEBUG,
            log_file=str(log_file),
        )

        logger.debug_stack()

        log_content = log_file.read_text(encoding="utf-8")
        assert "Call stack:" in log_content

    def test_debug_methods_respect_log_level(self, tmp_path):
        """Test that debug methods respect log level."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=str(log_file),
        )

        # Log something at INFO level to create the file
        logger.info("Test message")

        # These should not be logged
        logger.debug_var("test_var", "test_value")
        logger.debug_call("test_func", args=(1, 2))

        log_content = log_file.read_text(encoding="utf-8")
        assert "Variable:" not in log_content
        assert "Calling:" not in log_content


class TestTraceCallsDecorator:
    """Test trace_calls decorator."""

    def test_trace_calls_basic(self, tmp_path):
        """Test basic trace_calls decorator functionality."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.DEBUG,
            log_file=str(log_file),
        )

        @trace_calls(logger)
        def test_function(a, b):
            return a + b

        result = test_function(1, 2)
        assert result == 3

        log_content = log_file.read_text(encoding="utf-8")
        assert "Entering:" in log_content
        assert "test_function" in log_content
        assert "Exiting:" in log_content
        assert "took" in log_content  # timing info

    def test_trace_calls_with_exception(self, tmp_path):
        """Test trace_calls decorator with exception."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.DEBUG,
            log_file=str(log_file),
        )

        @trace_calls(logger)
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        log_content = log_file.read_text(encoding="utf-8")
        assert "Entering:" in log_content
        assert "Exception in" in log_content
        assert "ValueError" in log_content

    def test_trace_calls_respects_log_level(self, tmp_path):
        """Test that trace_calls respects log level."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.INFO,
            log_file=str(log_file),
        )

        # Log something at INFO level to create the file
        logger.info("Test message")

        @trace_calls(logger)
        def test_function(a, b):
            return a + b

        result = test_function(1, 2)
        assert result == 3

        log_content = log_file.read_text(encoding="utf-8")
        # Should not have trace info at INFO level
        assert "â†’ Entering:" not in log_content
        assert "â† Exiting:" not in log_content


class TestEnhancedDebugIntegration:
    """Integration tests for enhanced debug features."""

    def test_nested_function_tracing(self, tmp_path):
        """Test tracing nested function calls."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.DEBUG,
            log_file=str(log_file),
        )

        @trace_calls(logger)
        def outer_function(x):
            return inner_function(x * 2)

        @trace_calls(logger)
        def inner_function(y):
            return y + 10

        result = outer_function(5)
        assert result == 20

        log_content = log_file.read_text(encoding="utf-8")
        assert "outer_function" in log_content
        assert "inner_function" in log_content

    def test_debug_var_with_complex_types(self, tmp_path):
        """Test debug_var with complex data types."""
        log_file = tmp_path / "test.log"
        logger = WorkflowLogger(
            log_level=LogLevel.DEBUG,
            log_file=str(log_file),
        )

        # Test with nested dict
        complex_data = {"level1": {"level2": {"items": [1, 2, 3]}}}
        logger.debug_var("complex_data", complex_data)

        log_content = log_file.read_text(encoding="utf-8")
        assert "complex_data" in log_content
        assert "level1" in log_content
        assert "level2" in log_content
        assert "items" in log_content
