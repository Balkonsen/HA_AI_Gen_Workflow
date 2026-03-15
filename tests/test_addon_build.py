"""
Tests for Home Assistant add-on build configuration and compatibility.

Validates that the add-on configuration files are correct and consistent,
the Dockerfile follows HA builder conventions, and version detection works
for automated updates.
"""

import os
import re
import shutil
from typing import Any

import pytest
import yaml


# Paths relative to repository root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON_DIR = os.path.join(REPO_ROOT, "ha_ai_workflow_addon")
CONFIG_YAML = os.path.join(ADDON_DIR, "config.yaml")
BUILD_YAML = os.path.join(ADDON_DIR, "build.yaml")
DOCKERFILE = os.path.join(ADDON_DIR, "Dockerfile")
DOCKERIGNORE = os.path.join(ADDON_DIR, ".dockerignore")
RUN_SH = os.path.join(ADDON_DIR, "run.sh")
ADDON_CHANGELOG = os.path.join(ADDON_DIR, "CHANGELOG.md")
REPO_YAML = os.path.join(REPO_ROOT, "repository.yaml")
WORKFLOW_FILE = os.path.join(REPO_ROOT, ".github", "workflows", "docker-build.yml")


def _load_yaml_dict(file_path: str) -> dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj)
    assert isinstance(data, dict)
    return data


@pytest.mark.unit
class TestAddonConfigYaml:
    """Tests for ha_ai_workflow_addon/config.yaml"""

    def test_config_yaml_exists(self):
        """config.yaml must exist in the add-on directory."""
        assert os.path.isfile(CONFIG_YAML), f"config.yaml not found at {CONFIG_YAML}"

    def test_config_yaml_valid(self):
        """config.yaml must be valid YAML."""
        config = _load_yaml_dict(CONFIG_YAML)
        assert isinstance(config, dict), "config.yaml should parse to a dict"

    def test_config_yaml_required_fields(self):
        """config.yaml must have all required HA add-on fields."""
        config = _load_yaml_dict(CONFIG_YAML)
        required_fields = ["name", "version", "slug", "description", "arch", "image"]
        for field in required_fields:
            assert field in config, f"Missing required field '{field}' in config.yaml"

    def test_config_yaml_version_format(self):
        """Version must be a non-empty string."""
        config = _load_yaml_dict(CONFIG_YAML)
        version = str(config["version"])
        assert len(version) > 0, "Version must not be empty"
        assert version != "None", "Version must not be None"

    def test_config_yaml_arch_valid(self):
        """Architectures must be valid HA architectures."""
        config = _load_yaml_dict(CONFIG_YAML)
        valid_archs = {"amd64", "aarch64", "armv7", "armhf", "i386"}
        archs = config.get("arch", [])
        assert isinstance(archs, list)
        for arch in archs:
            assert arch in valid_archs, f"Invalid architecture '{arch}' in config.yaml"

    def test_config_yaml_image_pattern(self):
        """Image field must use {arch} placeholder for HA update detection."""
        config = _load_yaml_dict(CONFIG_YAML)
        image = config.get("image", "")
        assert (
            "{arch}" in image
        ), f"Image field must contain '{{arch}}' placeholder for HA to detect updates. Got: {image}"

    def test_config_yaml_image_uses_ghcr(self):
        """Image field should reference ghcr.io for GitHub Container Registry."""
        config = _load_yaml_dict(CONFIG_YAML)
        image = config.get("image", "")
        assert image.startswith("ghcr.io/"), f"Image should use ghcr.io registry. Got: {image}"


