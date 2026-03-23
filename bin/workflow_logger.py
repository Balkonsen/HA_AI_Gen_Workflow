#!/usr/bin/env python3
"""
Centralized Logging Module for HA AI Gen Workflow
Provides structured logging with multiple levels and file output support.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Optional, Any, Callable
import json
import functools
import time
import tempfile
import inspect
import threading


class LogLevel(Enum):
    """Logging levels for the workflow."""

    DEBUG = 0  # Very detailed information for debugging
    VERBOSE = 1  # Detailed information about operations
    INFO = 2  # General informational messages (default)
    CONDENSED = 3  # Only important messages
    WARNING = 4  # Warning messages
    ERROR = 5  # Error messages
    CRITICAL = 6  # Critical errors


class WorkflowLogger:
    """
    Centralized logger for HA AI Gen Workflow.

    Supports:
    - Multiple log levels (debug, verbose, info, condensed, warning, error, critical)
    - File output with optional rotation
    - Console output with color coding
    - Structured logging for machine parsing
    - Context tracking for error diagnostics
    """

    # ANSI color codes
    COLORS = {
        "RED": "\033[0;31m",
        "GREEN": "\033[0;32m",
        "YELLOW": "\033[1;33m",
        "BLUE": "\033[0;34m",
        "MAGENTA": "\033[0;35m",
        "CYAN": "\033[0;36m",
        "WHITE": "\033[1;37m",
        "NC": "\033[0m",  # No Color
    }

    # Icons for different message types
    ICONS = {
        "debug": "🔍",
        "verbose": "→",
        "info": "ℹ",
        "condensed": "•",
        "warning": "⚠",
        "error": "✗",
        "critical": "❌",
        "success": "✓",
        "progress": "⏳",
    }

    def __init__(
        self,
        log_level: LogLevel = LogLevel.INFO,
        log_file: Optional[str] = None,
        trace_log_file: Optional[str] = None,
        trace_enabled: bool = False,
        enable_console: bool = True,
        enable_colors: bool = True,
        log_format: str = "text",  # 'text' or 'json'
    ):
        """
        Initialize the workflow logger.

        Args:
            log_level: Minimum log level to output
            log_file: Path to log file (None disables file logging)
            trace_log_file: Path to structured trace log (jsonl)
            trace_enabled: Whether to write detailed trace records
            enable_console: Whether to output to console
            enable_colors: Whether to use colored output in console
            log_format: Output format ('text' or 'json')
        """
        self.log_level = log_level
        self.log_file = log_file
        self.trace_enabled = trace_enabled
        self.trace_log_file = trace_log_file
        self.enable_console = enable_console
        self.enable_colors = enable_colors and sys.stdout.isatty()
        self.log_format = log_format
        self.context_stack = []
        self._sequence = 0

        # Ensure log directory exists if log file is specified
        if self.log_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

        # Ensure trace log directory exists if trace logging is enabled
        if self.trace_enabled and self.trace_log_file:
            Path(self.trace_log_file).parent.mkdir(parents=True, exist_ok=True)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if a message at the given level should be logged."""
        return level.value >= self.log_level.value

    def _format_message(self, level: LogLevel, message: str, icon: Optional[str] = None) -> str:
        """Format a log message for console output."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.log_format == "json":
            log_entry = {
                "timestamp": timestamp,
                "level": level.name,
                "message": message,
                "context": self.context_stack.copy() if self.context_stack else [],
            }
            return json.dumps(log_entry)

        # Text format
        if icon is None:
            icon = self.ICONS.get(level.name.lower(), "•")

        if self.enable_colors:
            color_map = {
                LogLevel.DEBUG: self.COLORS["CYAN"],
                LogLevel.VERBOSE: self.COLORS["WHITE"],
                LogLevel.INFO: self.COLORS["BLUE"],
                LogLevel.CONDENSED: self.COLORS["WHITE"],
                LogLevel.WARNING: self.COLORS["YELLOW"],
                LogLevel.ERROR: self.COLORS["RED"],
                LogLevel.CRITICAL: self.COLORS["RED"],
            }
            color = color_map.get(level, self.COLORS["WHITE"])
            reset = self.COLORS["NC"]
            return f"{timestamp} [{level.name:9}] {color}{icon}{reset} {message}"
        else:
            return f"{timestamp} [{level.name:9}] {icon} {message}"

    def _write_to_file(self, formatted_message: str):
        """Write a log message to file."""
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(formatted_message + "\n")
            except Exception as e:
                print(f"Failed to write to log file {self.log_file}: {e}", file=sys.stderr)

    def _next_sequence(self) -> int:
        """Return the next monotonic sequence number for trace records."""
        self._sequence += 1
        return self._sequence

    def _build_trace_record(
        self,
        level: LogLevel,
        message: str,
        icon: Optional[str],
        emitted: bool,
    ) -> dict[str, Any]:
        """Build a structured trace record for deep troubleshooting."""
        caller = None
        try:
            # Frame index 0 is this helper, 1 is _trace_log_call, 2 is _log caller.
            frame_info = inspect.stack()[3]
            caller = {
                "file": frame_info.filename,
                "function": frame_info.function,
                "line": frame_info.lineno,
            }
        except Exception:
            caller = None

        return {
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "sequence": self._next_sequence(),
            "thread": threading.current_thread().name,
            "pid": os.getpid(),
            "level": level.name,
            "icon": icon,
            "message": message,
            "emitted": emitted,
            "log_level": self.log_level.name,
            "context": self.context_stack.copy() if self.context_stack else [],
            "caller": caller,
        }

    def _write_trace_record(self, record: dict[str, Any]):
        """Write a single structured record to the trace log file."""
        if not (self.trace_enabled and self.trace_log_file):
            return

        try:
            with open(self.trace_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
        except Exception as e:
            print(f"Failed to write to trace log file {self.trace_log_file}: {e}", file=sys.stderr)

    def _trace_log_call(self, level: LogLevel, message: str, icon: Optional[str], emitted: bool):
        """Capture every log invocation for full-fidelity trace diagnostics."""
        if not self.trace_enabled:
            return

        record = self._build_trace_record(
            level=level,
            message=message,
            icon=icon,
            emitted=emitted,
        )
        self._write_trace_record(record)

    def _log(self, level: LogLevel, message: str, icon: Optional[str] = None):
        """Internal logging method."""
        should_emit = self._should_log(level)
        self._trace_log_call(level=level, message=message, icon=icon, emitted=should_emit)

        if not should_emit:
            return

        formatted = self._format_message(level, message, icon)

        if self.enable_console:
            print(formatted)

        if self.log_file:
            self._write_to_file(formatted)

    # Public logging methods
    def debug(self, message: str):
        """Log a debug message."""
        self._log(LogLevel.DEBUG, message)

    def verbose(self, message: str):
        """Log a verbose message."""
        self._log(LogLevel.VERBOSE, message)

    def info(self, message: str):
        """Log an informational message."""
        self._log(LogLevel.INFO, message)

    def condensed(self, message: str):
        """Log a condensed message (only important info)."""
        self._log(LogLevel.CONDENSED, message)

    def warning(self, message: str):
        """Log a warning message."""
        self._log(LogLevel.WARNING, message)

    def error(self, message: str):
        """Log an error message."""
        self._log(LogLevel.ERROR, message)

    def critical(self, message: str):
        """Log a critical error message."""
        self._log(LogLevel.CRITICAL, message)

    def success(self, message: str):
        """Log a success message."""
        self._log(LogLevel.INFO, message, icon=self.ICONS["success"])

    def progress(self, message: str):
        """Log a progress message."""
        self._log(LogLevel.INFO, message, icon=self.ICONS["progress"])

    def banner(self, message: str):
        """Print a banner message."""
        if self.enable_console:
            separator = "=" * 67
            print()
            print(separator)
            print(f"  {message}")
            print(separator)
            print()

        if self.log_file:
            self._write_to_file("")
            self._write_to_file("=" * 67)
            self._write_to_file(f"  {message}")
            self._write_to_file("=" * 67)
            self._write_to_file("")

    def push_context(self, context: str):
        """Push a context onto the stack for better error tracking."""
        self.context_stack.append(context)

    def pop_context(self):
        """Pop a context from the stack."""
        if self.context_stack:
            self.context_stack.pop()

    def set_log_level(self, level: LogLevel):
        """Change the current log level."""
        self.log_level = level
        self.verbose(f"Log level changed to {level.name}")

    def set_log_file(self, log_file: str):
        """Change the log file path."""
        self.log_file = log_file
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    def log_exception(self, exception: Exception, context: Optional[str] = None):
        """Log an exception with context information."""
        import traceback

        if context:
            self.push_context(context)

        self.error(f"Exception occurred: {type(exception).__name__}: {str(exception)}")

        if self.log_level.value <= LogLevel.DEBUG.value:
            # Include full traceback in debug mode
            tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
            for line in tb_lines:
                self._write_to_file(line.rstrip())

        if context:
            self.pop_context()

    def create_diagnostic_report(self, output_path: str, include_context: bool = True) -> str:
        """
        Create a diagnostic report for troubleshooting.

        Args:
            output_path: Path to save the diagnostic report
            include_context: Include context stack in the report

        Returns:
            Path to the created report
        """
        report_lines = [
            "# Diagnostic Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Configuration",
            f"- Log Level: {self.log_level.name}",
            f"- Log File: {self.log_file or 'None'}",
            f"- Console Output: {self.enable_console}",
            f"- Colors Enabled: {self.enable_colors}",
            f"- Format: {self.log_format}",
            "",
        ]

        if include_context and self.context_stack:
            report_lines.extend(
                [
                    "## Current Context",
                    "",
                ]
            )
            for i, ctx in enumerate(self.context_stack, 1):
                report_lines.append(f"{i}. {ctx}")
            report_lines.append("")

        # Include last lines from log file if it exists
        if self.log_file and Path(self.log_file).exists():
            report_lines.extend(
                [
                    "## Recent Log Entries (Last 50 lines)",
                    "",
                    "```",
                ]
            )
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    last_lines = lines[-50:] if len(lines) > 50 else lines
                    report_lines.extend([line.rstrip() for line in last_lines])
            except Exception as e:
                report_lines.append(f"Error reading log file: {e}")

            report_lines.append("```")
            report_lines.append("")

        # Write report
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(report_lines))
            self.success(f"Diagnostic report created: {output_path}")
            return output_path
        except Exception as e:
            self.error(f"Failed to create diagnostic report: {e}")
            raise

    # -------------------------------------------------------------------------
    # Enhanced Debug Methods
    # -------------------------------------------------------------------------

    def debug_var(self, var_name: str, var_value: Any):
        """Log a variable name and value at DEBUG level.

        Args:
            var_name: Name of the variable
            var_value: Value of the variable
        """
        if self.log_level.value <= LogLevel.DEBUG.value:
            # Format value based on type
            if isinstance(var_value, (dict, list)):
                try:
                    formatted_value = json.dumps(var_value, indent=2, default=str)
                except Exception:
                    formatted_value = str(var_value)
            else:
                formatted_value = repr(var_value)

            self.debug(f"Variable: {var_name} = {formatted_value}")

    def debug_call(
        self,
        func_name: str,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ):
        """Log a function call with its arguments at DEBUG level.

        Args:
            func_name: Name of the function being called
            args: Positional arguments
            kwargs: Keyword arguments
        """
        if self.log_level.value <= LogLevel.DEBUG.value:
            args_str = ", ".join(repr(a) for a in args)
            kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in (kwargs or {}).items())
            all_args = ", ".join(filter(None, [args_str, kwargs_str]))
            self.debug(f"Calling: {func_name}({all_args})")

    def debug_return(self, func_name: str, return_value: Any):
        """Log a function return value at DEBUG level.

        Args:
            func_name: Name of the function returning
            return_value: The return value
        """
        if self.log_level.value <= LogLevel.DEBUG.value:
            if isinstance(return_value, (dict, list)):
                try:
                    formatted_value = json.dumps(return_value, indent=2, default=str)
                except Exception:
                    formatted_value = str(return_value)
            else:
                formatted_value = repr(return_value)

            self.debug(f"Returned from {func_name}: {formatted_value}")

    def debug_enter(
        self,
        func_name: str,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ):
        """Log entering a function at DEBUG level.

        Args:
            func_name: Name of the function
            args: Positional arguments
            kwargs: Keyword arguments
        """
        if self.log_level.value <= LogLevel.DEBUG.value:
            args_str = ", ".join(repr(a) for a in args)
            kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in (kwargs or {}).items())
            all_args = ", ".join(filter(None, [args_str, kwargs_str]))
            self.debug(f"→ Entering: {func_name}({all_args})")
            self.push_context(func_name)

    def debug_exit(self, func_name: str, return_value: Any = None):
        """Log exiting a function at DEBUG level.

        Args:
            func_name: Name of the function
            return_value: Optional return value to log
        """
        if self.log_level.value <= LogLevel.DEBUG.value:
            if return_value is not None:
                self.debug(f"← Exiting: {func_name} -> {repr(return_value)}")
            else:
                self.debug(f"← Exiting: {func_name}")
            self.pop_context()

    def debug_stack(self):
        """Log the current call stack at DEBUG level."""
        if self.log_level.value <= LogLevel.DEBUG.value:
            import traceback

            stack = traceback.format_stack()[:-1]  # Exclude this function
            self.debug("Call stack:")
            for line in stack:
                self._write_to_file(f"  {line.rstrip()}")

    def trace_event(self, event: str, details: Optional[dict[str, Any]] = None):
        """Write a dedicated structured trace event record.

        This bypasses log-level filtering so workflow phases and skill usage can be
        correlated in a single machine-readable trace stream.
        """
        if not self.trace_enabled:
            return

        record: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "sequence": self._next_sequence(),
            "thread": threading.current_thread().name,
            "pid": os.getpid(),
            "type": "trace_event",
            "event": event,
            "context": self.context_stack.copy() if self.context_stack else [],
            "details": details or {},
        }
        self._write_trace_record(record)


def trace_calls(logger: Optional[WorkflowLogger] = None):
    """Decorator to trace function calls, arguments, and return values at DEBUG level.

    Usage:
        @trace_calls()
        def my_function(arg1, arg2):
            return result

    Args:
        logger: Optional logger instance. If None, uses global logger.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger()

            # Only trace if debug level is enabled
            if _logger.log_level.value > LogLevel.DEBUG.value:
                return func(*args, **kwargs)

            func_name = f"{func.__module__}.{func.__qualname__}"

            # Log function entry
            _logger.debug_enter(func_name, args, kwargs)

            try:
                # Execute function with timing
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Log function exit with timing
                _logger.debug(f"← Exiting: {func_name} (took {elapsed:.3f}s)")
                _logger.debug_return(func_name, result)
                _logger.pop_context()

                return result
            except Exception as e:
                # Log exception
                _logger.debug(f"✗ Exception in {func_name}: {type(e).__name__}: {e}")
                _logger.pop_context()
                raise

        return wrapper

    return decorator


