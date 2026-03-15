#!/usr/bin/env python3
"""
Home Assistant Configuration Export Tool
Exports complete HA configuration with sensitive data sanitization
Creates AI-friendly export with strict separation: ai_upload/ and secrets/

Export Structure:
  export_YYYYMMDD_HHMMSS/
  ├── ai_upload/                    # SAFE TO UPLOAD TO AI
  │   ├── ha_context.md             # Single consolidated context file
  │   ├── ha_entities.json          # All entity IDs (compact)
  │   ├── ha_config.yaml            # Merged config (sanitized)
  │   └── ha_automations.yaml       # All automations (sanitized)
  └── secrets/                      # NEVER SHARE
      └── secrets_map.json          # Secret value mappings
"""

import os
import sys
import json
import tarfile
import hashlib
import re
import subprocess
from datetime import datetime
import shutil

# Script version - increment when making incompatible changes
SCRIPT_VERSION = "2.0.0"  # v2.0: Added --config-dir support

# Maximum file size for AI upload (in bytes) - 10MB default
MAX_AI_FILE_SIZE = 10 * 1024 * 1024


def _load_supervisor_token_from_env_file() -> str:
    """Load SUPERVISOR_TOKEN from common .env locations."""
    candidates = [
        os.path.join(os.environ.get("HA_INSTALL_DIR", ""), ".env"),
        os.path.join(os.getcwd(), ".env"),
        "/usr/local/ha-ai-workflow/.env",
        os.path.expanduser("~/.ha-ai-workflow.env"),
    ]
    for env_file in candidates:
        if not env_file or not os.path.exists(env_file):
            continue
        try:
            with open(env_file, "r", encoding="utf-8") as handle:
                for line in handle:
                    if line.startswith("SUPERVISOR_TOKEN="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            continue
    return ""


class HAConfigExporter:
    def __init__(self, output_dir="/tmp/ha_export", config_dir=None, ha_url=None):  # nosec B108
        self.output_dir = output_dir
        self.config_dir = config_dir or os.environ.get("HA_CONFIG_DIR", os.environ.get("HA_CONFIG_PATH", "/config"))
        self.secrets_map = {}
        self.secret_counter = 0
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.export_name = f"ha_config_export_{self.timestamp}"
        self._update_paths()

        # Collected data for AI context generation
        self.entities_data = {}
        self.devices_data = {}
        self.automations_data = []
        self.scripts_data = []
        self.integrations_data = {}
        self.system_info = {}
        self.config_files = {}

        # HA API configuration for fallback data retrieval
        self.api_token = os.environ.get("SUPERVISOR_TOKEN") or _load_supervisor_token_from_env_file()
        self.ha_url = ha_url or os.environ.get("HA_URL")

        # Determine API mode: external (standalone) or internal (add-on)
        self._is_external_mode = bool(self.ha_url)
        if self._is_external_mode:
            # External mode: Use HA URL with /api/hassio prefix
            self._api_base_url = f"{self.ha_url}/api"
            self._supervisor_base_url = f"{self.ha_url}/api/hassio"
        else:
            # Internal mode: Use supervisor endpoints (add-on)
            self._api_base_url = "http://supervisor/core/api"
            self._supervisor_base_url = "http://supervisor"

        # Patterns to identify sensitive data
        self.sensitive_patterns = {
            "password": r'password["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)',
            "token": r'token["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)',
            "api_key": r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)',
            "secret": r'secret["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)',
            "webhook": r'webhook["\']?\s*[:=]\s*["\']?(https?://[^"\'}\s,]+)',
            "latitude": r'latitude["\']?\s*[:=]\s*["\']?(-?\d+\.\d+)',
            "longitude": r'longitude["\']?\s*[:=]\s*["\']?(-?\d+\.\d+)',
            "email": r"[\w\.-]+@[\w\.-]+\.\w+",
            "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "mac_address": r"\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b",
            "ssid": r'ssid["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)',
            "username": r'username["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)',
        }

        # HA paths to export (use config_dir for dynamic resolution)
        self.config_paths = {
            "config": self.config_dir,
            "addons": os.environ.get("HA_ADDONS_DIR", "/data/addons"),
            "supervisor": os.environ.get("HA_SUPERVISOR_DIR", "/data/supervisor"),
        }

    def _update_paths(self):
        """Update derived paths from export_name. Must be called after changing export_name."""
        self.export_path = os.path.join(self.output_dir, self.export_name)
        self.ai_upload_path = os.path.join(self.export_path, "ai_upload")
        self.secrets_path = os.path.join(self.export_path, "secrets")

    def create_export_structure(self):
        """Create export directory structure with strict AI/Secrets separation"""
        print(f"Creating export structure: {self.export_path}")
        os.makedirs(self.export_path, exist_ok=True)

        # AI Upload folder - safe to share with AI assistants
        os.makedirs(self.ai_upload_path, exist_ok=True)

        # Secrets folder - NEVER share
        os.makedirs(self.secrets_path, exist_ok=True)

        # Create .gitignore in secrets folder
        with open(os.path.join(self.secrets_path, ".gitignore"), "w") as f:
            f.write("# Never commit secrets\n*\n!.gitignore\n")

    def _api_request(self, endpoint):
        """Make an authenticated request to the HA Supervisor API.

        Args:
            endpoint: API endpoint path (e.g., '/addons', '/supervisor/info')

        Returns:
            JSON response or None on error
        """
        if not self.api_token:
            return None
        try:
            # Use appropriate base URL based on mode (external vs internal)
            url = f"{self._supervisor_base_url}{endpoint}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            import requests

            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    def _export_entities_via_api(self):
        """Fallback: export entity data via HA API /api/states."""
        try:
            import requests

            url = f"{self._api_base_url}/states"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                print(f"  API returned status {response.status_code}")
                return False

            states = response.json()
            self.entities_data["total_entities"] = len(states)
            for state in states:
                entity_id = state.get("entity_id", "")
                domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
                self.entities_data["all_entity_ids"].append(entity_id)
                if domain not in self.entities_data["entities_by_domain"]:
                    self.entities_data["entities_by_domain"][domain] = []
                self.entities_data["entities_by_domain"][domain].append(entity_id)
                self.entities_data["entity_details"].append(
                    {
                        "entity_id": entity_id,
                        "domain": domain,
                        "platform": "unknown",
                        "name": state.get("attributes", {}).get("friendly_name"),
                        "disabled": False,
                    }
                )

            print(f"✓ Collected {len(states)} entities via API")
            print(f"  - Domains: {len(self.entities_data['entities_by_domain'])}")
            return True
        except Exception as e:
            print(f"  Error fetching entities via API: {e}")
            return False

    def _export_addons_via_api(self):
        """Fallback: export add-on data via Supervisor API."""
        addon_data = {"installed_addons": []}
        result = self._api_request("/addons")
        if result and "data" in result and "addons" in result["data"]:
            for addon in result["data"]["addons"]:
                addon_data["installed_addons"].append(
                    {
                        "slug": addon.get("slug", ""),
                        "name": addon.get("name", ""),
                        "version": addon.get("version", ""),
                        "state": addon.get("state", ""),
                    }
                )
            self.integrations_data["addons"] = addon_data
            print(f"✓ Collected {len(addon_data['installed_addons'])} add-ons via API")
            return True
        return False

    def _export_entity_states_via_api(self):
        """Fallback: export entity states via HA API /api/states."""
        try:
            import requests

            url = f"{self._api_base_url}/states"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                print(f"  API returned status {response.status_code}")
                return False

            states = response.json()
            state_values = {}
            for state in states:
                entity_id = state.get("entity_id", "")
                if entity_id:
                    state_values[entity_id] = {
                        "state": state.get("state", ""),
                        "attributes": state.get("attributes", {}),
                    }

            self.entities_data["entity_states"] = state_values
            print(f"✓ Collected {len(state_values)} entity states via API")
            return True
        except Exception as e:
            print(f"  Error fetching entity states via API: {e}")
            return False

    def run_command(self, cmd):
        """Run command and return output."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), 1

    def generate_secret_placeholder(self, secret_type, value):
        """Generate unique placeholder for sensitive data"""
        if value in self.secrets_map:
            return self.secrets_map[value]

        self.secret_counter += 1
        placeholder = f"<<{secret_type.upper()}_{self.secret_counter}>>"
        self.secrets_map[value] = placeholder
        return placeholder

    def sanitize_text(self, text, filename=""):
        """Replace sensitive data with placeholders"""
        if not isinstance(text, str):
            return text

        sanitized = text

        # Apply all sensitive patterns
        for secret_type, pattern in self.sensitive_patterns.items():
            matches = re.finditer(pattern, sanitized, re.IGNORECASE)
            for match in matches:
                original_value = match.group(1) if match.groups() else match.group(0)
                # Skip obvious placeholders and examples
                skip_tokens = ["placeholder", "xxx", "***"]
                if secret_type != "email":
                    skip_tokens.append("example")
                if any(x in original_value.lower() for x in skip_tokens):
                    continue
                if len(original_value) < 3:  # Skip very short matches
                    continue
                placeholder = self.generate_secret_placeholder(secret_type, original_value)
                sanitized = sanitized.replace(original_value, placeholder)

        return sanitized

    def export_yaml_file(self, source_path, dest_path):
        """Export and sanitize YAML file"""
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                content = f.read()

            sanitized = self.sanitize_text(content, os.path.basename(source_path))

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(sanitized)

            return True
        except Exception as e:
            print(f"  Error exporting {source_path}: {e}")
            return False

    def export_json_file(self, source_path, dest_path):
        """Export and sanitize JSON file"""
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                content = f.read()

            sanitized = self.sanitize_text(content, os.path.basename(source_path))

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(sanitized)

            return True
        except Exception as e:
            print(f"  Error exporting {source_path}: {e}")
            return False

    def export_entities_registry(self):
        """Export entities from core.entity_registry - stores in memory for AI context"""
        print("\n=== Exporting Entity Registry ===")
        entity_registry_path = os.path.join(self.config_dir, ".storage", "core.entity_registry")

        self.entities_data = {
            "total_entities": 0,
            "entities_by_domain": {},
            "entities_by_platform": {},
            "disabled_entities": [],
            "all_entity_ids": [],  # Compact list of just IDs
            "entity_details": [],  # Detailed info
        }

        if os.path.exists(entity_registry_path):
            try:
                with open(entity_registry_path, "r") as f:
                    registry = json.load(f)

                entities = registry.get("data", {}).get("entities", [])
                self.entities_data["total_entities"] = len(entities)

                for entity in entities:
                    entity_id = entity.get("entity_id", "")
                    domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
                    platform = entity.get("platform", "unknown")

                    # Add to compact ID list
                    self.entities_data["all_entity_ids"].append(entity_id)

                    # Detailed entity info
                    entity_detail = {
                        "entity_id": entity_id,
                        "domain": domain,
                        "platform": platform,
                        "name": entity.get("name"),
                        "original_name": entity.get("original_name"),
                        "disabled": entity.get("disabled_by") is not None,
                        "hidden": entity.get("hidden_by") is not None,
                        "device_id": entity.get("device_id"),
                        "device_class": entity.get("original_device_class"),
                    }
                    self.entities_data["entity_details"].append(entity_detail)

                    # Count by domain
                    if domain not in self.entities_data["entities_by_domain"]:
                        self.entities_data["entities_by_domain"][domain] = []
                    self.entities_data["entities_by_domain"][domain].append(entity_id)

                    # Count by platform
                    if platform not in self.entities_data["entities_by_platform"]:
                        self.entities_data["entities_by_platform"][platform] = []
                    self.entities_data["entities_by_platform"][platform].append(entity_id)

                    # Track disabled
                    if entity.get("disabled_by"):
                        self.entities_data["disabled_entities"].append(entity_id)

                print(f"✓ Collected {self.entities_data['total_entities']} entities")
                print(
                    f"  - Active: {self.entities_data['total_entities'] - len(self.entities_data['disabled_entities'])}"
                )
                print(f"  - Disabled: {len(self.entities_data['disabled_entities'])}")
                print(f"  - Domains: {len(self.entities_data['entities_by_domain'])}")

                return True
            except PermissionError:
                print("  ⚠ Permission denied reading entity registry")
                if self.api_token:
                    return self._export_entities_via_api()
                print("    Set SUPERVISOR_TOKEN for API fallback")
                return False
            except Exception as e:
                print(f"  Error exporting entity registry: {e}")
                return False
        elif self.api_token:
            return self._export_entities_via_api()
        else:
            print("  Entity registry not found (set SUPERVISOR_TOKEN for API fallback)")
            return False

    def export_entity_states(self):
        """Export current entity states from core.restore_state"""
        print("\n=== Exporting Entity States ===")
        restore_state_path = os.path.join(self.config_dir, ".storage", "core.restore_state")

        states_data = {
            "total_states": 0,
            "states_by_domain": {},
            "state_values": {},
        }  # entity_id -> state value

        if os.path.exists(restore_state_path):
            try:
                with open(restore_state_path, "r") as f:
                    restore_data = json.load(f)

                states = restore_data.get("data", [])
                states_data["total_states"] = len(states)

                for state_entry in states:
                    state = state_entry.get("state", {})
                    entity_id = state.get("entity_id", "")

                    if not entity_id:
                        continue

                    domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
                    state_value = state.get("state", "")

                    # Store state value
                    states_data["state_values"][entity_id] = {
                        "state": state_value,
                        "attributes": state.get("attributes", {}),
                    }

                    # Count by domain
                    if domain not in states_data["states_by_domain"]:
                        states_data["states_by_domain"][domain] = 0
                    states_data["states_by_domain"][domain] += 1

                # Merge states into entities_data
                self.entities_data["entity_states"] = states_data["state_values"]

                print(f"✓ Collected {states_data['total_states']} entity states")
                return True
            except PermissionError:
                print("  ⚠ Permission denied reading entity states file")
                print("    Ensure the process has read access to .storage/ or set SUPERVISOR_TOKEN")
            except Exception as e:
                print(f"  Error exporting entity states: {e}")
                return False

        # Fallback to API if file not available and token is set
        if self.api_token:
            return self._export_entity_states_via_api()
        else:
            print("  Entity states file not found (set SUPERVISOR_TOKEN for API fallback)")
            return False

    def export_device_registry(self):
        """Export devices from core.device_registry - stores in memory for AI context"""
        print("\n=== Exporting Device Registry ===")
        device_registry_path = os.path.join(self.config_dir, ".storage", "core.device_registry")

        self.devices_data = {
            "total_devices": 0,
            "devices_by_manufacturer": {},
            "devices_by_integration": {},
            "device_list": [],  # Compact device info
        }

        if os.path.exists(device_registry_path):
            try:
                with open(device_registry_path, "r") as f:
                    registry = json.load(f)

                devices = registry.get("data", {}).get("devices", [])
                self.devices_data["total_devices"] = len(devices)

                for device in devices:
                    manufacturer = device.get("manufacturer", "Unknown")

                    # Get primary integration
                    identifiers = device.get("identifiers", [])
                    integration = identifiers[0][0] if identifiers and len(identifiers[0]) > 0 else "unknown"

                    device_info = {
                        "id": device.get("id"),
                        "name": self.sanitize_text(device.get("name", "")),
                        "manufacturer": manufacturer,
                        "model": device.get("model"),
                        "integration": integration,
                    }
                    self.devices_data["device_list"].append(device_info)

                    # Count by manufacturer
                    if manufacturer not in self.devices_data["devices_by_manufacturer"]:
                        self.devices_data["devices_by_manufacturer"][manufacturer] = 0
                    self.devices_data["devices_by_manufacturer"][manufacturer] += 1

                    # Count by integration
                    if integration not in self.devices_data["devices_by_integration"]:
                        self.devices_data["devices_by_integration"][integration] = 0
                    self.devices_data["devices_by_integration"][integration] += 1

                print(f"✓ Collected {self.devices_data['total_devices']} devices")
                print(f"  - Manufacturers: {len(self.devices_data['devices_by_manufacturer'])}")
                print(f"  - Integrations: {len(self.devices_data['devices_by_integration'])}")

                return True
            except PermissionError:
                print("  ⚠ Permission denied reading device registry")
                print("    Ensure the process has read access to .storage/ or set SUPERVISOR_TOKEN")
                return False
            except Exception as e:
                print(f"  Error exporting device registry: {e}")
                return False
        else:
            if self.api_token:
                print("  Device registry not found, no device API available in HA REST API")
            else:
                print("  Device registry not found (set SUPERVISOR_TOKEN for API fallback)")
            return False

    def export_config_directory(self):
        """Export main configuration directory - collects automations/scripts for AI context"""
        print("\n=== Exporting Configuration Files ===")
        config_dir = self.config_dir

        # Files to exclude
        exported_count = 0

        # Collect automations
        automations_path = os.path.join(config_dir, "automations.yaml")
        if os.path.exists(automations_path):
            try:
                with open(automations_path, "r", encoding="utf-8") as f:
                    content = f.read()
                sanitized = self.sanitize_text(content)
                self.config_files["automations"] = sanitized
                exported_count += 1
            except Exception as e:
                print(f"  Warning: Could not read automations.yaml: {e}")

        # Collect scripts
        scripts_path = os.path.join(config_dir, "scripts.yaml")
        if os.path.exists(scripts_path):
            try:
                with open(scripts_path, "r", encoding="utf-8") as f:
                    content = f.read()
                sanitized = self.sanitize_text(content)
                self.config_files["scripts"] = sanitized
                exported_count += 1
            except Exception as e:
                print(f"  Warning: Could not read scripts.yaml: {e}")

        # Collect scenes
        scenes_path = os.path.join(config_dir, "scenes.yaml")
        if os.path.exists(scenes_path):
            try:
                with open(scenes_path, "r", encoding="utf-8") as f:
                    content = f.read()
                sanitized = self.sanitize_text(content)
                self.config_files["scenes"] = sanitized
                exported_count += 1
            except Exception as e:
                print(f"  Warning: Could not read scenes.yaml: {e}")

        # Collect main configuration
        main_config_path = os.path.join(config_dir, "configuration.yaml")
        if os.path.exists(main_config_path):
            try:
                with open(main_config_path, "r", encoding="utf-8") as f:
                    content = f.read()
                sanitized = self.sanitize_text(content)
                self.config_files["configuration"] = sanitized
                exported_count += 1
            except Exception as e:
                print(f"  Warning: Could not read configuration.yaml: {e}")

        # Collect packages
        packages_dir = os.path.join(config_dir, "packages")
        if os.path.exists(packages_dir):
            packages_content = []
            for root, dirs, files in os.walk(packages_dir):
                for file in files:
                    if file.endswith((".yaml", ".yml")):
                        try:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, packages_dir)
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            sanitized = self.sanitize_text(content)
                            packages_content.append(f"# --- {rel_path} ---\n{sanitized}")
                            exported_count += 1
                        except Exception as e:
                            print(f"  Warning: Could not read {file}: {e}")
            if packages_content:
                self.config_files["packages"] = "\n\n".join(packages_content)

        # Collect custom components manifest
        custom_comp_dir = os.path.join(config_dir, "custom_components")
        if os.path.exists(custom_comp_dir):
            custom_components = []
            for comp in os.listdir(custom_comp_dir):
                manifest_path = os.path.join(custom_comp_dir, comp, "manifest.json")
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, "r") as f:
                            manifest = json.load(f)
                        custom_components.append(
                            {
                                "domain": manifest.get("domain", comp),
                                "name": manifest.get("name", comp),
                                "version": manifest.get("version", "unknown"),
                            }
                        )
                    except (OSError, TypeError, ValueError, json.JSONDecodeError):
                        custom_components.append({"domain": comp})
            self.config_files["custom_components"] = custom_components

        print(f"✓ Collected {exported_count} configuration files")

    def export_addon_configs(self):
        """Export add-on configurations - stores in memory for AI context"""
        print("\n=== Exporting Add-on Configurations ===")

        addon_data = {
            "installed_addons": [],
        }

        # Get list of installed add-ons via CLI
        stdout, _, code = self.run_command(["ha", "addons", "--raw-json"])
        try:
            addons_info = json.loads(stdout) if code == 0 and stdout.strip() else {}
            if "data" in addons_info and "addons" in addons_info["data"]:
                for addon in addons_info["data"]["addons"]:
                    addon_data["installed_addons"].append(
                        {
                            "slug": addon.get("slug", ""),
                            "name": addon.get("name", ""),
                            "version": addon.get("version", ""),
                            "state": addon.get("state", ""),
                        }
                    )
        except Exception:
            pass

        # Fallback to API if CLI returned no add-ons
        if not addon_data["installed_addons"] and self.api_token:
            if self._export_addons_via_api():
                return

        self.integrations_data["addons"] = addon_data
        print(f"✓ Collected {len(addon_data['installed_addons'])} add-on configurations")

    def collect_system_info(self):
        """Collect system diagnostic information - stores in memory for AI context"""
        print("\n=== Collecting System Information ===")

        self.system_info = {
            "ha_version": "unknown",
            "supervisor_version": "unknown",
            "installation_type": "unknown",
        }

        # Get HA version via CLI
        stdout, _, code = self.run_command(["ha", "core", "info", "--raw-json"])
        if code == 0:
            try:
                info = json.loads(stdout)
                self.system_info["ha_version"] = info.get("data", {}).get("version", "unknown")
            except Exception:
                pass

        # Get supervisor version via CLI
        stdout, _, code = self.run_command(["ha", "supervisor", "info", "--raw-json"])
        if code == 0:
            try:
                info = json.loads(stdout)
                self.system_info["supervisor_version"] = info.get("data", {}).get("version", "unknown")
                self.system_info["installation_type"] = "Home Assistant OS/Supervised"
            except Exception:
                pass

        # Fallback to API if CLI did not provide info
        if self.system_info["ha_version"] == "unknown" and self.api_token:
            result = self._api_request("/core/info")
            if result and "data" in result:
                self.system_info["ha_version"] = result["data"].get("version", "unknown")
        if self.system_info["supervisor_version"] == "unknown" and self.api_token:
            result = self._api_request("/supervisor/info")
            if result and "data" in result:
                self.system_info["supervisor_version"] = result["data"].get("version", "unknown")
                self.system_info["installation_type"] = "Home Assistant OS/Supervised"

        print(f"✓ Collected system info (HA {self.system_info['ha_version']})")

    def export_integrations_info(self):
        """Export information about configured integrations - stores in memory"""
        print("\n=== Exporting Integrations Information ===")

        # Check .storage for integration configs
        storage_path = os.path.join(self.config_dir, ".storage")
        if os.path.exists(storage_path):
            core_config_entries = os.path.join(storage_path, "core.config_entries")
            if os.path.exists(core_config_entries):
                try:
                    with open(core_config_entries, "r") as f:
                        config_entries = json.load(f)

                    integrations = []
                    for entry in config_entries.get("data", {}).get("entries", []):
                        integrations.append(
                            {
                                "domain": entry.get("domain", ""),
                                "title": entry.get("title", ""),
                            }
                        )
                    self.integrations_data["configured"] = integrations
                    print(f"✓ Found {len(integrations)} integrations")
                except Exception as e:
                    print(f"  Warning: Could not read config entries: {e}")

        # Custom components already collected in export_config_directory
        custom_count = len(self.config_files.get("custom_components", []))
        if custom_count:
            print(f"✓ Found {custom_count} custom components")

    def save_secrets_map(self):
        """Save the secrets mapping file to secrets/ folder"""
        print("\n=== Saving Secrets Mapping ===")

        # Create reverse map for easier lookup
        reverse_map = {v: k for k, v in self.secrets_map.items()}

        secrets_data = {
            "export_timestamp": self.timestamp,
            "total_secrets": len(self.secrets_map),
            "secrets": reverse_map,
            "instructions": {
                "usage": "Use the import script to restore these secrets",
                "format": "Each placeholder maps to the original sensitive value",
                "security": "Store this file securely and NEVER share or upload to AI",
            },
        }

        secrets_file = os.path.join(self.secrets_path, "secrets_map.json")
        with open(secrets_file, "w") as f:
            json.dump(secrets_data, f, indent=2)

        print(f"✓ Saved {len(self.secrets_map)} secret mappings to secrets/secrets_map.json")
        print("⚠️  IMPORTANT: Keep secrets/ folder secure - NEVER upload to AI!")

    def generate_ai_context_file(self):
        """Generate consolidated AI context markdown file"""
        print("\n=== Generating AI Context File ===")

        active_entities = self.entities_data.get("total_entities", 0) - len(
            self.entities_data.get("disabled_entities", [])
        )
        addons_count = len(self.integrations_data.get("addons", {}).get("installed_addons", []))

        # Build the context markdown
        context = f"""# Home Assistant Configuration Context
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
HA Version: {self.system_info.get('ha_version', 'unknown')}

