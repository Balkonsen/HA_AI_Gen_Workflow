# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Docker Image Build Process** - Replaced manual Docker build with Home Assistant official builder
  - Switched to `home-assistant/builder@2025.11.0` GitHub Action
  - Ensures proper image tagging and metadata for Home Assistant discovery
  - Home Assistant can now correctly detect and install add-on updates
  - Automatic version detection from config.yaml
  - Proper integration with Home Assistant's add-on update mechanism
  - Documented in new `docs/BUILD_AND_RELEASE.md` guide
- **Export Verification** - Fixed verifier to support both v1.0 and v2.0 export formats
  - v2.0 exports now correctly verified (ai_upload/, secrets/ structure)
  - Backward compatibility maintained for v1.0 exports (config/, diagnostics/ structure)
  - Automatic format detection from METADATA.json
  - Export workflow now completes successfully without false failures

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