# Global logger instance (can be configured by importing scripts)
_global_logger: Optional[WorkflowLogger] = None


def _parse_bool_env(value: Optional[str], default: bool = False) -> bool:
    """Parse boolean-like environment values safely."""
    if value is None:
        return default

    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on", "enabled"}


def get_logger() -> WorkflowLogger:
    """Get or create the global logger instance."""
    global _global_logger
    if _global_logger is None:
        # Default configuration - use environment variable, or fall back to
        # ./exports (resolved to absolute path) instead of a hardcoded
        # container-only path like /config/ai_exports
        default_log_dir = os.path.abspath("./exports")
        log_dir = os.environ.get("HA_AI_LOG_DIR", default_log_dir)
        log_file = os.path.join(log_dir, "workflow.log")
        trace_log_file = os.environ.get("HA_AI_TRACE_FILE", os.path.join(log_dir, "workflow_trace.log"))
        log_level_str = os.environ.get("HA_AI_LOG_LEVEL", "INFO")
        trace_enabled = _parse_bool_env(os.environ.get("HA_AI_TRACE_LOG"), default=False)

        try:
            log_level = LogLevel[log_level_str.upper()]
        except KeyError:
            log_level = LogLevel.INFO

        _global_logger = WorkflowLogger(
            log_level=log_level,
            log_file=log_file,
            trace_enabled=trace_enabled,
            trace_log_file=trace_log_file,
        )

    return _global_logger


