#!/usr/bin/env python3
"""
Lessons Learned Engine for HA AI Gen Workflow

Implements an iterative, automated self-learning improvement loop that:
1. Analyzes completed PRs and coding sessions for patterns and issues
2. Captures structured lessons learned
3. Challenges lessons against current repository configuration
4. Applies feasible improvements automatically

This module is designed to run as a fixed routine step after each PR merge.
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

# Add bin directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow_logger import get_logger  # noqa: E402

# Lessons learned storage file
LESSONS_FILE = "lessons_learned.json"

# Categories for lessons
LESSON_CATEGORIES = [
    "build_failure",
    "test_failure",
    "lint_issue",
    "security_issue",
    "configuration_drift",
    "documentation_gap",
    "dependency_issue",
    "architecture_pattern",
]

# Files that can be automatically improved
IMPROVABLE_TARGETS = {
    "copilot_instructions": ".github/copilot-instructions.md",
    "agent_instructions": "docs/AGENT_INSTRUCTIONS.md",
    "developer_guide": "docs/DEVELOPER_GUIDE.md",
    "makefile": "Makefile",
    "ci_workflow": ".github/workflows/ci-cd.yml",
}


class LessonEntry:
    """Represents a single lesson learned from a PR or coding session."""

    def __init__(
        self,
        category: str,
        summary: str,
        details: str,
        source_pr: Optional[str] = None,
        source_files: Optional[List[str]] = None,
        recommendation: Optional[str] = None,
        auto_fixable: bool = False,
        fix_target: Optional[str] = None,
        fix_content: Optional[str] = None,
    ):
        """Initialize a lesson entry.

        Args:
            category: Lesson category from LESSON_CATEGORIES
            summary: Short summary of the lesson
            details: Detailed description of what was learned
            source_pr: PR number or identifier that triggered this lesson
            source_files: List of files involved
            recommendation: Suggested improvement
            auto_fixable: Whether this can be auto-fixed
            fix_target: Target file key from IMPROVABLE_TARGETS
            fix_content: Content to add/update for auto-fix
        """
        if category not in LESSON_CATEGORIES:
            raise ValueError(f"Invalid category '{category}'. Must be one of: {LESSON_CATEGORIES}")

        self.category = category
        self.summary = summary
        self.details = details
        self.source_pr = source_pr
        self.source_files = source_files or []
        self.recommendation = recommendation
        self.auto_fixable = auto_fixable
        self.fix_target = fix_target
        self.fix_content = fix_content
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.applied = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "category": self.category,
            "summary": self.summary,
            "details": self.details,
            "source_pr": self.source_pr,
            "source_files": self.source_files,
            "recommendation": self.recommendation,
            "auto_fixable": self.auto_fixable,
            "fix_target": self.fix_target,
            "fix_content": self.fix_content,
            "timestamp": self.timestamp,
            "applied": self.applied,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LessonEntry":
        """Deserialize from dictionary."""
        entry = cls(
            category=data["category"],
            summary=data["summary"],
            details=data["details"],
            source_pr=data.get("source_pr"),
            source_files=data.get("source_files", []),
            recommendation=data.get("recommendation"),
            auto_fixable=data.get("auto_fixable", False),
            fix_target=data.get("fix_target"),
            fix_content=data.get("fix_content"),
        )
        entry.timestamp = data.get("timestamp", entry.timestamp)
        entry.applied = data.get("applied", False)
        return entry


class LessonsStore:
    """Manages persistence of lessons learned."""

    def __init__(self, store_path: Optional[str] = None):
        """Initialize the lessons store.

        Args:
            store_path: Path to the lessons JSON file.
                        Defaults to LESSONS_FILE in the repo root.
        """
        if store_path:
            self.store_path = Path(os.path.abspath(store_path))
        else:
            repo_root = Path(__file__).resolve().parent.parent
            self.store_path = repo_root / LESSONS_FILE

        self.lessons: List[LessonEntry] = []
        self._load()

    def _load(self) -> None:
        """Load lessons from the JSON file."""
        if self.store_path.exists():
            with open(self.store_path, "r") as f:
                data = json.load(f)
            self.lessons = [LessonEntry.from_dict(entry) for entry in data.get("lessons", [])]
        else:
            self.lessons = []

    def save(self) -> None:
        """Save lessons to the JSON file."""
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_lessons": len(self.lessons),
            "lessons": [lesson.to_dict() for lesson in self.lessons],
        }
        with open(self.store_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_lesson(self, lesson: LessonEntry) -> None:
        """Add a lesson, avoiding duplicates based on summary."""
        for existing in self.lessons:
            if existing.summary == lesson.summary and existing.category == lesson.category:
                return  # Skip duplicate
        self.lessons.append(lesson)

    def get_unapplied(self) -> List[LessonEntry]:
        """Get lessons that haven't been applied yet."""
        return [lesson for lesson in self.lessons if not lesson.applied and lesson.auto_fixable]

    def get_by_category(self, category: str) -> List[LessonEntry]:
        """Get lessons filtered by category."""
        return [lesson for lesson in self.lessons if lesson.category == category]

    def mark_applied(self, lesson: LessonEntry) -> None:
        """Mark a lesson as applied."""
        lesson.applied = True

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all lessons."""
        summary: Dict[str, int] = {}
        for cat in LESSON_CATEGORIES:
            count = len(self.get_by_category(cat))
            if count > 0:
                summary[cat] = count

        return {
            "total": len(self.lessons),
            "applied": len([entry for entry in self.lessons if entry.applied]),
            "pending": len([entry for entry in self.lessons if not entry.applied]),
            "auto_fixable": len([entry for entry in self.lessons if entry.auto_fixable and not entry.applied]),
            "by_category": summary,
        }


class PRAnalyzer:
    """Analyzes PR changes and results to extract lessons learned."""

    # Patterns that indicate common issues
    ISSUE_PATTERNS = {
        "docker_context": {
            "pattern": r"COPY\s+(?:ha_ai_workflow_addon/|\.\./).*",
            "category": "build_failure",
            "summary": "Dockerfile COPY uses repo-root paths instead of addon-relative paths",
            "recommendation": "All Dockerfile COPY paths must be relative to ha_ai_workflow_addon/ build context",
        },
        "bashio_usage": {
            "pattern": r"bashio::|with-contenv\s+bashio",
            "category": "build_failure",
            "summary": "Shell script uses bashio/s6 functions instead of pure bash",
            "recommendation": "Use pure bash with jq for config reading, no bashio:: or s6-overlay",
        },
        "armv7_reference": {
            "pattern": r"\barmv7\b",
            "category": "architecture_pattern",
            "summary": "Reference to unsupported armv7 architecture detected",
            "recommendation": "Only amd64 and aarch64 are supported; remove armv7 references",
        },
        "bare_except": {
            "pattern": r"except\s*:",
            "category": "lint_issue",
            "summary": "Bare except clause found - catches all exceptions including SystemExit",
            "recommendation": "Use specific exception types instead of bare except",
        },
        "hardcoded_config_path": {
            "pattern": r'["\']/config/ai_exports["\']',
            "category": "configuration_drift",
            "summary": "Hardcoded container path /config/ai_exports found",
            "recommendation": "Use config-driven paths with os.path.abspath() fallback",
        },
        "missing_type_hints": {
            "pattern": r"def\s+\w+\([^)]*\)\s*:",
            "category": "lint_issue",
            "summary": "Function missing return type hint",
            "recommendation": "Add return type hints to function signatures",
        },
        "print_instead_of_logger": {
            "pattern": r"\bprint\s*\(",
            "category": "lint_issue",
            "summary": "Using print() instead of workflow logger",
            "recommendation": "Use workflow_logger.get_logger() for structured logging",
        },
        "secret_in_log": {
            "pattern": r"(?:log|print|debug|info|warning|error).*(?:password|token|secret|api_key)",
            "category": "security_issue",
            "summary": "Potential secret exposure in log/print statement",
            "recommendation": "Never log sensitive values; use sanitized placeholders",
        },
    }

    def __init__(self, repo_root: Optional[str] = None):
        """Initialize the PR analyzer.

        Args:
            repo_root: Path to the repository root.
        """
        if repo_root:
            self.repo_root = Path(os.path.abspath(repo_root))
        else:
            self.repo_root = Path(__file__).resolve().parent.parent

    def analyze_diff(self, diff_content: str, pr_number: Optional[str] = None) -> List[LessonEntry]:
        """Analyze a PR diff for patterns that indicate lessons learned.

        Args:
            diff_content: The unified diff content to analyze.
            pr_number: Optional PR number for tracking.

        Returns:
            List of lesson entries extracted from the diff.
        """
        lessons: List[LessonEntry] = []
        added_lines = self._extract_added_lines(diff_content)
        changed_files = self._extract_changed_files(diff_content)

        for name, pattern_info in self.ISSUE_PATTERNS.items():
            for line_num, line in added_lines:
                if re.search(pattern_info["pattern"], line):
                    lesson = LessonEntry(
                        category=pattern_info["category"],
                        summary=pattern_info["summary"],
                        details=f"Pattern '{name}' detected in added line: {line.strip()[:100]}",
                        source_pr=pr_number,
                        source_files=changed_files,
                        recommendation=pattern_info["recommendation"],
                    )
                    lessons.append(lesson)
                    break  # One lesson per pattern per diff

        return lessons

    def analyze_test_results(self, test_output: str, pr_number: Optional[str] = None) -> List[LessonEntry]:
        """Analyze test output to extract lessons from failures.

        Args:
            test_output: The pytest output text.
            pr_number: Optional PR number for tracking.

        Returns:
            List of lesson entries from test failures.
        """
        lessons: List[LessonEntry] = []

        # Extract failed test info
        failed_pattern = r"FAILED\s+([\w/]+\.py::[\w:]+)"
        failed_tests = re.findall(failed_pattern, test_output)

        if failed_tests:
            # Extract error types
            error_types = re.findall(r"(\w+Error|\w+Exception)", test_output)
            unique_errors = list(set(error_types))

            lesson = LessonEntry(
                category="test_failure",
                summary=f"Test failures detected: {len(failed_tests)} test(s) failed",
                details=(
                    f"Failed tests: {', '.join(failed_tests[:5])}\n" f"Error types: {', '.join(unique_errors[:5])}"
                ),
                source_pr=pr_number,
                source_files=[t.split("::")[0] for t in failed_tests],
                recommendation="Review and fix failing tests before merging",
            )
            lessons.append(lesson)

        # Check for deprecation warnings
        deprecation_pattern = r"(DeprecationWarning|PendingDeprecationWarning):\s*(.+)"
        deprecations = re.findall(deprecation_pattern, test_output)
        if deprecations:
            unique_deps = list(set(msg for _, msg in deprecations))
            lesson = LessonEntry(
                category="dependency_issue",
                summary=f"Deprecation warnings detected: {len(unique_deps)} unique warning(s)",
                details=f"Warnings: {'; '.join(unique_deps[:3])}",
                source_pr=pr_number,
                recommendation="Update deprecated API usage before they become errors",
            )
            lessons.append(lesson)

        return lessons

    def analyze_lint_results(self, lint_output: str, pr_number: Optional[str] = None) -> List[LessonEntry]:
        """Analyze linter output to extract lessons from violations.

        Args:
            lint_output: The linter output text (flake8, pylint, black, etc).
            pr_number: Optional PR number for tracking.

        Returns:
            List of lesson entries from lint violations.
        """
        lessons: List[LessonEntry] = []

        # Count flake8 violations by code
        flake8_pattern = r"(\w+\d+)\s"
        violations = re.findall(flake8_pattern, lint_output)
        if violations:
            violation_counts: Dict[str, int] = {}
            for code in violations:
                if re.match(r"[A-Z]\d{3,4}", code):
                    violation_counts[code] = violation_counts.get(code, 0) + 1

            if violation_counts:
                top_violations = sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                lesson = LessonEntry(
                    category="lint_issue",
                    summary=f"Lint violations detected: {sum(violation_counts.values())} total",
                    details=f"Top violations: {', '.join(f'{code}({count})' for code, count in top_violations)}",
                    source_pr=pr_number,
                    recommendation="Run 'make format' to auto-fix formatting, then address remaining issues",
                )
                lessons.append(lesson)

        # Check for black formatting issues
        if "would reformat" in lint_output.lower():
            files_to_reformat = re.findall(r"would reformat\s+(.+)", lint_output, re.IGNORECASE)
            lesson = LessonEntry(
                category="lint_issue",
                summary="Code formatting issues detected (black)",
                details=f"Files needing reformat: {', '.join(files_to_reformat[:5])}",
                source_pr=pr_number,
                source_files=files_to_reformat[:5],
                recommendation="Run 'make format' before committing to auto-fix formatting",
            )
            lessons.append(lesson)

        return lessons

    def scan_repository(self) -> List[LessonEntry]:
        """Scan the repository for known anti-patterns.

        Returns:
            List of lesson entries from repository-wide scan.
        """
        lessons: List[LessonEntry] = []

        for name, pattern_info in self.ISSUE_PATTERNS.items():
            pattern = pattern_info["pattern"]
            category = pattern_info["category"]

            # Skip patterns that are too broad for repo-wide scanning
            if name in ("missing_type_hints", "print_instead_of_logger"):
                continue

            for py_file in self.repo_root.glob("bin/*.py"):
                try:
                    content = py_file.read_text()
                    if re.search(pattern, content):
                        lesson = LessonEntry(
                            category=category,
                            summary=pattern_info["summary"],
                            details=f"Pattern '{name}' found in {py_file.name}",
                            source_files=[str(py_file.relative_to(self.repo_root))],
                            recommendation=pattern_info["recommendation"],
                        )
                        lessons.append(lesson)
                except OSError:
                    continue

        return lessons

    @staticmethod
    def _extract_added_lines(diff_content: str) -> List[Tuple[int, str]]:
        """Extract added lines (starting with +) from a unified diff.

        Args:
            diff_content: Unified diff content.

        Returns:
            List of (line_number, line_content) tuples.
        """
        added: List[Tuple[int, str]] = []
        line_num = 0
        for line in diff_content.split("\n"):
            if line.startswith("@@"):
                match = re.search(r"\+(\d+)", line)
                if match:
                    line_num = int(match.group(1))
            elif line.startswith("+") and not line.startswith("+++"):
                added.append((line_num, line[1:]))  # Remove the leading +
                line_num += 1
            elif not line.startswith("-"):
                line_num += 1
        return added

    @staticmethod
    def _extract_changed_files(diff_content: str) -> List[str]:
        """Extract file paths from a unified diff.

        Args:
            diff_content: Unified diff content.

        Returns:
            List of changed file paths.
        """
        files = re.findall(r"^\+\+\+ b/(.+)$", diff_content, re.MULTILINE)
        return files


class ImprovementApplicator:
    """Applies feasible improvements to the repository based on lessons learned."""

    def __init__(self, repo_root: Optional[str] = None):
        """Initialize the improvement applicator.

        Args:
            repo_root: Path to the repository root.
        """
        if repo_root:
            self.repo_root = Path(os.path.abspath(repo_root))
        else:
            self.repo_root = Path(__file__).resolve().parent.parent
        self.logger = get_logger()

    def apply_improvements(self, store: LessonsStore) -> Dict[str, Any]:
        """Apply all feasible pending improvements.

        Args:
            store: The lessons store with pending improvements.

        Returns:
            Summary of applied improvements.
        """
        results = {"applied": [], "skipped": [], "failed": []}

        for lesson in store.get_unapplied():
            if not lesson.fix_target or not lesson.fix_content:
                results["skipped"].append({"summary": lesson.summary, "reason": "No fix target or content specified"})
                continue

            target_key = lesson.fix_target
            if target_key not in IMPROVABLE_TARGETS:
                results["skipped"].append({"summary": lesson.summary, "reason": f"Unknown fix target: {target_key}"})
                continue

            target_path = self.repo_root / IMPROVABLE_TARGETS[target_key]
            success = self._apply_fix(target_path, lesson)

            if success:
                store.mark_applied(lesson)
                results["applied"].append({"summary": lesson.summary, "target": str(target_path)})
            else:
                results["failed"].append({"summary": lesson.summary, "target": str(target_path)})

        store.save()
        return results

    def _apply_fix(self, target_path: Path, lesson: LessonEntry) -> bool:
        """Apply a single fix to a target file.

        Args:
            target_path: Path to the file to modify.
            lesson: The lesson entry with fix details.

        Returns:
            True if the fix was applied successfully.
        """
        if not target_path.exists():
            return False

        content = target_path.read_text()

        # Check if the fix content is already present (idempotent)
        if lesson.fix_content and lesson.fix_content.strip() in content:
            store_ref = lesson  # Mark as applied since content already exists
            store_ref.applied = True
            return True

        # Append lesson as a documented pitfall
        if lesson.fix_content:
            updated_content = content.rstrip() + "\n\n" + lesson.fix_content.strip() + "\n"
            target_path.write_text(updated_content)
            return True

        return False

    def validate_repository(self, store: LessonsStore) -> List[LessonEntry]:
        """Validate current repository against known lessons.

        Cross-references the repository state with lessons learned
        to detect recurring issues or regressions.

        Args:
            store: The lessons store with all lessons.

        Returns:
            List of new lessons from validation findings.
        """
        analyzer = PRAnalyzer(str(self.repo_root))
        new_lessons = analyzer.scan_repository()

        # Filter out lessons that are already known
        existing_summaries = {entry.summary for entry in store.lessons}
        novel_lessons = [entry for entry in new_lessons if entry.summary not in existing_summaries]

        return novel_lessons


class LessonsLearnedEngine:
    """Main engine that orchestrates the self-learning improvement loop.

    This is the primary entry point for the lessons learned system.
    It coordinates analysis, storage, and application of improvements.
    """

    def __init__(self, repo_root: Optional[str] = None, store_path: Optional[str] = None):
        """Initialize the lessons learned engine.

        Args:
            repo_root: Path to the repository root.
            store_path: Path to the lessons JSON file.
        """
        if repo_root:
            self.repo_root = Path(os.path.abspath(repo_root))
        else:
            self.repo_root = Path(__file__).resolve().parent.parent

        self.store = LessonsStore(store_path)
        self.analyzer = PRAnalyzer(str(self.repo_root))
        self.applicator = ImprovementApplicator(str(self.repo_root))
        self.logger = get_logger()

    def run_post_pr_analysis(
        self,
        diff_content: Optional[str] = None,
        test_output: Optional[str] = None,
        lint_output: Optional[str] = None,
        pr_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the complete post-PR analysis loop.

        This is the main entry point called after each PR merge.

        Args:
            diff_content: PR diff content (unified diff format).
            test_output: Test results output.
            lint_output: Linter output.
            pr_number: PR number for tracking.

        Returns:
            Summary of analysis and applied improvements.
        """
        results: Dict[str, Any] = {
            "pr_number": pr_number,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lessons_found": 0,
            "improvements_applied": 0,
            "validation_findings": 0,
        }

        # Step 1: Analyze PR diff
        if diff_content:
            diff_lessons = self.analyzer.analyze_diff(diff_content, pr_number)
            for lesson in diff_lessons:
                self.store.add_lesson(lesson)
            results["lessons_found"] += len(diff_lessons)

        # Step 2: Analyze test results
        if test_output:
            test_lessons = self.analyzer.analyze_test_results(test_output, pr_number)
            for lesson in test_lessons:
                self.store.add_lesson(lesson)
            results["lessons_found"] += len(test_lessons)

        # Step 3: Analyze lint results
        if lint_output:
            lint_lessons = self.analyzer.analyze_lint_results(lint_output, pr_number)
            for lesson in lint_lessons:
                self.store.add_lesson(lesson)
            results["lessons_found"] += len(lint_lessons)

        # Step 4: Validate repository against all known lessons
        validation_findings = self.applicator.validate_repository(self.store)
        for lesson in validation_findings:
            self.store.add_lesson(lesson)
        results["validation_findings"] = len(validation_findings)

        # Step 5: Apply feasible improvements
        improvement_results = self.applicator.apply_improvements(self.store)
        results["improvements_applied"] = len(improvement_results.get("applied", []))
        results["improvement_details"] = improvement_results

        # Step 6: Save all lessons
        self.store.save()

        # Step 7: Generate summary
        results["store_summary"] = self.store.get_summary()

        return results

    def get_report(self) -> str:
        """Generate a human-readable report of lessons learned.

        Returns:
            Formatted report string.
        """
        summary = self.store.get_summary()
        lines = [
            "=" * 60,
            "Lessons Learned Report",
            "=" * 60,
            f"Total lessons: {summary['total']}",
            f"Applied: {summary['applied']}",
            f"Pending: {summary['pending']}",
            f"Auto-fixable: {summary['auto_fixable']}",
            "",
            "By Category:",
        ]

        for category, count in summary.get("by_category", {}).items():
            lines.append(f"  {category}: {count}")

        lines.append("")
        lines.append("Recent Lessons:")

        for lesson in self.store.lessons[-10:]:
            status = "✓" if lesson.applied else "○"
            lines.append(f"  {status} [{lesson.category}] {lesson.summary}")
            if lesson.recommendation:
                lines.append(f"    → {lesson.recommendation}")

        lines.append("=" * 60)
        return "\n".join(lines)


