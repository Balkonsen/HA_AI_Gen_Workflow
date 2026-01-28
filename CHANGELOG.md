# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
