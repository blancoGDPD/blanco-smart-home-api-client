"""API stage configuration and endpoint constants for the BLANCO Smart Home API.

Defines BlancoApiStage, the per-stage key/URL table, and the resolved
API_KEY / API_BASE_URL / endpoint constants used by BlancoApiClient.

To switch between the production and development API environments, change
ACTIVE_STAGE to BlancoApiStage.PROD or BlancoApiStage.DEV.
"""

from __future__ import annotations

from enum import Enum


class BlancoApiStage(Enum):
    """Deployment stage selecting the target API environment."""

    DEFAULT = "default"
    """Alias for the production environment — used when no explicit stage is configured."""
    PROD = "prod"
    """Production API environment."""
    DEV = "dev"
    """Development / staging API environment."""


# Maps each BlancoApiStage to its corresponding API key and base URL.
_STAGE_CONFIG: dict[BlancoApiStage, dict[str, str]] = {
    BlancoApiStage.DEFAULT: {
        "api_key": "u8GGIsN64z1WaQId9n2Qu3XITlXTnomx78p0fKAu",
        "api_base_url": "https://smart-home-api.prod.ddi-backend.blanco.com",
    },
    BlancoApiStage.PROD: {
        "api_key": "u8GGIsN64z1WaQId9n2Qu3XITlXTnomx78p0fKAu",
        "api_base_url": "https://smart-home-api.prod.ddi-backend.blanco.com",
    },
    BlancoApiStage.DEV: {
        "api_key": "SxvZiPiH6s9AAWgY7nfy87tDOk5o51wM6QcLDhn7",
        "api_base_url": "https://smart-home-api.dev.ddi-backend.blanco.com",
    },
}

# ── Active stage — change this value to switch environments ───────────────────

ACTIVE_STAGE: BlancoApiStage = BlancoApiStage.DEFAULT
"""Currently active deployment stage. Change to BlancoApiStage.DEV or BlancoApiStage.PROD to switch environments."""

# Resolved configuration dict for the active stage, falling back to DEFAULT.
_active_stage_config = _STAGE_CONFIG.get(
    ACTIVE_STAGE, _STAGE_CONFIG[BlancoApiStage.DEFAULT]
)

API_KEY = _active_stage_config["api_key"]
"""API key for the active stage, sent in the X-Api-Key request header."""
API_BASE_URL = _active_stage_config["api_base_url"]
"""Base URL of the BLANCO Smart Home API for the active stage."""
API_AUTH_ENDPOINT = "/auth/token"
"""Endpoint for device authentication and token issuance (POST)."""
API_DEVICES_ENDPOINT = "/devices"
"""Base path for device data endpoints (system, status, settings, errors, actions)."""
API_APP_REGISTRATIONS_ENDPOINT = "/apps/registrations"
"""Endpoint for registering, updating, and deregistering app instances."""
