"""Tests for client.py — BlancoApiClient, compute_dev_id, and _jwt_expires_at."""

from __future__ import annotations

import base64
import json
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from blanco_smart_home_api_client.client import BlancoApiClient, _jwt_expires_at
from blanco_smart_home_api_client.errors import (
    BlancoAuthError,
    BlancoTokenExpiredError,
)

AUTH_RESPONSE = {
    "results": [{"token": "renewed-token", "token_type": "Bearer", "dev_type": 2}],
    "info": {},
}
SYSTEM_RESPONSE = {"results": [{"dev_name": "My BLANCO"}], "info": {}}


# ── Test helpers ─────────────────────────────────────────────────────────────


def _make_jwt(exp_offset: int) -> str:
    """Return a minimal unsigned JWT with exp = now + exp_offset seconds."""
    header = (
        base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode()
    )
    payload = (
        base64.urlsafe_b64encode(
            json.dumps({"exp": int(time.time()) + exp_offset}).encode()
        )
        .rstrip(b"=")
        .decode()
    )
    return f"{header}.{payload}."


def _make_response(status: int, json_data: dict | None = None) -> MagicMock:
    """Return an async context-manager mock simulating an aiohttp response."""
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_data or {})
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=resp)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _make_session(get_responses=(), post_responses=()) -> MagicMock:
    """Return a mock aiohttp session with independent GET/POST response queues."""
    session = MagicMock()
    session.get = MagicMock(side_effect=list(get_responses))
    session.post = MagicMock(side_effect=list(post_responses))
    return session


# ── compute_dev_id ───────────────────────────────────────────────────────────


class TestComputeDevId:
    """Tests for BlancoApiClient.compute_dev_id."""

    def test_is_deterministic(self) -> None:
        """The same inputs always produce the same dev_id."""
        assert BlancoApiClient.compute_dev_id(
            "SN123", "CODE456"
        ) == BlancoApiClient.compute_dev_id("SN123", "CODE456")

    def test_matches_plain_concatenated_sha256(self) -> None:
        """The digest is sha256 of the plain, undelimited "{serial}{service_code}".

        Must match what BLANCO Cloud/the UNIT app derive for the same pair — see the
        docstring on compute_dev_id for why this is not free to change to a delimited
        (collision-safe) form despite this codebase's general canonical-form rule.
        """
        import hashlib

        expected = hashlib.sha256(b"SN123CODE456").hexdigest()
        assert BlancoApiClient.compute_dev_id("SN123", "CODE456") == expected

    def test_boundary_split_collides_by_design(self) -> None:
        """("A", "12") and ("A1", "2") DO collide — matches BLANCO's own derivation.

        This is the accepted trade-off documented on compute_dev_id, not an oversight.
        """
        assert BlancoApiClient.compute_dev_id(
            "A", "12"
        ) == BlancoApiClient.compute_dev_id("A1", "2")


# ── _jwt_expires_at ──────────────────────────────────────────────────────────


class TestJwtExpiresAt:
    """Tests for the _jwt_expires_at helper."""

    def test_valid_jwt_returns_exp_timestamp(self) -> None:
        """A well-formed JWT returns its exp claim as a float."""
        token = _make_jwt(3600)
        expires_at = _jwt_expires_at(token)
        assert expires_at > time.time()

    def test_expired_jwt_returns_past_timestamp(self) -> None:
        """An expired JWT's exp claim is in the past."""
        token = _make_jwt(-3600)
        assert _jwt_expires_at(token) < time.time()

    def test_non_jwt_returns_inf(self) -> None:
        """A plain bearer token (no dots) returns infinity."""
        assert _jwt_expires_at("plain-bearer-token") == float("inf")


# ── Automatic renewal ────────────────────────────────────────────────────────


class TestAutomaticRenewal:
    """Tests for the proactive/reactive token renewal built into device data calls."""

    async def test_proactive_renewal_before_expired_jwt(self) -> None:
        """An already-expired JWT is renewed before the device GET is made."""
        session = _make_session(
            get_responses=[_make_response(200, SYSTEM_RESPONSE)],
            post_responses=[_make_response(200, AUTH_RESPONSE)],
        )
        renewed: list[tuple[str, str]] = []
        client = BlancoApiClient(
            session,
            app_id="app1",
            token=_make_jwt(-10),
            dev_id="dev1",
            on_token_renewed=lambda t, tt: renewed.append((t, tt)),
        )
        status, _ = await client.get_device_system("dev1")

        assert status == 200
        assert renewed == [("renewed-token", "Bearer")]
        session.post.assert_called_once()
        session.get.assert_called_once()

    async def test_reactive_renewal_after_401(self) -> None:
        """A 401 on the device GET triggers one renew-and-retry."""
        session = _make_session(
            get_responses=[
                _make_response(401, {}),
                _make_response(200, SYSTEM_RESPONSE),
            ],
            post_responses=[_make_response(200, AUTH_RESPONSE)],
        )
        client = BlancoApiClient(
            session, app_id="app1", token="plain-bearer-token", dev_id="dev1"
        )
        status, _ = await client.get_device_system("dev1")

        assert status == 200
        assert session.get.call_count == 2

    async def test_renewal_failure_propagates(self) -> None:
        """When renewal itself fails, the resulting BlancoApiError propagates."""
        session = _make_session(
            get_responses=[_make_response(401, {})],
            post_responses=[_make_response(401, {})],
        )
        client = BlancoApiClient(
            session, app_id="app1", token="plain-bearer-token", dev_id="dev1"
        )

        with pytest.raises(BlancoAuthError):
            await client.get_device_system("dev1")

    async def test_no_dev_id_configured_401_propagates_without_renewal(self) -> None:
        """Without a configured dev_id, a 401 raises without attempting renewal."""
        session = _make_session(get_responses=[_make_response(401, {})])
        client = BlancoApiClient(session, app_id="app1", token="plain-bearer-token")

        with pytest.raises(BlancoTokenExpiredError):
            await client.get_device_system("dev1")
        session.post.assert_not_called()
