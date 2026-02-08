# Version and CHANGELOG Management

## The Simple Rule (Works Through 1.0.6)

**When you bump the version, update the CHANGELOG immediately in the same PR.**

That's it. No complex validation, no automation needed.

## How It Works

### 1. Before Making Changes

Current state:
- `ha_ai_workflow_addon/config.yaml` has `version: "1.0.14"`
- `CHANGELOG.md` has a section `## [1.0.14] - 2026-02-08`

### 2. When Making a PR

If your PR requires a version bump:

```bash
# Edit config.yaml
version: "1.0.15"  # Bump version

# Edit CHANGELOG.md - Add NEW section at top (after [Unreleased])
## [1.0.15] - 2026-02-XX

### Fixed
- **Your fix description** — What you fixed and why (PR #XX)

### Added  
- **Your new feature** — What you added (PR #XX)

### Changed
- **Your change** — What you changed (PR #XX)
```

### 3. Real Examples (What Worked)

**Version 1.0.6:**
```markdown
## [1.0.6] - 2026-02-06

### Fixed
- **Docker build not triggered on version bump** — Fixed `docker-build.yml` race condition (PR #46)
- **Lessons learned pushing to wrong branch** — Fixed workflow to push to PR target branch (PR #46)
- **Workflow concurrency** — Added concurrency group to prevent race conditions
```

**Version 1.0.5:**
```markdown
## [1.0.5] - 2026-02-06

### Fixed
- **Docker build context alignment** — Dockerfile COPY paths now addon-relative (PR #40)
- **Path resolution** — Replaced hardcoded paths with `os.path.abspath()` (PR #41)
- **Export verifier** — Supports both v1.0 and v2.0 formats (PR #37)

### Added
- **CI/CD caching** — Docker layer caching via `--self-cache` (PR #43)
- **Lessons Learned Engine** — Automated self-learning improvement loop
```

## What NOT to Do

❌ **Don't bump version without CHANGELOG entry:**
```yaml
# config.yaml
version: "1.0.15"  # Changed

# CHANGELOG.md - Still says 1.0.14 as latest
## [1.0.14] - 2026-02-08  # ← This causes desync!
```

❌ **Don't use generic placeholders:**
```markdown
## [1.0.15] - 2026-02-XX

### Changed
- Version bump  # ← Too vague! What actually changed?
```

## Checklist for Version Bumps

Before merging a PR that changes `ha_ai_workflow_addon/config.yaml`:

- [ ] Updated `version` in `config.yaml`
- [ ] Added corresponding `## [X.X.X]` section in `CHANGELOG.md`
- [ ] Listed actual changes with **bold descriptions**
- [ ] Referenced PR numbers where applicable
- [ ] Used proper categories (Fixed/Added/Changed/Removed/Security)
- [ ] Added today's date (or PR merge date)

## Why This Works

1. **Simple** - One rule, easy to remember
2. **Manual** - Humans know what changed, automation doesn't
3. **Descriptive** - Forces you to write what you did
4. **Synchronous** - Version bump and CHANGELOG update happen together
5. **Proven** - Worked perfectly through versions 1.0.0 to 1.0.6

## When Things Go Wrong

If versions 1.0.7-1.0.13 got out of sync, just backfill them once (like we did in PR #52) and then **follow the simple rule** going forward.

---

**Remember:** The CHANGELOG is for users and future maintainers. Make it helpful.
