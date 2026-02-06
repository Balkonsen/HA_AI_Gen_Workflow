#!/usr/bin/env python3
"""
Unit tests for the lessons_learned module.
"""

import os
import sys
import json

import pytest

# Add bin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

from lessons_learned import (  # noqa: E402
    LessonEntry,
    LessonsStore,
    PRAnalyzer,
    ImprovementApplicator,
    LessonsLearnedEngine,
)


@pytest.mark.unit
class TestLessonEntry:
    """Tests for LessonEntry data class."""

    def test_create_valid_entry(self):
        """Test creating a lesson entry with valid category."""
        entry = LessonEntry(
            category="build_failure",
            summary="Test summary",
            details="Test details",
        )
        assert entry.category == "build_failure"
        assert entry.summary == "Test summary"
        assert entry.details == "Test details"
        assert entry.applied is False
        assert entry.timestamp is not None

    def test_invalid_category_raises(self):
        """Test that invalid category raises ValueError."""
        with pytest.raises(ValueError, match="Invalid category"):
            LessonEntry(
                category="invalid_category",
                summary="Test",
                details="Test",
            )

    def test_serialization_roundtrip(self):
        """Test that to_dict/from_dict preserves all fields."""
        entry = LessonEntry(
            category="test_failure",
            summary="Tests failed",
            details="3 tests failed",
            source_pr="42",
            source_files=["tests/test_foo.py"],
            recommendation="Fix the tests",
            auto_fixable=True,
            fix_target="copilot_instructions",
            fix_content="## New Pitfall\nDon't do X",
        )
        data = entry.to_dict()
        restored = LessonEntry.from_dict(data)

        assert restored.category == entry.category
        assert restored.summary == entry.summary
        assert restored.details == entry.details
        assert restored.source_pr == entry.source_pr
        assert restored.source_files == entry.source_files
        assert restored.recommendation == entry.recommendation
        assert restored.auto_fixable == entry.auto_fixable
        assert restored.fix_target == entry.fix_target
        assert restored.fix_content == entry.fix_content

    def test_default_optional_fields(self):
        """Test that optional fields default correctly."""
        entry = LessonEntry(
            category="lint_issue",
            summary="Lint issue",
            details="Details",
        )
        assert entry.source_pr is None
        assert entry.source_files == []
        assert entry.recommendation is None
        assert entry.auto_fixable is False
        assert entry.fix_target is None
        assert entry.fix_content is None


