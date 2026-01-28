#!/usr/bin/env python3
"""
Home Assistant API Client for Add-on Integration.

This module provides secure access to the Home Assistant API using the
SUPERVISOR_TOKEN that is automatically injected into add-on containers.

Security Notes:
- SUPERVISOR_TOKEN is provided by the Supervisor and should never be logged
- All API calls use Bearer token authentication
- This module only works when running as a Home Assistant add-on
"""

import logging
import os
from typing import Any

import requests

_LOGGER = logging.getLogger(__name__)

# API endpoints (internal to HA Supervisor network)
HA_API_URL = os.environ.get("HA_API_URL", "http://supervisor/core/api")
SUPERVISOR_URL = os.environ.get("HA_SUPERVISOR_URL", "http://supervisor")


class HomeAssistantAPI:
    """Client for interacting with Home Assistant API from an add-on."""

    def __init__(self, token: str | None = None):
        """Initialize the HA API client.

        Args:
            token: Optional SUPERVISOR_TOKEN. If not provided, reads from environment.
        """
        self._token = token or os.environ.get("SUPERVISOR_TOKEN")
        self._api_url = HA_API_URL
        self._supervisor_url = SUPERVISOR_URL

        if not self._token:
            _LOGGER.warning("SUPERVISOR_TOKEN not available. " "HA API calls will fail unless running as an add-on.")

    @property
    def is_available(self) -> bool:
        """Check if the API token is available."""
        return bool(self._token)

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """Make an authenticated request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            **kwargs: Additional arguments passed to requests

        Returns:
            JSON response or None on error
        """
        if not self._token:
            _LOGGER.error("Cannot make API request: SUPERVISOR_TOKEN not available")
            return None

        try:
            response = requests.request(
                method,
                url,
                headers=self._get_headers(),
                timeout=30,
                **kwargs,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            _LOGGER.error("API request timed out: %s", url)
        except requests.exceptions.HTTPError as err:
            _LOGGER.error("API request failed: %s - %s", url, err)
        except requests.exceptions.RequestException as err:
            _LOGGER.error("API request error: %s - %s", url, err)
        except ValueError as err:
            _LOGGER.error("Invalid JSON response: %s", err)

        return None

    # -------------------------------------------------------------------------
    # Home Assistant Core API Methods
    # -------------------------------------------------------------------------

    def get_config(self) -> dict[str, Any] | None:
        """Get Home Assistant configuration."""
        return self._request("GET", f"{self._api_url}/config")

    def check_config(self) -> dict[str, Any] | None:
        """Check Home Assistant configuration for errors.

        Returns:
            Dict with 'result' key: 'valid' or 'invalid', and 'errors' if invalid
        """
        return self._request("POST", f"{self._api_url}/config/core/check_config")

    def restart_core(self) -> bool:
        """Restart Home Assistant Core.

        Returns:
            True if restart initiated successfully
        """
        result = self._request("POST", f"{self._api_url}/services/homeassistant/restart")
        return result is not None

    def get_states(self) -> list[dict[str, Any]] | None:
        """Get all entity states."""
        return self._request("GET", f"{self._api_url}/states")

    def get_state(self, entity_id: str) -> dict[str, Any] | None:
        """Get state of a specific entity."""
        return self._request("GET", f"{self._api_url}/states/{entity_id}")

    def call_service(
        self,
        domain: str,
        service: str,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Call a Home Assistant service.

        Args:
            domain: Service domain (e.g., 'light', 'switch')
            service: Service name (e.g., 'turn_on', 'turn_off')
            data: Optional service data

        Returns:
            True if service call succeeded
        """
        result = self._request(
            "POST",
            f"{self._api_url}/services/{domain}/{service}",
            json=data or {},
        )
        return result is not None

    # -------------------------------------------------------------------------
    # Supervisor API Methods
    # -------------------------------------------------------------------------

    def get_supervisor_info(self) -> dict[str, Any] | None:
        """Get Supervisor information."""
        return self._request("GET", f"{self._supervisor_url}/supervisor/info")

    def get_core_info(self) -> dict[str, Any] | None:
        """Get Home Assistant Core information."""
        return self._request("GET", f"{self._supervisor_url}/core/info")

    def get_addons(self) -> dict[str, Any] | None:
        """Get list of installed add-ons."""
        return self._request("GET", f"{self._supervisor_url}/addons")

    def get_addon_info(self, slug: str) -> dict[str, Any] | None:
        """Get information about a specific add-on."""
        return self._request("GET", f"{self._supervisor_url}/addons/{slug}/info")

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def test_connection(self) -> tuple[bool, str]:
        """Test connection to Home Assistant API.

        Returns:
            Tuple of (success, message)
        """
        if not self._token:
            return False, "SUPERVISOR_TOKEN not available"

        try:
            response = requests.get(
                f"{self._api_url}/config",
                headers=self._get_headers(),
                timeout=10,
            )
            if response.status_code == 200:
                return True, "Connection successful"
            return False, f"API returned status {response.status_code}"
        except requests.exceptions.RequestException as err:
            return False, f"Connection failed: {err}"


# Singleton instance for easy access
_api_instance: HomeAssistantAPI | None = None


def get_ha_api() -> HomeAssistantAPI:
    """Get the Home Assistant API client instance.

    Returns:
        HomeAssistantAPI instance
    """
    global _api_instance
    if _api_instance is None:
        _api_instance = HomeAssistantAPI()
    return _api_instance
