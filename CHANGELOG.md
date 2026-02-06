# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.6] - 2026-02-06

### Fixed
- **Docker build not triggered on version bump** — Fixed `docker-build.yml` race condition where concurrent workflow runs could prevent the build from executing after PR merge (PR #46)
- **Lessons learned pushing to wrong branch** — Fixed `lessons-learned.yml` to explicitly push to the PR target branch instead of detached HEAD, which was creating commits on unrelated branches like `v1.1b1` (PR #46)
- **Workflow concurrency** — Added concurrency group to `docker-build.yml` to prevent race conditions between simultaneous pushes to main

## [1.0.5] - 2026-02-06

### Fixed
- **Docker build context alignment** — Dockerfile COPY paths now correctly reference addon-relative paths for HA builder compatibility (PR #40)
- **Path resolution** — Replaced hardcoded `/config/ai_exports` with `os.path.abspath()` for non-container environments (PR #41)
- **Export verifier** — Supports both v1.0 and v2.0 export formats with automatic version detection (PR #37)

### Added
- **CI/CD caching** — Docker layer caching via `--self-cache` and pip cache for faster builds (PR #43)
- **Lessons Learned Engine** — Automated self-learning improvement loop (`bin/lessons_learned.py`)
  - Analyzes PR diffs, test results, and lint output for patterns and anti-patterns
  - Captures structured lessons learned in `lessons_learned.json`
  - Validates repository against known lessons to detect regressions
  - Applies feasible improvements automatically (idempotent updates to docs/config)
  - CLI interface with `--scan`, `--report`, and post-PR analysis modes
- **Lessons Learned CI Workflow** — `.github/workflows/lessons-learned.yml`
  - Runs automatically after each merged PR on main/develop branches
  - Collects PR diff, test output, and lint results for analysis
  - Commits updated lessons back to the repository
  - Supports manual dispatch with scan-only mode
- **Comprehensive test suite** for lessons learned module (36 unit tests)
- **Developer tooling** — Updated copilot-instructions.md with battle-tested lessons; added devcontainer (PR #42)

### Changed
- Version bump to trigger Home Assistant Supervisor update detection

## [1.0.4] - 2026-02-06

**BREAKING CHANGE**: Removed support for 32-bit ARM (armv7) architectures

### Changed
- **Dropped armv7 (32-bit) architecture support** - Home Assistant 2026.2.0+ only supports 64-bit systems
  - Supported architectures: amd64, aarch64 (64-bit only)
  - Users on 32-bit systems must migrate to 64-bit OS or remain on HA 2025.12 or earlier

### Fixed
- Version synchronization across all add-on configuration files
- Add-on update mechanism compatibility with Home Assistant 2026.2.0+
- Ensures proper recognition and updates by Home Assistant Supervisor

### Security
- **Updated cryptography package** from 41.0.0 to 42.0.4+ to fix critical vulnerabilities:
  - CVE-2024-0727: Bleichenbacher timing oracle attack
  - CVE-2024-26130: NULL pointer dereference in pkcs12.serialize_key_and_certificates
  - CVE-2023-38325: SSH certificate mishandling
- Aligned with Home Assistant's security and support model for 2026+

## [1.0.0] - 2026-01-28

### Added
- **Home Assistant Add-on** — Native installation via HA Supervisor with sidebar integration
- **Streamlit Web GUI** — Full graphical interface for export/import workflow
- **SUPERVISOR_TOKEN Authentication** — Secure API access for add-on operations
- **Ingress Support** — Seamless integration into Home Assistant UI
- **Multi-architecture Support** — Builds for amd64, aarch64, and armv7

### Changed
- Primary installation method is now Home Assistant Add-on
- Simplified README focused on add-on usage
- Cleaned up repository structure (removed redundant files)

### Removed
- Windows PowerShell installer (deprecated in favor of add-on)
- Redundant SSH documentation files
- Duplicate README files

## [0.9.0] - 2026-01-15

### Added
- Complete pytest test suite for all Python modules
- Pre-commit hooks for code quality
- GitHub Actions CI/CD pipeline
- Docker testing environment
- VSCode integration (tasks, debugging, settings)
- Comprehensive developer documentation

### Security
- Bandit security scanning
- Secrets detection in pre-commit hooks
- Trivy vulnerability scanning in CI/CD

## [0.1.0] - 2024-01-01

### Added
- Initial release

[1.0.0]: https://github.com/Balkonsen/HA_AI_Gen_Workflow/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/Balkonsen/HA_AI_Gen_Workflow/compare/v0.1.0...v0.9.0
[0.1.0]: https://github.com/Balkonsen/HA_AI_Gen_Workflow/releases/tag/v0.1.0
