# Changelog

## [1.0.3] - 2026-01-28

### Fixed
- **CRITICAL FIX**: Resolved "404 Not Found" error when accessing add-on web UI through Home Assistant Ingress
  - Added `--server.enableWebsocketCompression=false` flag to Streamlit configuration
  - This flag is required for Streamlit 1.10+ to work correctly behind reverse proxies and Home Assistant's Ingress
  - The internal URL shown in logs (`http://0.0.0.0:8501/...`) is now correctly handled by the Ingress proxy

### Documentation
- Added troubleshooting section explaining the 404 error and its resolution
- Clarified that SSH server is NOT required for add-on usage
- Explained that SSH is only needed for remote Home Assistant instances
- Documented that the URL shown in logs is internal and should not be accessed directly
- Added instructions to access the add-on through Home Assistant's sidebar or "Open Web UI" button

## [1.0.2] - 2026-01-28

### Fixed
- **CRITICAL FIX**: Completely resolved "s6-overlay-suexec: fatal: can only run as pid 1" error
  - Removed dependency on s6-overlay bashio functions
  - Rewrote run.sh to use standard bash instead of `#!/usr/bin/with-contenv bashio`
  - Script now works with `init: false` setting without conflicts

### Added
- Comprehensive logging system with color-coded output (INFO, WARNING, ERROR, DEBUG)
- Debug mode and verbose mode configuration options
- Multiple failsafe mechanisms:
  - Automatic jq installation if missing
  - Config file fallback from `/data/options.json` to `/config/options.json`
  - Default values for all configuration options
  - Directory creation with elevated permissions fallback
  - Streamlit installation fallback
  - Multiple ingress URL detection methods
  - API connectivity retry mechanism (3 attempts)
- Enhanced error handling throughout the script
- Detailed debug logging for troubleshooting
- Better startup feedback with clear progress indicators

### Changed
- Configuration reading now uses native bash + jq instead of bashio
- Ingress URL detection now has 3 fallback methods
- API connectivity testing now retries up to 3 times
- All logging functions replaced with custom implementations
- Script is now fully self-contained and doesn't require s6-overlay

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