@pytest.mark.unit
class TestLessonsStore:
    """Tests for LessonsStore persistence layer."""

    def test_empty_store(self, tmp_path):
        """Test creating a new empty store."""
        store_file = str(tmp_path / "lessons.json")
        store = LessonsStore(store_path=store_file)
        assert len(store.lessons) == 0

    def test_add_and_save(self, tmp_path):
        """Test adding a lesson and saving to file."""
        store_file = str(tmp_path / "lessons.json")
        store = LessonsStore(store_path=store_file)

        lesson = LessonEntry(
            category="build_failure",
            summary="Docker build failed",
            details="COPY path was wrong",
        )
        store.add_lesson(lesson)
        store.save()

        # Verify file contents
        with open(store_file, "r") as f:
            data = json.load(f)
        assert data["total_lessons"] == 1
        assert data["lessons"][0]["summary"] == "Docker build failed"

    def test_load_existing(self, tmp_path):
        """Test loading from an existing file."""
        store_file = str(tmp_path / "lessons.json")

        # Create initial store
        store1 = LessonsStore(store_path=store_file)
        store1.add_lesson(LessonEntry(category="lint_issue", summary="Lint 1", details="D1"))
        store1.add_lesson(LessonEntry(category="lint_issue", summary="Lint 2", details="D2"))
        store1.save()

        # Load from file
        store2 = LessonsStore(store_path=store_file)
        assert len(store2.lessons) == 2

    def test_no_duplicates(self, tmp_path):
        """Test that duplicate lessons (same summary+category) are skipped."""
        store_file = str(tmp_path / "lessons.json")
        store = LessonsStore(store_path=store_file)

        lesson1 = LessonEntry(category="build_failure", summary="Same issue", details="D1")
        lesson2 = LessonEntry(category="build_failure", summary="Same issue", details="D2")
        store.add_lesson(lesson1)
        store.add_lesson(lesson2)

        assert len(store.lessons) == 1

    def test_get_unapplied(self, tmp_path):
        """Test filtering unapplied auto-fixable lessons."""
        store_file = str(tmp_path / "lessons.json")
        store = LessonsStore(store_path=store_file)

        lesson1 = LessonEntry(
            category="lint_issue",
            summary="Fixable",
            details="D1",
            auto_fixable=True,
            fix_target="copilot_instructions",
            fix_content="content",
        )
        lesson2 = LessonEntry(
            category="lint_issue",
            summary="Not fixable",
            details="D2",
            auto_fixable=False,
        )
        store.add_lesson(lesson1)
        store.add_lesson(lesson2)

        unapplied = store.get_unapplied()
        assert len(unapplied) == 1
        assert unapplied[0].summary == "Fixable"

    def test_get_by_category(self, tmp_path):
        """Test filtering by category."""
        store_file = str(tmp_path / "lessons.json")
        store = LessonsStore(store_path=store_file)

        store.add_lesson(LessonEntry(category="lint_issue", summary="L1", details="D1"))
        store.add_lesson(LessonEntry(category="build_failure", summary="B1", details="D1"))
        store.add_lesson(LessonEntry(category="lint_issue", summary="L2", details="D2"))

        lint_lessons = store.get_by_category("lint_issue")
        assert len(lint_lessons) == 2

        build_lessons = store.get_by_category("build_failure")
        assert len(build_lessons) == 1

    def test_mark_applied(self, tmp_path):
        """Test marking a lesson as applied."""
        store_file = str(tmp_path / "lessons.json")
        store = LessonsStore(store_path=store_file)

        lesson = LessonEntry(category="lint_issue", summary="Issue", details="D", auto_fixable=True)
        store.add_lesson(lesson)
        store.mark_applied(lesson)

        assert lesson.applied is True
        assert len(store.get_unapplied()) == 0

    def test_get_summary(self, tmp_path):
        """Test generating a summary."""
        store_file = str(tmp_path / "lessons.json")
        store = LessonsStore(store_path=store_file)

        store.add_lesson(LessonEntry(category="lint_issue", summary="L1", details="D1"))
        store.add_lesson(
            LessonEntry(
                category="build_failure",
                summary="B1",
                details="D1",
                auto_fixable=True,
            )
        )

        summary = store.get_summary()
        assert summary["total"] == 2
        assert summary["applied"] == 0
        assert summary["pending"] == 2
        assert summary["auto_fixable"] == 1
        assert summary["by_category"]["lint_issue"] == 1
        assert summary["by_category"]["build_failure"] == 1


