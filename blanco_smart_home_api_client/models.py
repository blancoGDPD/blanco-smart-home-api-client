"""Domain-model enums for the BLANCO Smart Home API client.

Defines the API-side enums shared across all library modules:
error severity levels, action types, and water dispense types.
"""

from __future__ import annotations

from enum import IntEnum


class BlancoErrorType(IntEnum):
    """Error severity types returned by the /errors endpoint."""

    UNDEF = 0
    """Unknown or unrecognised error type — used as a safe fallback."""
    CRITICAL = 1
    """Critical error — device operation is impaired and immediate attention is required."""
    WARNING = 2
    """Warning — device continues to operate but attention is recommended."""
    INFO = 3
    """Informational notice — no action required."""


class BlancoActionType(IntEnum):
    """Action types reported in the act_type field of the /actions endpoint."""

    UNDEF = 0
    """Unknown or unrecognised action type — used as a safe fallback."""

    # ── Common ────────────────────────────────────────────────────────────────
    PASSWORD_CHANGED = 1
    """Device password was changed."""
    REQUEST_CLOUD_ACCESS = 2
    """Cloud access was requested."""
    UPDATE_REJECTED = 3
    """A firmware or configuration update was rejected."""

    # ── SODA + AIO ────────────────────────────────────────────────────────────
    WATER_DISPENSE = 1000
    """Water was dispensed (SODA and AIO devices)."""
    CALIBRATION_DONE = 1001
    """Calibration procedure completed."""
    FILTER_CHANGE_DONE = 1002
    """Filter replacement was confirmed."""
    CO2_CHANGE_DONE = 1003
    """CO₂ cartridge replacement was confirmed."""

    # ── AQUA ──────────────────────────────────────────────────────────────────
    WATER_FLOW = 9000
    """Water was dispensed (AQUA devices — volume reported via wtr_flow)."""
    FILTER_CHANGED = 9001
    """Filter replacement was confirmed (AQUA devices)."""


class BlancoWaterType(IntEnum):
    """Water type dispensed by the device tap, as reported in the /actions endpoint."""

    UNDEF = 0
    """Unknown or unrecognised water type — used as a safe fallback."""
    STILL = 1
    """Still (non-carbonated) water."""
    MEDIUM = 2
    """Medium carbonation water."""
    CLASSIC = 3
    """Classic (fully carbonated) sparkling water."""
    HOT = 4
    """Hot water (AIO devices only)."""