## System Overview

| Metric | Value |
|--------|-------|
| Total Entities | {self.entities_data.get('total_entities', 0)} |
| Active Entities | {active_entities} |
| Disabled Entities | {len(self.entities_data.get('disabled_entities', []))} |
| Total Devices | {self.devices_data.get('total_devices', 0)} |
| Integrations | {len(self.integrations_data.get('configured', []))} |
| Add-ons | {addons_count} |

## Entity Domains

"""
        # Add entity domain breakdown
        domains = self.entities_data.get("entities_by_domain", {})
        sorted_domains = sorted(domains.items(), key=lambda x: len(x[1]), reverse=True)
        for domain, entities in sorted_domains[:15]:
            context += f"- **{domain}**: {len(entities)} entities\n"
        if len(sorted_domains) > 15:
            context += f"- ... and {len(sorted_domains) - 15} more domains\n"

        # Add device manufacturers
        context += "\n## Device Manufacturers\n\n"
        manufacturers = self.devices_data.get("devices_by_manufacturer", {})
        sorted_mfrs = sorted(manufacturers.items(), key=lambda x: x[1], reverse=True)
        for mfr, count in sorted_mfrs[:10]:
            context += f"- **{mfr}**: {count} devices\n"

        # Add integrations
        context += "\n## Configured Integrations\n\n"
        integrations = self.integrations_data.get("configured", [])
        for integration in integrations[:20]:
            context += f"- {integration.get('domain', 'unknown')}: {integration.get('title', '')}\n"
        if len(integrations) > 20:
            context += f"- ... and {len(integrations) - 20} more integrations\n"

        # Add custom components
        custom_comps = self.config_files.get("custom_components", [])
        if custom_comps:
            context += "\n## Custom Components\n\n"
            for comp in custom_comps:
                context += f"- {comp.get('name', comp.get('domain', 'unknown'))} (v{comp.get('version', '?')})\n"

        # Add add-ons
        addons = self.integrations_data.get("addons", {}).get("installed_addons", [])
        if addons:
            context += "\n## Installed Add-ons\n\n"
            for addon in addons:
                context += f"- {addon.get('name', addon.get('slug', 'unknown'))} ({addon.get('state', 'unknown')})\n"

        # Add configuration files section
        context += "\n---\n\n## Configuration Files\n\n"
        context += "The following configuration files are included in `ha_config.yaml`:\n"
        for key in self.config_files:
            if key != "custom_components":
                context += f"- {key}.yaml\n"

        context += """