@pytest.mark.unit
class TestPRAnalyzer:
    """Tests for PRAnalyzer diff and output analysis."""

    def test_analyze_diff_docker_context(self, tmp_path):
        """Test detecting Docker context path issues in diffs."""
        diff = """diff --git a/Dockerfile b/Dockerfile
--- a/Dockerfile
+++ b/Dockerfile
@@ -1,3 +1,3 @@
 FROM python:3.11-alpine
-COPY bin/ /app/bin/
+COPY ha_ai_workflow_addon/bin/ /app/bin/
"""
        analyzer = PRAnalyzer(str(tmp_path))
        lessons = analyzer.analyze_diff(diff, pr_number="99")

        assert len(lessons) >= 1
        docker_lessons = [lesson for lesson in lessons if "COPY" in lesson.summary or "Dockerfile" in lesson.summary]
        assert len(docker_lessons) >= 1

    def test_analyze_diff_bashio(self, tmp_path):
        """Test detecting bashio usage in diffs."""
        diff = """diff --git a/run.sh b/run.sh
--- a/run.sh
+++ b/run.sh
@@ -1,2 +1,2 @@
-#!/usr/bin/env bash
+#!/usr/bin/with-contenv bashio
"""
        analyzer = PRAnalyzer(str(tmp_path))
        lessons = analyzer.analyze_diff(diff, pr_number="100")

        bashio_lessons = [lesson for lesson in lessons if "bashio" in lesson.summary.lower()]
        assert len(bashio_lessons) >= 1

    def test_analyze_diff_bare_except(self, tmp_path):
        """Test detecting bare except clauses in diffs."""
        diff = """diff --git a/bin/test.py b/bin/test.py
--- a/bin/test.py
+++ b/bin/test.py
@@ -1,3 +1,4 @@
 try:
     do_something()
+except:
+    pass
"""
        analyzer = PRAnalyzer(str(tmp_path))
        lessons = analyzer.analyze_diff(diff, pr_number="101")

        bare_except = [lesson for lesson in lessons if "except" in lesson.summary.lower()]
        assert len(bare_except) >= 1

    def test_analyze_diff_clean(self, tmp_path):
        """Test that clean diffs produce no lessons."""
        diff = """diff --git a/bin/test.py b/bin/test.py
--- a/bin/test.py
+++ b/bin/test.py
@@ -1,3 +1,4 @@
 import os
+import sys
"""
        analyzer = PRAnalyzer(str(tmp_path))
        lessons = analyzer.analyze_diff(diff, pr_number="102")
        assert len(lessons) == 0

    def test_analyze_test_results_with_failures(self, tmp_path):
        """Test extracting lessons from test failure output."""
        test_output = """
FAILED tests/test_foo.py::TestFoo::test_bar - AssertionError: expected True
FAILED tests/test_baz.py::TestBaz::test_qux - ValueError: invalid input
======================== 2 failed, 10 passed in 1.5s ========================
"""
        analyzer = PRAnalyzer(str(tmp_path))
        lessons = analyzer.analyze_test_results(test_output, pr_number="103")

        assert len(lessons) >= 1
        assert any("2 test(s) failed" in lesson.summary for lesson in lessons)

    def test_analyze_test_results_passing(self, tmp_path):
        """Test that all-passing tests produce no lessons."""
        test_output = """
======================== 42 passed in 2.0s ========================
"""
        analyzer = PRAnalyzer(str(tmp_path))
        lessons = analyzer.analyze_test_results(test_output, pr_number="104")
        assert len(lessons) == 0

    def test_analyze_test_results_deprecation(self, tmp_path):
        """Test extracting deprecation warnings from test output."""
        test_output = """
tests/test_foo.py::test_bar
  DeprecationWarning: use xyz instead of abc
======================== 10 passed in 1.0s ========================
"""
        analyzer = PRAnalyzer(str(tmp_path))
        lessons = analyzer.analyze_test_results(test_output, pr_number="105")

        dep_lessons = [lesson for lesson in lessons if lesson.category == "dependency_issue"]
        assert len(dep_lessons) >= 1

    def test_analyze_lint_results_with_violations(self, tmp_path):
        """Test extracting lessons from lint violations."""
        lint_output = """
bin/foo.py:10:5: E303 too many blank lines (3)
bin/foo.py:20:1: W291 trailing whitespace
bin/bar.py:5:1: E303 too many blank lines (3)
"""
        analyzer = PRAnalyzer(str(tmp_path))
        lessons = analyzer.analyze_lint_results(lint_output, pr_number="106")

        assert len(lessons) >= 1
        assert any("violations" in lesson.summary.lower() for lesson in lessons)

    def test_analyze_lint_results_black_reformat(self, tmp_path):
        """Test detecting black formatting issues."""
        lint_output = """
would reformat bin/foo.py
would reformat bin/bar.py
Oh no! 💥 💔 💥
2 files would be reformatted.
"""
        analyzer = PRAnalyzer(str(tmp_path))
        lessons = analyzer.analyze_lint_results(lint_output, pr_number="107")

        assert len(lessons) >= 1
        assert any("black" in lesson.summary.lower() for lesson in lessons)

    def test_analyze_lint_results_clean(self, tmp_path):
        """Test that clean lint output produces no lessons."""
        lint_output = """
All done! ✨ 🍰 ✨
42 files left unchanged.
"""
        analyzer = PRAnalyzer(str(tmp_path))
        lessons = analyzer.analyze_lint_results(lint_output, pr_number="108")
        assert len(lessons) == 0

    def test_extract_added_lines(self):
        """Test extracting added lines from a diff."""
        diff = """@@ -1,3 +1,5 @@
 existing line
+added line 1
+added line 2
 another existing line
"""
        added = PRAnalyzer._extract_added_lines(diff)
        assert len(added) == 2
        assert added[0][1] == "added line 1"
        assert added[1][1] == "added line 2"

    def test_extract_changed_files(self):
        """Test extracting changed file paths from a diff."""
        diff = """diff --git a/bin/foo.py b/bin/foo.py
--- a/bin/foo.py
+++ b/bin/foo.py
@@ -1,3 +1,3 @@
diff --git a/tests/test_foo.py b/tests/test_foo.py
--- a/tests/test_foo.py
+++ b/tests/test_foo.py
@@ -1,3 +1,3 @@
"""
        files = PRAnalyzer._extract_changed_files(diff)
        assert "bin/foo.py" in files
        assert "tests/test_foo.py" in files

    def test_scan_repository(self, tmp_path):
        """Test scanning a mock repository for anti-patterns."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        # Create a file with a bare except
        (bin_dir / "bad_module.py").write_text("try:\n    x = 1\nexcept:\n    pass\n")

        analyzer = PRAnalyzer(str(tmp_path))
        lessons = analyzer.scan_repository()

        assert len(lessons) >= 1
        assert any("except" in entry.summary.lower() for entry in lessons)


@pytest.mark.unit
class TestImprovementApplicator:
    """Tests for ImprovementApplicator."""

    def test_apply_fix_appends_content(self, tmp_path):
        """Test that a fix appends content to the target file."""
        # Create a mock target file
        github_dir = tmp_path / ".github"
        github_dir.mkdir(parents=True)
        target_file = github_dir / "copilot-instructions.md"
        target_file.write_text("# Instructions\n\nExisting content.\n")

        applicator = ImprovementApplicator(str(tmp_path))

        store = LessonsStore(str(tmp_path / "lessons.json"))
        lesson = LessonEntry(
            category="build_failure",
            summary="New pitfall discovered",
            details="Details here",
            auto_fixable=True,
            fix_target="copilot_instructions",
            fix_content="## New Pitfall\n\nAvoid doing X.",
        )
        store.add_lesson(lesson)

        results = applicator.apply_improvements(store)

        assert len(results["applied"]) == 1
        content = target_file.read_text()
        assert "New Pitfall" in content
        assert "Avoid doing X" in content

    def test_idempotent_fix(self, tmp_path):
        """Test that applying the same fix twice is idempotent."""
        github_dir = tmp_path / ".github"
        github_dir.mkdir(parents=True)
        target_file = github_dir / "copilot-instructions.md"
        target_file.write_text("# Instructions\n\n## New Pitfall\n\nAvoid doing X.\n")

        applicator = ImprovementApplicator(str(tmp_path))

        store = LessonsStore(str(tmp_path / "lessons.json"))
        lesson = LessonEntry(
            category="build_failure",
            summary="New pitfall discovered",
            details="Details here",
            auto_fixable=True,
            fix_target="copilot_instructions",
            fix_content="## New Pitfall\n\nAvoid doing X.",
        )
        store.add_lesson(lesson)

        applicator.apply_improvements(store)

        # Content should already exist, so the lesson gets marked applied but
        # nothing new is appended
        content = target_file.read_text()
        assert content.count("New Pitfall") == 1

    def test_skip_unknown_target(self, tmp_path):
        """Test that unknown fix targets are skipped."""
        applicator = ImprovementApplicator(str(tmp_path))

        store = LessonsStore(str(tmp_path / "lessons.json"))
        lesson = LessonEntry(
            category="build_failure",
            summary="Unknown target",
            details="Details",
            auto_fixable=True,
            fix_target="nonexistent_target",
            fix_content="content",
        )
        store.add_lesson(lesson)

        results = applicator.apply_improvements(store)
        assert len(results["skipped"]) == 1

    def test_skip_missing_content(self, tmp_path):
        """Test that lessons without fix content are skipped."""
        applicator = ImprovementApplicator(str(tmp_path))

        store = LessonsStore(str(tmp_path / "lessons.json"))
        lesson = LessonEntry(
            category="build_failure",
            summary="No content",
            details="Details",
            auto_fixable=True,
            fix_target="copilot_instructions",
        )
        store.add_lesson(lesson)

        results = applicator.apply_improvements(store)
        assert len(results["skipped"]) == 1

    def test_validate_repository(self, tmp_path):
        """Test repository validation against known lessons."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        (bin_dir / "module.py").write_text("try:\n    x = 1\nexcept:\n    pass\n")

        applicator = ImprovementApplicator(str(tmp_path))
        store = LessonsStore(str(tmp_path / "lessons.json"))

        new_lessons = applicator.validate_repository(store)
        assert len(new_lessons) >= 1


