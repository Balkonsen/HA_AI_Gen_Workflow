---
name: ha-release-version-sync
description: 'Synchronize version changes with changelog and addon metadata for HA AI Gen Workflow. Use when bumping versions, preparing releases, or updating addon metadata files and release notes.'
---

# HA Release Version Sync

Use this skill to apply safe, consistent version updates with mandatory changelog synchronization.

## When to Use This Skill

- Bumping release version
- Preparing release PRs
- Updating add-on metadata
- Verifying version consistency across required files

## Mandatory Rule

When version is changed, changelog must be updated in the same change set.

## Required Files

- ha_ai_workflow_addon/config.yaml (source of truth)
- ha_ai_workflow_addon/build.yaml
- ha_ai_workflow_addon/Dockerfile labels (if version labels exist)
- CHANGELOG.md

## Workflow

### Step 1: Read Current Version

- Read current version from ha_ai_workflow_addon/config.yaml
- Treat this value as canonical source version

### Step 2: Apply New Version Consistently

- Update version in required metadata files
- Ensure exact string match across files

### Step 3: Update CHANGELOG

- Insert new section directly below "## [Unreleased]"
- Use format: "## [X.Y.Z] - YYYY-MM-DD"
- Add concrete entries under categories such as Fixed, Added, Changed, Removed, Security
- Avoid vague entries like "misc updates"

### Step 4: Consistency Verification

- Verify all required files now reference identical version
- Verify changelog section exists and is non-empty

### Step 5: Output Release Summary

- Old version and new version
- Files updated
- Changelog section header and categories used
- Any follow-up actions

## Quality Gates

- Gate 1: Version updated in all required metadata files
- Gate 2: CHANGELOG updated in same change set
- Gate 3: No version mismatches remain

If any gate fails, return FAIL with blocking fix steps.

## Reporting Format

1. Result: PASS or FAIL
2. Version delta: old -> new
3. Files changed: explicit paths
4. Changelog status: updated or missing
5. Next actions: fixes required

## Selectable Invocation Options

Use this numbered menu to choose a release-sync operation. Respond with just the option number when selecting.

1. Patch release sync (x.y.Z)
Context: Use for bugfix-only releases where metadata and changelog must be updated quickly and consistently.
Prompt: "Run option 1 for HA release version sync to bump patch version."

2. Minor release sync (x.Y.z)
Context: Use when adding features that require a structured changelog section with Added/Changed details.
Prompt: "Run option 2 for HA release version sync to bump minor version."

3. Major release sync (X.y.z)
Context: Use for breaking changes and full release-note discipline across required files.
Prompt: "Run option 3 for HA release version sync to bump major version."

4. Version consistency audit only (no edits)
Context: Use before release branching to detect mismatches between config, build metadata, and changelog.
Prompt: "Run option 4 for HA release version sync."

5. Changelog quality audit only (no version bump)
Context: Use during PR review to verify changelog format, placement, and specificity.
Prompt: "Run option 5 for HA release version sync."
