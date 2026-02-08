"""
Unit tests for ha_api_client.py
Tests the HomeAssistantAPI class with dual-mode support (internal/external).
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add bin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

from ha_api_client import HomeAssistantAPI


class TestHomeAssistantAPIInitialization:
    """Test HomeAssistantAPI initialization and mode detection"""

    def test_init_internal_mode_with_supervisor_token(self):
        """Test initialization in internal mode (add-on) with SUPERVISOR_TOKEN"""
        with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token"}):
            api = HomeAssistantAPI()

            assert api._token == "test_token"
            assert api._is_external_mode is False
            assert api._api_url == "http://supervisor/core/api"
            assert api._supervisor_url == "http://supervisor"

    def test_init_internal_mode_with_explicit_token(self):
        """Test initialization in internal mode with explicit token"""
        api = HomeAssistantAPI(token="explicit_token")

        assert api._token == "explicit_token"
        assert api._is_external_mode is False
        assert api._api_url == "http://supervisor/core/api"
        assert api._supervisor_url == "http://supervisor"

    def test_init_external_mode_with_ha_url(self):
        """Test initialization in external mode (standalone) with ha_url"""
        api = HomeAssistantAPI(token="test_token", ha_url="http://192.168.1.100:8123")

        assert api._token == "test_token"
        assert api._is_external_mode is True
        assert api._api_url == "http://192.168.1.100:8123/api"
        assert api._supervisor_url == "http://192.168.1.100:8123/api/hassio"

    def test_init_external_mode_with_env_ha_url(self):
        """Test initialization in external mode with HA_URL environment variable"""
        with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test_token", "HA_URL": "http://homeassistant.local:8123"}):
            api = HomeAssistantAPI()

            assert api._token == "test_token"
            assert api._is_external_mode is True
            assert api._api_url == "http://homeassistant.local:8123/api"
            assert api._supervisor_url == "http://homeassistant.local:8123/api/hassio"

    def test_init_external_mode_https(self):
        """Test initialization in external mode with HTTPS URL"""
        api = HomeAssistantAPI(token="test_token", ha_url="https://ha.example.com:8123")

        assert api._token == "test_token"
        assert api._is_external_mode is True
        assert api._api_url == "https://ha.example.com:8123/api"
        assert api._supervisor_url == "https://ha.example.com:8123/api/hassio"

    def test_init_without_token_logs_warning(self, caplog):
        """Test that initialization without token logs a warning"""
        with patch.dict(os.environ, clear=True):
            api = HomeAssistantAPI()

            assert api._token is None
            assert api.is_available is False

    def test_is_available_with_token(self):
        """Test is_available property returns True with token"""
        api = HomeAssistantAPI(token="test_token")
        assert api.is_available is True

    def test_is_available_without_token(self):
        """Test is_available property returns False without token"""
        with patch.dict(os.environ, clear=True):
            api = HomeAssistantAPI()
            assert api.is_available is False


class TestHomeAssistantAPIEndpoints:
    """Test API endpoint URL construction in different modes"""

    def test_get_addons_internal_mode(self):
        """Test get_addons uses correct endpoint in internal mode"""
        with patch("requests.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"addons": []}}
            mock_request.return_value = mock_response

            api = HomeAssistantAPI(token="test_token")
            api.get_addons()

            # Verify correct endpoint was called
            call_args = mock_request.call_args
            assert call_args[0][1] == "http://supervisor/addons"

    def test_get_addons_external_mode(self):
        """Test get_addons uses correct endpoint in external mode"""
        with patch("requests.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"addons": []}}
            mock_request.return_value = mock_response

            api = HomeAssistantAPI(token="test_token", ha_url="http://192.168.1.100:8123")
            api.get_addons()

            # Verify correct endpoint was called (matches example script)
            call_args = mock_request.call_args
            assert call_args[0][1] == "http://192.168.1.100:8123/api/hassio/addons"

    def test_get_supervisor_info_internal_mode(self):
        """Test get_supervisor_info uses correct endpoint in internal mode"""
        with patch("requests.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"version": "2024.1.0"}}
            mock_request.return_value = mock_response

            api = HomeAssistantAPI(token="test_token")
            api.get_supervisor_info()

            call_args = mock_request.call_args
            assert call_args[0][1] == "http://supervisor/supervisor/info"

    def test_get_supervisor_info_external_mode(self):
        """Test get_supervisor_info uses correct endpoint in external mode"""
        with patch("requests.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"version": "2024.1.0"}}
            mock_request.return_value = mock_response

            api = HomeAssistantAPI(token="test_token", ha_url="http://192.168.1.100:8123")
            api.get_supervisor_info()

            call_args = mock_request.call_args
            assert call_args[0][1] == "http://192.168.1.100:8123/api/hassio/supervisor/info"

    def test_get_states_internal_mode(self):
        """Test get_states uses correct endpoint in internal mode"""
        with patch("requests.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_request.return_value = mock_response

            api = HomeAssistantAPI(token="test_token")
            api.get_states()

            call_args = mock_request.call_args
            assert call_args[0][1] == "http://supervisor/core/api/states"

    def test_get_states_external_mode(self):
        """Test get_states uses correct endpoint in external mode"""
        with patch("requests.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_request.return_value = mock_response

            api = HomeAssistantAPI(token="test_token", ha_url="http://192.168.1.100:8123")
            api.get_states()

            call_args = mock_request.call_args
            assert call_args[0][1] == "http://192.168.1.100:8123/api/states"


class TestHomeAssistantAPIHeaders:
    """Test API request headers"""

    def test_get_headers_includes_bearer_token(self):
        """Test that headers include Bearer token"""
        api = HomeAssistantAPI(token="test_token_123")
        headers = api._get_headers()

        assert headers["Authorization"] == "Bearer test_token_123"
        assert headers["Content-Type"] == "application/json"


class TestHomeAssistantAPIErrorHandling:
    """Test error handling in API client"""

    def test_request_without_token_returns_none(self):
        """Test that requests without token return None"""
        with patch.dict(os.environ, clear=True):
            api = HomeAssistantAPI()
            result = api.get_states()

            assert result is None

    def test_connection_timeout_returns_none(self):
        """Test that connection timeout returns None"""
        with patch("requests.request") as mock_request:
            import requests
            mock_request.side_effect = requests.exceptions.Timeout("Connection timeout")

            api = HomeAssistantAPI(token="test_token")
            result = api.get_states()

            assert result is None