def main():
    """CLI entry point for the lessons learned engine."""
    import argparse

    parser = argparse.ArgumentParser(description="HA AI Workflow Lessons Learned Engine")
    parser.add_argument("--repo-root", help="Repository root path", default=None)
    parser.add_argument("--store-path", help="Path to lessons JSON file", default=None)
    parser.add_argument("--diff-file", help="Path to PR diff file", default=None)
    parser.add_argument("--test-output-file", help="Path to test output file", default=None)
    parser.add_argument("--lint-output-file", help="Path to lint output file", default=None)
    parser.add_argument("--pr-number", help="PR number", default=None)
    parser.add_argument("--report", action="store_true", help="Show lessons report")
    parser.add_argument("--scan", action="store_true", help="Scan repository for anti-patterns")

    args = parser.parse_args()

    engine = LessonsLearnedEngine(repo_root=args.repo_root, store_path=args.store_path)

    if args.report:
        print(engine.get_report())
        return

    # Read input files
    diff_content = None
    test_output = None
    lint_output = None

    if args.diff_file and os.path.exists(args.diff_file):
        with open(args.diff_file, "r") as f:
            diff_content = f.read()

    if args.test_output_file and os.path.exists(args.test_output_file):
        with open(args.test_output_file, "r") as f:
            test_output = f.read()

    if args.lint_output_file and os.path.exists(args.lint_output_file):
        with open(args.lint_output_file, "r") as f:
            lint_output = f.read()

    if args.scan:
        # Just scan the repository
        analyzer = PRAnalyzer(args.repo_root)
        findings = analyzer.scan_repository()
        for finding in findings:
            engine.store.add_lesson(finding)
        engine.store.save()
        print(f"Repository scan complete: {len(findings)} finding(s)")
        print(engine.get_report())
        return

    # Run post-PR analysis
    results = engine.run_post_pr_analysis(
        diff_content=diff_content,
        test_output=test_output,
        lint_output=lint_output,
        pr_number=args.pr_number,
    )

    print(f"Analysis complete for PR #{args.pr_number or 'unknown'}")
    print(f"  Lessons found: {results['lessons_found']}")
    print(f"  Validation findings: {results['validation_findings']}")
    print(f"  Improvements applied: {results['improvements_applied']}")
    print(engine.get_report())


if __name__ == "__main__":
    main()
