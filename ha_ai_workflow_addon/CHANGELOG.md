# Changelog

## [1.0.1] - 2026-01-28

### Fixed
- Fixed "s6-overlay-suexec: fatal: can only run as pid 1" error by adding `init: false` to config.yaml

## [1.0.0] - 2024-01-28

### Added
- Initial release of the HA AI Gen Workflow add-on
- Streamlit-based web UI for workflow management
- Export functionality with secrets sanitization
- AI context generation for AI assistants
- Import functionality with automatic secret restoration
- SSH support for remote Home Assistant instances
- Ingress support for Home Assistant panel integration