@pytest.mark.unit
class TestBuildYaml:
    """Tests for ha_ai_workflow_addon/build.yaml"""

    def test_build_yaml_exists(self):
        """build.yaml must exist in the add-on directory."""
        assert os.path.isfile(BUILD_YAML), f"build.yaml not found at {BUILD_YAML}"

    def test_build_yaml_valid(self):
        """build.yaml must be valid YAML."""
        build = _load_yaml_dict(BUILD_YAML)
        assert isinstance(build, dict), "build.yaml should parse to a dict"

    def test_build_yaml_has_build_from(self):
        """build.yaml must define base images via build_from."""
        build = _load_yaml_dict(BUILD_YAML)
        assert "build_from" in build, "build.yaml must have 'build_from' section"

    def test_build_yaml_arch_matches_config(self):
        """build.yaml build_from architectures must match config.yaml arch list."""
        config = _load_yaml_dict(CONFIG_YAML)
        build = _load_yaml_dict(BUILD_YAML)
        config_archs = set(config.get("arch", []))
        build_archs = set(build.get("build_from", {}).keys())
        assert (
            config_archs == build_archs
        ), f"Architecture mismatch: config.yaml has {config_archs}, build.yaml has {build_archs}"

    def test_build_yaml_base_images_valid(self):
        """Base images must reference HA base images."""
        build = _load_yaml_dict(BUILD_YAML)
        for arch, image in build.get("build_from", {}).items():
            assert "ghcr.io/home-assistant/" in image, f"Base image for {arch} should use HA base images. Got: {image}"


@pytest.mark.unit
class TestDockerfile:
    """Tests for ha_ai_workflow_addon/Dockerfile"""

    def test_dockerfile_exists(self):
        """Dockerfile must exist in the add-on directory."""
        assert os.path.isfile(DOCKERFILE), f"Dockerfile not found at {DOCKERFILE}"

    def test_dockerfile_uses_build_from_arg(self):
        """Dockerfile must use ARG BUILD_FROM and FROM $BUILD_FROM."""
        with open(DOCKERFILE, "r") as f:
            content = f.read()
        assert "ARG BUILD_FROM" in content, "Dockerfile must declare ARG BUILD_FROM"
        assert "${BUILD_FROM}" in content, "Dockerfile must use ${BUILD_FROM} in FROM"

    def test_dockerfile_no_parent_dir_copies(self):
        """Dockerfile must not reference parent directory paths (Docker limitation)."""
        with open(DOCKERFILE, "r") as f:
            content = f.read()
        assert "../" not in content, "Dockerfile cannot COPY from parent directory"

    def test_dockerfile_no_hardcoded_subdirectory_copies(self):
        """Dockerfile COPY paths must not reference ha_ai_workflow_addon/ (build context IS that dir)."""
        with open(DOCKERFILE, "r") as f:
            content = f.read()
        # Check only COPY/ADD instruction lines (not comments)
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Remove inline comments
            code_part = stripped.split("#")[0].strip()
            if code_part.upper().startswith(("COPY ", "ADD ")):
                assert "ha_ai_workflow_addon/" not in code_part, (
                    f"Dockerfile should not reference ha_ai_workflow_addon/ in COPY/ADD commands - "
                    f"the HA builder uses that directory as the build context. Line: {stripped}"
                )

    def test_dockerfile_copies_run_sh(self):
        """Dockerfile must copy run.sh."""
        with open(DOCKERFILE, "r") as f:
            content = f.read()
        assert "COPY run.sh" in content, "Dockerfile must COPY run.sh"

    def test_dockerfile_has_cmd(self):
        """Dockerfile must have a CMD instruction."""
        with open(DOCKERFILE, "r") as f:
            content = f.read()
        assert "CMD" in content, "Dockerfile must have a CMD instruction"


@pytest.mark.unit
class TestRunScript:
    """Tests for ha_ai_workflow_addon/run.sh"""

    def test_run_sh_exists(self):
        """run.sh must exist."""
        assert os.path.isfile(RUN_SH), f"run.sh not found at {RUN_SH}"

    def test_run_sh_executable(self):
        """run.sh must be executable."""
        assert os.access(RUN_SH, os.X_OK), "run.sh must be executable"

    def test_run_sh_has_shebang(self):
        """run.sh must start with a shebang."""
        with open(RUN_SH, "r") as f:
            first_line = f.readline()
        assert first_line.startswith("#!"), "run.sh must start with a shebang line"