@pytest.mark.unit
class TestLessonsLearnedEngine:
    """Tests for the main LessonsLearnedEngine orchestrator."""

    def test_run_post_pr_analysis_with_diff(self, tmp_path):
        """Test running analysis with a PR diff."""
        engine = LessonsLearnedEngine(
            repo_root=str(tmp_path),
            store_path=str(tmp_path / "lessons.json"),
        )

        diff = """diff --git a/run.sh b/run.sh
--- a/run.sh
+++ b/run.sh
@@ -1,2 +1,2 @@
-#!/usr/bin/env bash
+#!/usr/bin/with-contenv bashio
"""
        results = engine.run_post_pr_analysis(
            diff_content=diff,
            pr_number="200",
        )

        assert results["pr_number"] == "200"
        assert results["lessons_found"] >= 1
        assert "store_summary" in results

    def test_run_post_pr_analysis_with_test_output(self, tmp_path):
        """Test running analysis with test output."""
        engine = LessonsLearnedEngine(
            repo_root=str(tmp_path),
            store_path=str(tmp_path / "lessons.json"),
        )

        test_output = """
FAILED tests/test_a.py::TestA::test_x - AssertionError
======================== 1 failed, 5 passed in 0.5s ========================
"""
        results = engine.run_post_pr_analysis(
            test_output=test_output,
            pr_number="201",
        )

        assert results["lessons_found"] >= 1

    def test_run_post_pr_analysis_with_lint_output(self, tmp_path):
        """Test running analysis with lint output."""
        engine = LessonsLearnedEngine(
            repo_root=str(tmp_path),
            store_path=str(tmp_path / "lessons.json"),
        )

        lint_output = """
would reformat bin/foo.py
"""
        results = engine.run_post_pr_analysis(
            lint_output=lint_output,
            pr_number="202",
        )

        assert results["lessons_found"] >= 1

    def test_run_post_pr_analysis_no_input(self, tmp_path):
        """Test running analysis with no input (repo scan only)."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        (bin_dir / "clean.py").write_text("import os\n")

        engine = LessonsLearnedEngine(
            repo_root=str(tmp_path),
            store_path=str(tmp_path / "lessons.json"),
        )

        results = engine.run_post_pr_analysis(pr_number="203")

        assert results["pr_number"] == "203"
        assert "store_summary" in results

    def test_get_report(self, tmp_path):
        """Test generating a human-readable report."""
        engine = LessonsLearnedEngine(
            repo_root=str(tmp_path),
            store_path=str(tmp_path / "lessons.json"),
        )

        engine.store.add_lesson(
            LessonEntry(
                category="build_failure",
                summary="Build broke",
                details="Docker issue",
                recommendation="Fix the Dockerfile",
            )
        )

        report = engine.get_report()
        assert "Lessons Learned Report" in report
        assert "Build broke" in report
        assert "Fix the Dockerfile" in report

    def test_full_loop_integration(self, tmp_path):
        """Test the complete analysis-store-apply loop."""
        # Set up a mock repo structure
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        (bin_dir / "module.py").write_text("import os\n")

        github_dir = tmp_path / ".github"
        github_dir.mkdir(parents=True)
        (github_dir / "copilot-instructions.md").write_text("# Instructions\n")

        engine = LessonsLearnedEngine(
            repo_root=str(tmp_path),
            store_path=str(tmp_path / "lessons.json"),
        )

        # Add an auto-fixable lesson
        lesson = LessonEntry(
            category="configuration_drift",
            summary="Missing rule",
            details="Should document a new rule",
            auto_fixable=True,
            fix_target="copilot_instructions",
            fix_content="## Learned Rule\n\nAlways do Y.",
        )
        engine.store.add_lesson(lesson)

        # Run analysis (which also applies improvements)
        results = engine.run_post_pr_analysis(pr_number="300")

        assert results["improvements_applied"] >= 1

        # Verify the file was updated
        content = (github_dir / "copilot-instructions.md").read_text()
        assert "Learned Rule" in content
        assert "Always do Y" in content

        # Verify the lesson is marked applied
        assert engine.store.lessons[0].applied is True