def configure_logger(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    trace_enabled: Optional[bool] = None,
    trace_log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_colors: bool = True,
    log_format: str = "text",
) -> WorkflowLogger:
    """
    Configure the global logger instance.

    Args:
        log_level: Log level as string (DEBUG, VERBOSE, INFO, CONDENSED, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        trace_enabled: Enable detailed structured trace logging
        trace_log_file: Path to structured trace log file (jsonl)
        enable_console: Enable console output
        enable_colors: Enable colored console output
        log_format: Log format ('text' or 'json')

    Returns:
        Configured logger instance
    """
    global _global_logger

    level = LogLevel.INFO
    if log_level:
        try:
            level = LogLevel[log_level.upper()]
        except KeyError:
            print(f"Warning: Invalid log level '{log_level}', using INFO", file=sys.stderr)

    resolved_trace_enabled = trace_enabled
    if resolved_trace_enabled is None:
        resolved_trace_enabled = _parse_bool_env(os.environ.get("HA_AI_TRACE_LOG"), default=False)

    resolved_trace_log_file = trace_log_file
    if resolved_trace_log_file is None:
        if log_file:
            resolved_trace_log_file = str(Path(log_file).with_name("workflow_trace.log"))
        else:
            default_log_dir = os.environ.get("HA_AI_LOG_DIR", os.path.abspath("./exports"))
            default_trace_file = os.path.join(default_log_dir, "workflow_trace.log")
            resolved_trace_log_file = os.environ.get("HA_AI_TRACE_FILE", default_trace_file)

    _global_logger = WorkflowLogger(
        log_level=level,
        log_file=log_file,
        trace_enabled=resolved_trace_enabled,
        trace_log_file=resolved_trace_log_file,
        enable_console=enable_console,
        enable_colors=enable_colors,
        log_format=log_format,
    )

    return _global_logger


if __name__ == "__main__":
    # Test the logger
    logger = configure_logger(
        log_level="DEBUG",
        log_file=os.path.join(tempfile.gettempdir(), "workflow_test.log"),
    )

    logger.banner("Testing Workflow Logger")
    logger.debug("This is a debug message")
    logger.verbose("This is a verbose message")
    logger.info("This is an info message")
    logger.condensed("This is a condensed message")
    logger.success("This is a success message")
    logger.progress("This is a progress message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    logger.push_context("Test context 1")
    logger.push_context("Test context 2")
    logger.info("Message with context")

    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.log_exception(e, "Exception test")

    logger.create_diagnostic_report("/tmp/diagnostic_test.md")  # nosec B108

    print("\nLog file created at: /tmp/workflow_test.log")
    print("Diagnostic report created at: /tmp/diagnostic_test.md")
