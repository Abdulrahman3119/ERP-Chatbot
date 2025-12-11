from dataclasses import dataclass
from typing import Dict, Optional

import requests

from app.config import Settings


@dataclass
class IDOClient:
    """HTTP client for IDO REST API."""

    settings: Settings

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": (
                f"token {self.settings.erpnext_api_key}:"
                f"{self.settings.erpnext_api_secret}"
            ),
            "Content-Type": "application/json",
        }

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Perform a GET request against IDO with basic error handling."""
        url = f"{self.settings.erpnext_base_url}{endpoint}"
        try:
            response = requests.get(
                url,
                params=params,
                headers=self._headers(),
                timeout=self.settings.request_timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as exc:
            raise TimeoutError(
                f"Request timeout while accessing {endpoint}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(
                f"IDO API error: {exc}"
            ) from exc

    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Perform a POST request against IDO with basic error handling."""
        url = f"{self.settings.erpnext_base_url}{endpoint}"
        try:
            response = requests.post(
                url,
                json=data,
                headers=self._headers(),
                timeout=self.settings.request_timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as exc:
            raise TimeoutError(
                f"Request timeout while accessing {endpoint}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(
                f"IDO API error: {exc}"
            ) from exc