---

## How to Use This Export

1. **Upload to AI**: Upload files from `ai_upload/` folder to your AI assistant
2. **Ask Questions**: Reference entity IDs, automations, or request new configurations
3. **Import Results**: Use the import tool to apply AI-generated configurations

### Recommended Files to Upload:
- `ha_context.md` - This file (system overview)
- `ha_entities.json` - Complete entity list with IDs
- `ha_config.yaml` - Automations, scripts, and configuration

### File Size Guide:
- Claude: Max 30MB per file, 100MB total
- ChatGPT: Max 512MB per file
- Gemini: Max 2GB per file

---

## Security Notice

✅ All files in `ai_upload/` are sanitized and safe to share with AI
❌ NEVER share the `secrets/` folder with anyone or any AI

Sensitive data has been replaced with placeholders like `<<PASSWORD_1>>`, `<<TOKEN_2>>`, etc.
"""

        # Write context file
        context_file = os.path.join(self.ai_upload_path, "ha_context.md")
        with open(context_file, "w", encoding="utf-8") as f:
            f.write(context)

        file_size = os.path.getsize(context_file)
        print(f"✓ Generated ha_context.md ({file_size / 1024:.1f} KB)")

    def generate_ai_entities_file(self):
        """Generate compact entities JSON file for AI upload"""
        print("\n=== Generating Entities File ===")

        # Create compact entities export
        entities_export = {
            "export_date": self.timestamp,
            "total_entities": self.entities_data.get("total_entities", 0),
            "entities_by_domain": {},
            "all_entity_ids": self.entities_data.get("all_entity_ids", []),
        }

        # Add domain breakdown with entity IDs
        for domain, entity_ids in self.entities_data.get("entities_by_domain", {}).items():
            entities_export["entities_by_domain"][domain] = {
                "count": len(entity_ids),
                "entity_ids": entity_ids,
            }

        # Add entity states if available
        if "entity_states" in self.entities_data:
            entities_export["entity_states"] = self.entities_data["entity_states"]

        # Write compact JSON (no indent to save space)
        entities_file = os.path.join(self.ai_upload_path, "ha_entities.json")

        # First try compact, if too large use minimal format
        json_content = json.dumps(entities_export, separators=(",", ":"))

        if len(json_content) > MAX_AI_FILE_SIZE:
            # Too large - create minimal version with just entity IDs
            print("  ⚠ Full entities file too large, creating minimal version")
            minimal_export = {
                "total_entities": entities_export["total_entities"],
                "all_entity_ids": entities_export["all_entity_ids"],
                "domains": {k: v["count"] for k, v in entities_export["entities_by_domain"].items()},
            }
            json_content = json.dumps(minimal_export, separators=(",", ":"))

        with open(entities_file, "w", encoding="utf-8") as f:
            f.write(json_content)

        file_size = os.path.getsize(entities_file)
        print(f"✓ Generated ha_entities.json ({file_size / 1024:.1f} KB)")

    def generate_ai_config_file(self):
        """Generate consolidated config YAML file for AI upload"""
        print("\n=== Generating Config File ===")

        # Combine all config files into one
        combined_config = []

        if "configuration" in self.config_files:
            combined_config.append("# ====== CONFIGURATION.YAML ======\n")
            combined_config.append(self.config_files["configuration"])
            combined_config.append("\n")

        if "automations" in self.config_files:
            combined_config.append("\n# ====== AUTOMATIONS.YAML ======\n")
            combined_config.append(self.config_files["automations"])
            combined_config.append("\n")

        if "scripts" in self.config_files:
            combined_config.append("\n# ====== SCRIPTS.YAML ======\n")
            combined_config.append(self.config_files["scripts"])
            combined_config.append("\n")

        if "scenes" in self.config_files:
            combined_config.append("\n# ====== SCENES.YAML ======\n")
            combined_config.append(self.config_files["scenes"])
            combined_config.append("\n")

        if "packages" in self.config_files:
            combined_config.append("\n# ====== PACKAGES ======\n")
            combined_config.append(self.config_files["packages"])
            combined_config.append("\n")

        config_content = "".join(combined_config)

        # Check file size
        if len(config_content) > MAX_AI_FILE_SIZE:
            print(f"  ⚠ Config file too large ({len(config_content) / 1024 / 1024:.1f}MB), truncating")
            # Prioritize automations, truncate rest
            truncated_config = []
            if "automations" in self.config_files:
                truncated_config.append("# ====== AUTOMATIONS.YAML ======\n")
                truncated_config.append(self.config_files["automations"][: MAX_AI_FILE_SIZE // 2])
            if "scripts" in self.config_files:
                remaining = MAX_AI_FILE_SIZE - len("".join(truncated_config))
                truncated_config.append("\n# ====== SCRIPTS.YAML (truncated) ======\n")
                truncated_config.append(self.config_files["scripts"][: remaining // 2])
            config_content = "".join(truncated_config)

        config_file = os.path.join(self.ai_upload_path, "ha_config.yaml")
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_content)

        file_size = os.path.getsize(config_file)
        print(f"✓ Generated ha_config.yaml ({file_size / 1024:.1f} KB)")

    def create_metadata(self):
        """Create export metadata and README files"""
        print("\n=== Creating Metadata ===")

        # Calculate file sizes
        ai_upload_size = sum(
            os.path.getsize(os.path.join(self.ai_upload_path, f))
            for f in os.listdir(self.ai_upload_path)
            if os.path.isfile(os.path.join(self.ai_upload_path, f))
        )

        metadata = {
            "export_version": "2.0",
            "export_timestamp": self.timestamp,
            "export_date": datetime.now().isoformat(),
            "total_secrets_replaced": len(self.secrets_map),
            "ai_upload_size_kb": ai_upload_size / 1024,
            "structure": {
                "ai_upload/": "SAFE TO UPLOAD - Sanitized files for AI assistants",
                "secrets/": "NEVER SHARE - Contains sensitive data mappings",
            },
            "files": {
                "ha_context.md": "System overview and entity statistics",
                "ha_entities.json": "Complete entity IDs and states",
                "ha_config.yaml": "Consolidated configuration files",
            },
        }

        with open(os.path.join(self.export_path, "METADATA.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        # Create README in export root
        readme = f"""# Home Assistant AI Export
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Export Version: 2.0

