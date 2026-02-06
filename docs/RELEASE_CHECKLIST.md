# Quick Reference: Releasing a New Version

This is a quick checklist for releasing a new version of the HA AI Gen Workflow add-on.

## Pre-Release Checklist

- [ ] All changes tested locally
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated with changes

## Release Steps

### 1. Update Version Numbers

Edit these files to update the version (e.g., from `1.0.4` to `1.0.5`):

**File: `ha_ai_workflow_addon/config.yaml`**
```yaml
version: "1.0.5"  # Line 2
```

**File: `ha_ai_workflow_addon/Dockerfile`**
```dockerfile
io.hass.version="1.0.5" \  # Line 56
```

### 2. Update CHANGELOG

**File: `ha_ai_workflow_addon/CHANGELOG.md`**
```markdown
## 1.0.5 - YYYY-MM-DD

### Added
- New feature description

### Changed
- Changed feature description

### Fixed
- Bug fix description
```

**File: `CHANGELOG.md` (root)**
Move unreleased changes to a new version section:
```markdown
## [1.0.5] - YYYY-MM-DD

### Added
- Feature descriptions from [Unreleased]

## [Unreleased]
(empty for now)
```

### 3. Commit and Push

```bash
git add ha_ai_workflow_addon/config.yaml \
        ha_ai_workflow_addon/Dockerfile \
        ha_ai_workflow_addon/CHANGELOG.md \
        CHANGELOG.md

git commit -m "Release version 1.0.5"
git push origin main
```

### 4. Create Git Tag (Optional but Recommended)

```bash
git tag -a v1.0.5 -m "Release version 1.0.5"
git push origin v1.0.5
```

### 5. Monitor Build

1. Go to: https://github.com/Balkonsen/HA_AI_Gen_Workflow/actions
2. Watch the "Build and Publish Docker Images" workflow
3. Ensure all architectures build successfully (amd64, aarch64)
4. Build typically takes 10-15 minutes

### 6. Verify Publication

Check that images are published to GitHub Container Registry:

**View Packages:**
- amd64: https://github.com/Balkonsen/HA_AI_Gen_Workflow/pkgs/container/ha_ai_gen_workflow-amd64
- aarch64: https://github.com/Balkonsen/HA_AI_Gen_Workflow/pkgs/container/ha_ai_gen_workflow-aarch64

**Verify Tags:**
Both packages should have:
- Tag: `1.0.5` (your version)
- Tag: `latest`

### 7. Test in Home Assistant

1. **Add repository** (if not already added):
   - Settings → Add-ons → Add-on Store → ⋮ → Repositories
   - Add: `https://github.com/Balkonsen/HA_AI_Gen_Workflow`

2. **Check for update**:
   - Settings → Add-ons → Add-on Store → ⋮ → Check for updates
   - Refresh the page
   - Should see new version available

3. **Test installation**:
   - Install on a test instance if possible
   - Verify the add-on starts correctly
   - Check logs for errors

### 8. Announce Release (Optional)

- Create a GitHub Release from the tag
- Post to Home Assistant Community forum
- Update README if needed

## Troubleshooting

### Build Fails

**Check:**
1. GitHub Actions logs for error messages
2. Dockerfile syntax is correct
3. Base images are available
4. All dependencies can be installed

**Fix:**
1. Address the error in the logs
2. Commit the fix
3. Push to trigger a new build

### Home Assistant Not Showing Update

**Try:**
1. Settings → Add-ons → Add-on Store → ⋮ → Check for updates
2. Remove and re-add the repository
3. Clear browser cache
4. Check HA Supervisor logs

**Verify:**
1. Version in `config.yaml` is higher than current
2. Docker images exist in GHCR with correct tags
3. GitHub Actions workflow completed successfully

### Image Pull Fails

**Check:**
1. Images are public in GHCR (not private)
2. Image names match `config.yaml`
3. Architecture is supported (amd64 or aarch64)

## Quick Commands

```bash
# Check current version
grep "^version:" ha_ai_workflow_addon/config.yaml

# View recent workflow runs
gh run list --workflow=docker-build.yml --limit 5

# View latest workflow logs
gh run view --log

# List available tags
git tag -l

# View package in GHCR
gh api /users/Balkonsen/packages/container/ha_ai_gen_workflow-amd64/versions
```

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **Major** (x.0.0): Breaking changes, major features
- **Minor** (1.x.0): New features, backward compatible
- **Patch** (1.0.x): Bug fixes, minor changes

Examples:
- `1.0.4` → `1.0.5`: Bug fix or minor improvement
- `1.0.5` → `1.1.0`: New feature added
- `1.1.0` → `2.0.0`: Breaking change or major overhaul

## Files Modified in Each Release

Minimum required changes:
1. `ha_ai_workflow_addon/config.yaml` - version
2. `ha_ai_workflow_addon/Dockerfile` - io.hass.version label
3. `ha_ai_workflow_addon/CHANGELOG.md` - add-on changelog
4. `CHANGELOG.md` - project changelog

Optional but recommended:
5. Create git tag `vX.Y.Z`
6. Create GitHub Release

## Support

- **Documentation**: `docs/BUILD_AND_RELEASE.md`
- **Issues**: https://github.com/Balkonsen/HA_AI_Gen_Workflow/issues
- **Actions**: https://github.com/Balkonsen/HA_AI_Gen_Workflow/actions