@pytest.mark.unit
class TestVersionRetrieval:
    """Tests for automated version retrieval from config.yaml"""

    @staticmethod
    def _extract_version_from_line(line: str) -> str:
        """Extract version from a `version:` YAML line with optional quotes."""
        match = re.match(r'^version:\s*"?([^"\s]+)"?\s*$', line)
        return match.group(1) if match else ""

    def test_version_extractable_with_grep(self):
        """Version line must be discoverable as a top-level `version:` entry."""
        with open(CONFIG_YAML, "r", encoding="utf-8") as f:
            lines = f.readlines()

        version_lines = [line.strip() for line in lines if line.startswith("version:")]
        assert version_lines, "config.yaml should contain a top-level version line"
        assert "version:" in version_lines[0]

    def test_version_extraction_script(self):
        """Version extraction logic must produce a valid non-empty version string."""
        with open(CONFIG_YAML, "r", encoding="utf-8") as f:
            lines = f.readlines()

        version_line = next((line.strip() for line in lines if line.startswith("version:")), "")
        version = self._extract_version_from_line(version_line)
        assert len(version) > 0, "Version extraction should produce a non-empty string"
        assert version != "None", "Version extraction produced 'None' instead of a version"

    def test_version_matches_config(self):
        """Extracted version must match what's in config.yaml."""
        config = _load_yaml_dict(CONFIG_YAML)
        expected = str(config["version"])

        with open(CONFIG_YAML, "r", encoding="utf-8") as f:
            lines = f.readlines()

        version_line = next((line.strip() for line in lines if line.startswith("version:")), "")
        extracted = self._extract_version_from_line(version_line)
        assert extracted == expected, f"Extracted version '{extracted}' != config version '{expected}'"


@pytest.mark.unit
class TestRepositoryYaml:
    """Tests for repository.yaml (HA add-on repository metadata)"""

    def test_repository_yaml_exists(self):
        """repository.yaml must exist at repo root."""
        assert os.path.isfile(REPO_YAML), f"repository.yaml not found at {REPO_YAML}"

    def test_repository_yaml_valid(self):
        """repository.yaml must be valid YAML with required fields."""
        repo = _load_yaml_dict(REPO_YAML)
        assert isinstance(repo, dict), "repository.yaml should parse to a dict"
        assert "name" in repo, "repository.yaml must have 'name' field"
        assert "url" in repo, "repository.yaml must have 'url' field"


@pytest.mark.unit
class TestBuildWorkflow:
    """Tests for .github/workflows/docker-build.yml"""

    def test_workflow_exists(self):
        """docker-build.yml workflow must exist."""
        assert os.path.isfile(WORKFLOW_FILE), f"docker-build.yml not found at {WORKFLOW_FILE}"

    def test_workflow_valid_yaml(self):
        """Workflow file must be valid YAML."""
        with open(WORKFLOW_FILE, "r") as f:
            workflow = yaml.safe_load(f)
        assert isinstance(workflow, dict), "Workflow should parse to a dict"

    def test_workflow_uses_ha_builder(self):
        """Workflow should use home-assistant/builder action."""
        with open(WORKFLOW_FILE, "r") as f:
            content = f.read()
        assert (
            "home-assistant/builder" in content
        ), "Workflow should use home-assistant/builder action for HA compatibility"

    def test_workflow_targets_addon_dir(self):
        """Workflow must target ha_ai_workflow_addon directory."""
        with open(WORKFLOW_FILE, "r") as f:
            content = f.read()
        assert (
            "--target ha_ai_workflow_addon" in content
        ), "Workflow must use --target ha_ai_workflow_addon for the HA builder"

    def test_workflow_stages_files(self):
        """Workflow must stage files into the build context before building."""
        with open(WORKFLOW_FILE, "r") as f:
            content = f.read()
        # Check that the workflow copies requirements.txt and app directories
        assert "cp CHANGELOG.md ha_ai_workflow_addon/CHANGELOG.md" in content, (
            "Workflow should stage root CHANGELOG.md into add-on build context "
            "to keep release notes up to date in builds"
        )
        assert "requirements.txt" in content, "Workflow should stage requirements.txt"
        assert "bin/" in content, "Workflow should stage bin/ directory"

    def test_addon_changelog_not_committed(self):
        """Add-on directory should not have a duplicate committed CHANGELOG file."""
        assert not os.path.exists(
            ADDON_CHANGELOG
        ), "ha_ai_workflow_addon/CHANGELOG.md should not be committed; root CHANGELOG.md is the source of truth"

    def test_root_changelog_can_be_staged_into_addon_context(self):
        """Build workflow changelog staging command should produce add-on CHANGELOG.md at runtime."""
        root_changelog = os.path.join(REPO_ROOT, "CHANGELOG.md")
        assert os.path.isfile(root_changelog), "Root CHANGELOG.md should exist"
        assert not os.path.exists(ADDON_CHANGELOG), "Precondition failed: add-on CHANGELOG.md should not be committed"

        try:
            shutil.copyfile(root_changelog, ADDON_CHANGELOG)
            assert os.path.isfile(ADDON_CHANGELOG), "Staging should create add-on CHANGELOG.md"
            with open(root_changelog, "r", encoding="utf-8") as root_file:
                root_content = root_file.read()
            with open(ADDON_CHANGELOG, "r", encoding="utf-8") as staged_file:
                staged_content = staged_file.read()
            assert staged_content == root_content, "Staged changelog should match root CHANGELOG.md exactly"
        finally:
            if os.path.exists(ADDON_CHANGELOG):
                os.remove(ADDON_CHANGELOG)

    def test_workflow_builds_declared_archs(self):
        """Workflow build architectures should match config.yaml."""
        config = _load_yaml_dict(CONFIG_YAML)
        with open(WORKFLOW_FILE, "r") as f:
            content = f.read()
        for arch in config.get("arch", []):
            # Match --arch as a standalone flag (word boundary via whitespace/newline)
            pattern = rf"--{re.escape(arch)}(\s|\\|$)"
            assert re.search(pattern, content), f"Workflow should build for '{arch}' as declared in config.yaml"