## 📁 Export Structure

```
{self.export_name}/
├── ai_upload/          ← UPLOAD THESE TO AI
│   ├── ha_context.md       System overview ({ai_upload_size / 1024:.0f} KB total)
│   ├── ha_entities.json    All entity IDs
│   └── ha_config.yaml      Automations & config
│
└── secrets/            ← NEVER SHARE!
    └── secrets_map.json    Secret value mappings
```

## ✅ Safe to Upload (ai_upload/)

Upload ALL files from `ai_upload/` to your AI assistant:
- **Claude**: Supports .md, .json, .yaml (max 30MB/file)
- **ChatGPT**: Supports .md, .json, .yaml (max 512MB/file)
- **Gemini**: Supports .md, .json, .yaml (max 2GB/file)

Total AI upload size: **{ai_upload_size / 1024:.1f} KB**

## ❌ Never Share (secrets/)

The `secrets/` folder contains mappings of sensitive data.
Placeholders like `<<PASSWORD_1>>` in the AI files map to real values here.

## 📊 Export Statistics

- **Entities**: {self.entities_data.get('total_entities', 0)}
- **Devices**: {self.devices_data.get('total_devices', 0)}
- **Secrets Replaced**: {len(self.secrets_map)}
- **Domains**: {len(self.entities_data.get('entities_by_domain', {}))}

