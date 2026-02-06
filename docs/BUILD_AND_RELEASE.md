# Docker Image Build and Release Process

This document explains how Docker images are built and published for the HA AI Gen Workflow add-on.

## Overview

The add-on uses the official **Home Assistant Builder** GitHub Action to build and publish Docker images to GitHub Container Registry (GHCR). This ensures proper integration with Home Assistant's add-on update mechanism.

## Build System

### GitHub Actions Workflow

The build process is automated via `.github/workflows/docker-build.yml` and uses:
- **Action**: `home-assistant/builder@2025.11.0`
- **Registry**: GitHub Container Registry (ghcr.io)
- **Images**: `ghcr.io/balkonsen/ha_ai_gen_workflow-{arch}`

### Supported Architectures

- **amd64** (64-bit x86 - Intel/AMD processors)
- **aarch64** (64-bit ARM)
  - Raspberry Pi 4, 4B, 400, 5
  - Raspberry Pi 3, 3B+
  - Home Assistant Green/Yellow

**Note**: As of Home Assistant 2026.2.0, 32-bit architectures (armv7, i386, armhf) are no longer supported. Raspberry Pi 4+ requires 64-bit Home Assistant OS.

## How It Works

### 1. Version Management

The version is managed in `ha_ai_workflow_addon/config.yaml`:

```yaml
version: "1.0.4"
```

The Home Assistant builder automatically:
- Reads the version from `config.yaml`
- Tags Docker images with the version number
- Tags the latest build as `latest` on the main branch
- Publishes to GHCR with proper metadata

### 2. Build Triggers

Images are built automatically when:
- **Push to main branch** - Builds and publishes images tagged with version and `latest`
- **New version tag** (e.g., `v1.0.4`) - Builds and publishes release images
- **Pull request** - Builds images for testing only (not published)
- **Manual trigger** - Via workflow_dispatch

### 3. Image Tagging

For version `1.0.4`, the following images are created:
```
ghcr.io/balkonsen/ha_ai_gen_workflow-amd64:1.0.4
ghcr.io/balkonsen/ha_ai_gen_workflow-amd64:latest
ghcr.io/balkonsen/ha_ai_gen_workflow-aarch64:1.0.4
ghcr.io/balkonsen/ha_ai_gen_workflow-aarch64:latest
```

### 4. Home Assistant Discovery

Home Assistant discovers updates by:
1. Reading `repository.yaml` from GitHub
2. Checking each add-on's `config.yaml` for version changes
3. Pulling the Docker image: `ghcr.io/balkonsen/ha_ai_gen_workflow-{arch}:{version}`

## Release Process

### Making a New Release

1. **Update version** in `ha_ai_workflow_addon/config.yaml`:
   ```yaml
   version: "1.0.5"  # Increment version
   ```

2. **Update version label** in `ha_ai_workflow_addon/Dockerfile`:
   ```dockerfile
   LABEL io.hass.version="1.0.5"
   ```

3. **Update CHANGELOG** in `ha_ai_workflow_addon/CHANGELOG.md`:
   ```markdown
   ## 1.0.5
   - Feature: Description of changes
   - Fix: Bug fixes
   ```

4. **Commit and push** to main branch:
   ```bash
   git add ha_ai_workflow_addon/config.yaml ha_ai_workflow_addon/Dockerfile ha_ai_workflow_addon/CHANGELOG.md
   git commit -m "Release version 1.0.5"
   git push origin main
   ```

5. **Create a git tag** (optional, but recommended):
   ```bash
   git tag -a v1.0.5 -m "Release version 1.0.5"
   git push origin v1.0.5
   ```

6. **Monitor the build**:
   - Check GitHub Actions at: https://github.com/Balkonsen/HA_AI_Gen_Workflow/actions
   - Ensure all architecture builds complete successfully

7. **Verify publication**:
   - Images should appear in GHCR: https://github.com/Balkonsen/HA_AI_Gen_Workflow/pkgs/container/ha_ai_gen_workflow-amd64
   - Check that both `1.0.5` and `latest` tags exist

8. **Test in Home Assistant**:
   - Users should see the update in the Add-on Store
   - Install/update should pull the new version

## Architecture Configuration

### Files to Keep Consistent

When adding/removing architectures, update these files:

1. **`ha_ai_workflow_addon/config.yaml`**:
   ```yaml
   arch:
     - amd64
     - aarch64
   ```

2. **`ha_ai_workflow_addon/build.yaml`**:
   ```yaml
   build_from:
     amd64: ghcr.io/home-assistant/amd64-base-python:3.11-alpine3.18
     aarch64: ghcr.io/home-assistant/aarch64-base-python:3.11-alpine3.18
   ```

3. **`.github/workflows/docker-build.yml`**:
   ```yaml
   args: |
     --amd64 \
     --aarch64 \
     --target ha_ai_workflow_addon \
     --docker-hub ghcr.io/balkonsen
   ```

## Troubleshooting

### Home Assistant Not Detecting Updates

**Symptom**: New version released but HA shows no update available

**Causes**:
1. Version in `config.yaml` not incremented
2. Docker images not published to GHCR
3. GitHub Actions workflow failed
4. HA repository cache not refreshed

**Solutions**:
1. Verify version in `config.yaml` is higher than current
2. Check GitHub Actions for build failures
3. Verify images exist in GHCR packages
4. In HA: Settings → Add-ons → Add-on Store → ⋮ → Check for updates
5. Try removing and re-adding the repository

### Build Failures

**Common Issues**:

1. **Docker build timeout**:
   - Increase timeout in workflow
   - Check network connectivity
   - Retry the build

2. **Permission denied pushing to GHCR**:
   - Verify `GITHUB_TOKEN` has `packages: write` permission
   - Check workflow permissions in `.github/workflows/docker-build.yml`

3. **Base image not found**:
   - Verify base image tags in `build.yaml`
   - Check Home Assistant base image availability

### Testing Builds Locally

To test the build locally before pushing:

```bash
# Clone the repository
git clone https://github.com/Balkonsen/HA_AI_Gen_Workflow.git
cd HA_AI_Gen_Workflow

# Build for amd64
docker build \
  --build-arg BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11-alpine3.18 \
  -t ha_ai_gen_workflow-amd64:test \
  -f ha_ai_workflow_addon/Dockerfile \
  .

# Run the test image
docker run --rm ha_ai_gen_workflow-amd64:test
```

## Migration from Old Build System

If you were using a manual Docker build system (pre-2024 style):

### Old Approach (Don't Use)
```yaml
# Old workflow - manual docker build
- uses: docker/build-push-action@v5
  with:
    context: .
    file: ./ha_ai_workflow_addon/Dockerfile
    platforms: ${{ matrix.platform }}
    push: true
    tags: manual-tags
```

### New Approach (Current)
```yaml
# New workflow - Home Assistant builder
- uses: home-assistant/builder@2025.11.0
  with:
    args: |
      --amd64 \
      --aarch64 \
      --target ha_ai_workflow_addon \
      --docker-hub ghcr.io/balkonsen
```

**Benefits of the new approach**:
- Automatic version detection from `config.yaml`
- Correct tag format for HA discovery
- Multi-arch builds handled automatically
- Proper metadata and labels
- Better integration with HA ecosystem

## References

- [Home Assistant Builder](https://github.com/home-assistant/builder)
- [Home Assistant Add-on Development](https://developers.home-assistant.io/docs/add-ons)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [GitHub Actions Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
