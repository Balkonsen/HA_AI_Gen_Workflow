"""Unit tests for workflow_orchestrator.py command/result behavior."""

import os
import sys

# Add bin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

import workflow_orchestrator  # noqa: E402


class TestWorkflowMainValidateExitCode:
    """Ensure validate command exits correctly based on report success."""

    def test_validate_returns_nonzero_on_failed_report(self, monkeypatch):
        """Validate command should return 1 when report indicates failure."""

        class FailingOrchestrator:
            def __init__(self, *_args, **_kwargs):
                pass

            def validate_export(self, _source):
                return {"success": False}

        monkeypatch.setattr(
            workflow_orchestrator, "WorkflowOrchestrator", FailingOrchestrator
        )
        monkeypatch.setattr(
            sys,
            "argv",
            ["workflow_orchestrator.py", "validate", "--source", "dummy_path"],
        )

        assert workflow_orchestrator.main() == 1

    def test_validate_returns_zero_on_success_report(self, monkeypatch):
        """Validate command should return 0 when report indicates success."""

        class PassingOrchestrator:
            def __init__(self, *_args, **_kwargs):
                pass

            def validate_export(self, _source):
                return {"success": True}

        monkeypatch.setattr(
            workflow_orchestrator, "WorkflowOrchestrator", PassingOrchestrator
        )
        monkeypatch.setattr(
            sys,
            "argv",
            ["workflow_orchestrator.py", "validate", "--source", "dummy_path"],
        )

        assert workflow_orchestrator.main() == 0


class TestRunFullWorkflowValidationResult:
    """Ensure full workflow reflects validation result in return value."""

    def test_full_workflow_returns_false_when_validation_fails(self, monkeypatch):
        """Full workflow should fail when validation report has success=False."""
        orchestrator = workflow_orchestrator.WorkflowOrchestrator()

        monkeypatch.setattr(
            orchestrator, "export_local", lambda _source: "dummy_export"
        )
        monkeypatch.setattr(orchestrator, "sanitize_export", lambda _export: True)
        monkeypatch.setattr(
            orchestrator, "generate_ai_context", lambda _export: "dummy_context"
        )
        monkeypatch.setattr(
            orchestrator, "validate_export", lambda _export: {"success": False}
        )

        assert orchestrator.run_full_workflow("dummy_source", "local") is False

    def test_full_workflow_returns_true_when_validation_passes(self, monkeypatch):
        """Full workflow should succeed when validation report has success=True."""
        orchestrator = workflow_orchestrator.WorkflowOrchestrator()

        monkeypatch.setattr(
            orchestrator, "export_local", lambda _source: "dummy_export"
        )
        monkeypatch.setattr(orchestrator, "sanitize_export", lambda _export: True)
        monkeypatch.setattr(
            orchestrator, "generate_ai_context", lambda _export: "dummy_context"
        )
        monkeypatch.setattr(
            orchestrator, "validate_export", lambda _export: {"success": True}
        )

        assert orchestrator.run_full_workflow("dummy_source", "local") is True