@pytest.mark.unit
class TestDockerignore:
    """Tests for ha_ai_workflow_addon/.dockerignore"""

    def test_dockerignore_exists(self):
        """.dockerignore must exist in the add-on directory to reduce build context size."""
        assert os.path.isfile(DOCKERIGNORE), f".dockerignore not found at {DOCKERIGNORE}"

    def test_dockerignore_excludes_git(self):
        """.dockerignore must exclude .git/ to avoid bloating the build context."""
        with open(DOCKERIGNORE, "r") as f:
            content = f.read()
        assert ".git" in content, ".dockerignore should exclude .git directory"

    def test_dockerignore_excludes_tests(self):
        """.dockerignore must exclude tests/ (not needed at runtime)."""
        with open(DOCKERIGNORE, "r") as f:
            content = f.read()
        assert "tests/" in content, ".dockerignore should exclude tests directory"

    def test_dockerignore_excludes_docs(self):
        """.dockerignore must exclude docs/ (not needed at runtime)."""
        with open(DOCKERIGNORE, "r") as f:
            content = f.read()
        assert "docs/" in content, ".dockerignore should exclude docs directory"


@pytest.mark.unit
class TestDockerfileBuildPerformance:
    """Tests for Dockerfile build performance optimizations."""

    def test_dockerfile_uses_prefer_binary(self):
        """Dockerfile should use --prefer-binary to avoid compiling from source."""
        with open(DOCKERFILE, "r") as f:
            content = f.read()
        assert (
            "--prefer-binary" in content
        ), "Dockerfile should use --prefer-binary for pip install to use pre-built wheels"

    def test_dockerfile_has_progress_output(self):
        """Dockerfile pip install should show progress for user feedback."""
        with open(DOCKERFILE, "r") as f:
            content = f.read()
        assert "--progress-bar" in content, "Dockerfile should enable pip progress bar for install feedback"

    def test_dockerfile_build_deps_conditional(self):
        """Build dependencies (gcc, cargo) should only be installed if wheel install fails."""
        with open(DOCKERFILE, "r") as f:
            content = f.read()
        # Find the first RUN apk add block â€” it should contain only runtime deps
        lines = content.split("\n")
        in_first_apk = False
        first_apk_block = []
        for line in lines:
            stripped = line.strip()
            if not in_first_apk and "apk add" in stripped:
                in_first_apk = True
            if in_first_apk:
                first_apk_block.append(stripped)
                if not stripped.endswith("\\"):
                    break
        first_apk_content = " ".join(first_apk_block)
        assert (
            "gcc" not in first_apk_content
        ), "First apk add block should not include gcc (build dep) - it should be runtime deps only"

    def test_requirements_no_rpds_py_pin(self):
        """requirements.txt should not pin rpds-py (unnecessary with modern Alpine)."""
        req_file = os.path.join(REPO_ROOT, "requirements.txt")
        with open(req_file, "r") as f:
            content = f.read()
        assert "rpds-py" not in content, (
            "requirements.txt should not pin rpds-py - modern Alpine base images "
            "have a compatible Cargo and pre-built musllinux wheels are available"
        )
