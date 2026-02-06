"""
Tests for Home Assistant add-on build configuration and compatibility.

Validates that the add-on configuration files are correct and consistent,
the Dockerfile follows HA builder conventions, and version detection works
for automated updates.
"""

import os
import re
import subprocess

import pytest
import yaml


# Paths relative to repository root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON_DIR = os.path.join(REPO_ROOT, "ha_ai_workflow_addon")
CONFIG_YAML = os.path.join(ADDON_DIR, "config.yaml")
BUILD_YAML = os.path.join(ADDON_DIR, "build.yaml")
DOCKERFILE = os.path.join(ADDON_DIR, "Dockerfile")
RUN_SH = os.path.join(ADDON_DIR, "run.sh")
REPO_YAML = os.path.join(REPO_ROOT, "repository.yaml")
WORKFLOW_FILE = os.path.join(REPO_ROOT, ".github", "workflows", "docker-build.yml")


@pytest.mark.unit
class TestAddonConfigYaml:
    """Tests for ha_ai_workflow_addon/config.yaml"""

    def test_config_yaml_exists(self):
        """config.yaml must exist in the add-on directory."""
        assert os.path.isfile(CONFIG_YAML), f"config.yaml not found at {CONFIG_YAML}"

    def test_config_yaml_valid(self):
        """config.yaml must be valid YAML."""
        with open(CONFIG_YAML, "r") as f:
            config = yaml.safe_load(f)
        assert isinstance(config, dict), "config.yaml should parse to a dict"

    def test_config_yaml_required_fields(self):
        """config.yaml must have all required HA add-on fields."""
        with open(CONFIG_YAML, "r") as f:
            config = yaml.safe_load(f)
        required_fields = ["name", "version", "slug", "description", "arch", "image"]
        for field in required_fields:
            assert field in config, f"Missing required field '{field}' in config.yaml"

    def test_config_yaml_version_format(self):
        """Version must be a non-empty string."""
        with open(CONFIG_YAML, "r") as f:
            config = yaml.safe_load(f)
        version = str(config["version"])
        assert len(version) > 0, "Version must not be empty"
        assert version != "None", "Version must not be None"

    def test_config_yaml_arch_valid(self):
        """Architectures must be valid HA architectures."""
        with open(CONFIG_YAML, "r") as f:
            config = yaml.safe_load(f)
        valid_archs = {"amd64", "aarch64", "armv7", "armhf", "i386"}
        for arch in config["arch"]:
            assert arch in valid_archs, f"Invalid architecture '{arch}' in config.yaml"

    def test_config_yaml_image_pattern(self):
        """Image field must use {arch} placeholder for HA update detection."""
        with open(CONFIG_YAML, "r") as f:
            config = yaml.safe_load(f)
        image = config.get("image", "")
        assert "{arch}" in image, (
            f"Image field must contain '{{arch}}' placeholder for HA to detect updates. Got: {image}"
        )

    def test_config_yaml_image_uses_ghcr(self):
        """Image field should reference ghcr.io for GitHub Container Registry."""
        with open(CONFIG_YAML, "r") as f:
            config = yaml.safe_load(f)
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
        with open(BUILD_YAML, "r") as f:
            build = yaml.safe_load(f)
        assert isinstance(build, dict), "build.yaml should parse to a dict"

    def test_build_yaml_has_build_from(self):
        """build.yaml must define base images via build_from."""
        with open(BUILD_YAML, "r") as f:
            build = yaml.safe_load(f)
        assert "build_from" in build, "build.yaml must have 'build_from' section"

    def test_build_yaml_arch_matches_config(self):
        """build.yaml build_from architectures must match config.yaml arch list."""
        with open(CONFIG_YAML, "r") as f:
            config = yaml.safe_load(f)
        with open(BUILD_YAML, "r") as f:
            build = yaml.safe_load(f)
        config_archs = set(config.get("arch", []))
        build_archs = set(build.get("build_from", {}).keys())
        assert config_archs == build_archs, (
            f"Architecture mismatch: config.yaml has {config_archs}, build.yaml has {build_archs}"
        )

    def test_build_yaml_base_images_valid(self):
        """Base images must reference HA base images."""
        with open(BUILD_YAML, "r") as f:
            build = yaml.safe_load(f)
        for arch, image in build.get("build_from", {}).items():
            assert "ghcr.io/home-assistant/" in image, (
                f"Base image for {arch} should use HA base images. Got: {image}"
            )


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
        # Ignore comments
        lines = [line for line in content.split("\n") if not line.strip().startswith("#")]
        code_content = "\n".join(lines)
        assert "ha_ai_workflow_addon/" not in code_content, (
            "Dockerfile should not reference ha_ai_workflow_addon/ in COPY commands - "
            "the HA builder uses that directory as the build context"
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

    def test_version_extractable_with_grep(self):
        """Version must be extractable using the same method as the CI workflow."""
        result = subprocess.run(
            ["grep", "^version:", CONFIG_YAML],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "grep should find version line in config.yaml"
        version_line = result.stdout.strip()
        assert "version:" in version_line

    def test_version_extraction_script(self):
        """The CI version extraction command must produce a valid version string."""
        result = subprocess.run(
            [
                "bash",
                "-c",
                f"grep '^version:' {CONFIG_YAML} | head -n1 | "
                f"sed 's/version:[[:space:]]*\"\\{{0,1\\}}\\([^\"]*\\)\"\\{{0,1\\}}/\\1/' | "
                f"tr -d '[:space:]'",
            ],
            capture_output=True,
            text=True,
        )
        version = result.stdout.strip()
        assert len(version) > 0, "Version extraction should produce a non-empty string"
        assert version != "None", f"Version extraction produced 'None' instead of a version"

    def test_version_matches_config(self):
        """Extracted version must match what's in config.yaml."""
        with open(CONFIG_YAML, "r") as f:
            config = yaml.safe_load(f)
        expected = str(config["version"])

        result = subprocess.run(
            [
                "bash",
                "-c",
                f"grep '^version:' {CONFIG_YAML} | head -n1 | "
                f"sed 's/version:[[:space:]]*\"\\{{0,1\\}}\\([^\"]*\\)\"\\{{0,1\\}}/\\1/' | "
                f"tr -d '[:space:]'",
            ],
            capture_output=True,
            text=True,
        )
        extracted = result.stdout.strip()
        assert extracted == expected, f"Extracted version '{extracted}' != config version '{expected}'"


@pytest.mark.unit
class TestRepositoryYaml:
    """Tests for repository.yaml (HA add-on repository metadata)"""

    def test_repository_yaml_exists(self):
        """repository.yaml must exist at repo root."""
        assert os.path.isfile(REPO_YAML), f"repository.yaml not found at {REPO_YAML}"

    def test_repository_yaml_valid(self):
        """repository.yaml must be valid YAML with required fields."""
        with open(REPO_YAML, "r") as f:
            repo = yaml.safe_load(f)
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
        assert "home-assistant/builder" in content, (
            "Workflow should use home-assistant/builder action for HA compatibility"
        )

    def test_workflow_targets_addon_dir(self):
        """Workflow must target ha_ai_workflow_addon directory."""
        with open(WORKFLOW_FILE, "r") as f:
            content = f.read()
        assert "--target ha_ai_workflow_addon" in content, (
            "Workflow must use --target ha_ai_workflow_addon for the HA builder"
        )

    def test_workflow_stages_files(self):
        """Workflow must stage files into the build context before building."""
        with open(WORKFLOW_FILE, "r") as f:
            content = f.read()
        # Check that the workflow copies requirements.txt and app directories
        assert "requirements.txt" in content, "Workflow should stage requirements.txt"
        assert "bin/" in content, "Workflow should stage bin/ directory"

    def test_workflow_builds_declared_archs(self):
        """Workflow build architectures should match config.yaml."""
        with open(CONFIG_YAML, "r") as f:
            config = yaml.safe_load(f)
        with open(WORKFLOW_FILE, "r") as f:
            content = f.read()
        for arch in config.get("arch", []):
            assert f"--{arch}" in content, (
                f"Workflow should build for '{arch}' as declared in config.yaml"
            )