## 🤖 Using with AI

1. Upload files from `ai_upload/` to your AI assistant
2. Ask questions like:
   - "Create an automation using sensor.temperature"
   - "Design a dashboard for my lights"
   - "Help me optimize my automations"
3. Use the import script to apply AI suggestions

## 🔄 Restoration

To restore secrets after AI generates new configs:
```bash
python3 ha_config_import.py --source <ai_output> --secrets secrets/secrets_map.json
```
"""

        with open(os.path.join(self.export_path, "README.md"), "w") as f:
            f.write(readme)

        # Create README in ai_upload folder
        ai_readme = """# AI Upload Files

These files are sanitized and safe to upload to AI assistants.

## Files

1. **ha_context.md** - Start here! Overview of your HA setup
2. **ha_entities.json** - Complete list of all entity IDs
3. **ha_config.yaml** - Your automations, scripts, and configuration

## Upload Instructions

### Claude
1. Click the attachment icon
2. Select all files from this folder
3. Start your conversation

### ChatGPT
1. Click the attachment icon in the chat
2. Upload files one at a time or together
3. Reference them in your prompt

### Gemini
1. Click "Add file" in the prompt area
2. Select files to upload
3. Ask your questions

## What's Sanitized

- Passwords → `<<PASSWORD_N>>`
- API Keys → `<<API_KEY_N>>`
- Tokens → `<<TOKEN_N>>`
- IP Addresses → `<<IP_ADDRESS_N>>`
- Coordinates → `<<LATITUDE_N>>`, `<<LONGITUDE_N>>`
- Emails → `<<EMAIL_N>>`
"""

        with open(os.path.join(self.ai_upload_path, "README.md"), "w") as f:
            f.write(ai_readme)

    def create_tarball(self):
        """Create compressed tarballs - separate for AI upload and full export"""
        print("\n=== Creating Export Archives ===")

        # Create AI-only tarball (small, for easy upload)
        ai_tarball_path = f"{self.output_dir}/{self.export_name}_ai_upload.tar.gz"
        with tarfile.open(ai_tarball_path, "w:gz") as tar:
            tar.add(self.ai_upload_path, arcname="ai_upload")

        ai_size_kb = os.path.getsize(ai_tarball_path) / 1024
        print(f"✓ Created AI upload archive: {ai_tarball_path}")
        print(f"  Size: {ai_size_kb:.1f} KB")

        # Create full tarball (includes secrets)
        full_tarball_path = f"{self.output_dir}/{self.export_name}.tar.gz"
        with tarfile.open(full_tarball_path, "w:gz") as tar:
            tar.add(self.export_path, arcname=self.export_name)

        full_size_mb = os.path.getsize(full_tarball_path) / (1024 * 1024)

        with open(full_tarball_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        print(f"✓ Created full archive: {full_tarball_path}")
        print(f"  Size: {full_size_mb:.2f} MB")
        print(f"  SHA256: {file_hash}")

        return full_tarball_path, ai_tarball_path

    def cleanup_temp_files(self):
        """Remove temporary export directory"""
        try:
            shutil.rmtree(self.export_path)
        except OSError:
            pass

    def run(self):
        """Execute full export process with AI-friendly output"""
        print("=" * 70)
        print("Home Assistant Configuration Export Tool v2.0")
        print("AI-Friendly Export with Strict Separation")
        print("=" * 70)

        try:
            # Phase 1: Create structure
            self.create_export_structure()

            # Phase 2: Collect data (stores in memory)
            self.export_config_directory()
            self.export_addon_configs()
            self.export_entities_registry()
            self.export_entity_states()
            self.export_device_registry()
            self.collect_system_info()
            self.export_integrations_info()

            # Phase 3: Generate AI-friendly files
            self.generate_ai_context_file()
            self.generate_ai_entities_file()
            self.generate_ai_config_file()

            # Phase 4: Save secrets separately
            self.save_secrets_map()

            # Phase 5: Create metadata and archives
            self.create_metadata()
            full_tarball, ai_tarball = self.create_tarball()

            # Phase 6: Cleanup temp files (keep export folder)
            # self.cleanup_temp_files()  # Don't cleanup - user may want to browse

            print("\n" + "=" * 70)
            print("✓ Export Complete!")
            print("=" * 70)

            print(f"\n📁 Export Location: {self.export_path}")
            print("\n📤 AI Upload Files:")
            print(f"   {self.ai_upload_path}/")
            for f in os.listdir(self.ai_upload_path):
                fpath = os.path.join(self.ai_upload_path, f)
                if os.path.isfile(fpath):
                    size_kb = os.path.getsize(fpath) / 1024
                    print(f"   └── {f} ({size_kb:.1f} KB)")

            print("\n🔒 Secrets Location (NEVER SHARE):")
            print(f"   {self.secrets_path}/secrets_map.json")

            print("\n📦 Archives Created:")
            print(f"   AI Upload Only: {ai_tarball}")
            print(f"   Full Export:    {full_tarball}")

            print("\n🚀 Next Steps:")
            print("   1. Upload files from ai_upload/ to your AI assistant")
            print("   2. Ask AI to help with automations, dashboards, etc.")
            print("   3. Use import script to apply AI-generated configs")

            print("\n⚠️  Security Reminder:")
            print("   NEVER upload secrets/ folder to AI!")

            return full_tarball

        except Exception as e:
            print(f"\n✗ Export failed: {e}")
            import traceback

            traceback.print_exc()
            return None


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Export Home Assistant configuration with sanitization",
        epilog=f"Version: {SCRIPT_VERSION}",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {SCRIPT_VERSION}")
    parser.add_argument("--output-dir", default="/tmp/ha_export", help="Output directory for export")  # nosec B108
    parser.add_argument("--name", help="Custom export name")
    parser.add_argument(
        "--config-dir",
        default=None,
        help="HA config directory (default: $HA_CONFIG_DIR or /config)",
    )
    parser.add_argument("--quiet", action="store_true", help="Minimize output")

    args = parser.parse_args()

    # Show version info at start
    if not args.quiet:
        print(f"HA Diagnostic Export v{SCRIPT_VERSION}")
        print()

    config_dir = args.config_dir or os.environ.get("HA_CONFIG_DIR", os.environ.get("HA_CONFIG_PATH", "/config"))

    geteuid = getattr(os, "geteuid", None)
    if callable(geteuid) and geteuid() != 0 and not args.quiet:
        print("⚠️  Warning: Running without root privileges")
        print("   Some system information may not be accessible")
        print()

    # Check if config directory exists
    if not os.path.exists(config_dir):
        print(f"✗ Error: Config directory not found: {config_dir}")
        print("  This script must be run on a Home Assistant host")
        print("  Set HA_CONFIG_DIR or use --config-dir to specify the path")
        sys.exit(1)

    # Check .storage readability
    storage_dir = os.path.join(config_dir, ".storage")
    if os.path.exists(storage_dir) and not os.access(storage_dir, os.R_OK):
        if not args.quiet:
            print(f"⚠️  Warning: Cannot read {storage_dir} (permission denied)")
            if os.environ.get("SUPERVISOR_TOKEN"):
                print("   Will use SUPERVISOR_TOKEN API fallback for entity/device data")
            else:
                print("   Set SUPERVISOR_TOKEN environment variable for API fallback")
            print()

    # Create exporter with args
    output_dir = args.output_dir
    exporter = HAConfigExporter(output_dir=output_dir, config_dir=config_dir)
    if args.name:
        exporter.export_name = args.name
        exporter._update_paths()

    result = exporter.run()

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
