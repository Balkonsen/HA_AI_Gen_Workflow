# Changelog

## [1.0.5] - 2026-02-06

### Fixed
- **Docker build context alignment** — Dockerfile COPY paths now correctly reference addon-relative paths for HA builder compatibility (PR #40)
- **Path resolution** — Replaced hardcoded `/config/ai_exports` with `os.path.abspath()` for non-container environments (PR #41)
- **Export verifier** — Supports both v1.0 and v2.0 export formats with automatic version detection (PR #37)

### Added
- **CI/CD caching** — Docker layer caching via `--self-cache` and pip cache for faster builds (PR #43)
- **Automated self-learning** — Post-PR analysis engine captures lessons learned and applies improvements (PR #44)
- **Developer tooling** — Updated copilot-instructions.md with battle-tested lessons; added devcontainer (PR #42)

### Changed
- Version bump to trigger Home Assistant Supervisor update detection

## [1.0.4] - 2026-02-06

**BREAKING CHANGE**: This release removes support for 32-bit ARM (armv7) architectures to ensure compatibility with Home Assistant 2026.2.0 and later versions.

### Changed
- **Removed armv7 (32-bit ARM) architecture support** to comply with Home Assistant 2026.2.0+ requirements
  - Home Assistant officially dropped support for 32-bit systems starting with version 2026.2.0
  - Only 64-bit architectures are now supported: amd64 and aarch64
  - Users on 32-bit systems (e.g., Raspberry Pi 2/3/4 running 32-bit OS) must migrate to 64-bit OS or remain on older HA versions

### Fixed
- Version consistency across all add-on files (config.yaml, Dockerfile, build.yaml)
- Add-on update mechanism now properly recognized by Home Assistant 2026.2.0+

### Security
- **Updated cryptography package** from 41.0.0 to 42.0.4+ to fix critical vulnerabilities:
  - CVE-2024-0727: Bleichenbacher timing oracle attack
  - CVE-2024-26130: NULL pointer dereference in pkcs12.serialize_key_and_certificates
  - CVE-2023-38325: SSH certificate mishandling

### Migration Guide for 32-bit Users
If you are currently using this add-on on a 32-bit system:
1. Check if your hardware supports 64-bit operation (most Raspberry Pi 3/4/5 do)
2. Migrate to a 64-bit Home Assistant OS image (aarch64)
3. Restore your backup after migration
4. The add-on will then be available for installation/update

**Note**: If you cannot migrate to 64-bit, you must remain on Home Assistant 2025.12 or earlier, which is the last version supporting 32-bit systems.

## [1.0.3] - 2026-01-28 (Late afternoon)

**Note**: This is the third rapid bug fix release today, addressing critical startup and UI accessibility issues discovered after initial release.

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

## [1.0.2] - 2026-01-28 (Afternoon)

**Note**: This is a critical bug fix release addressing the s6-overlay error discovered immediately after v1.0.1.

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

## [1.0.1] - 2026-01-28 (Morning)

**Note**: Initial patch release fixing startup error.

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
