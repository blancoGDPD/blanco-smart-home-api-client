"""Domain-model enums for the BLANCO Smart Home API client.

Defines the API-side enums shared across all library modules: device types,
error severity levels, action types, and water dispense types.
"""

from __future__ import annotations

from enum import IntEnum


class BlancoDeviceType(IntEnum):
    """Device types returned in the dev_type field by /auth/token and device data endpoints."""

    UNDEF = 0
    """Unknown or unrecognised device type — used as a safe fallback."""
    SODA = 1
    """EVOL-S PRO — sparkling/still water dispenser with CO₂."""
    AIO = 2
    """CHOICE.ALL — all-in-one dispenser with hot, cold, and sparkling water."""
    SODA2 = 3
    """CHOICE.Soda — sparkling/still water dispenser."""
    FILTER = 4
    """CHOICE.Filter — filtered cold water dispenser."""
    HOT = 5
    """CHOICE.Hot — hot water dispenser."""
    SELECT = 6
    """SELECT II — multi-function water dispenser."""
    FLEXON = 7
    """FLEXON II — flexible water dispenser."""
    SEPURA = 8
    """SEPURA — water dispenser with filtration."""
    AQUA = 9
    """AQUA — filtration unit with volume- and time-based filter tracking."""
    BIOSORT = 10
    """BIOSORT — biological filtration system."""


BLANCO_DEVICE_NAMES: dict[BlancoDeviceType, str] = {
    BlancoDeviceType.SODA: "EVOL-S PRO",
    BlancoDeviceType.AIO: "CHOICE.ALL",
    BlancoDeviceType.SODA2: "CHOICE.Soda",
    BlancoDeviceType.FILTER: "CHOICE.Filter",
    BlancoDeviceType.HOT: "CHOICE.Hot",
    BlancoDeviceType.SELECT: "SELECT II",
    BlancoDeviceType.FLEXON: "FLEXON II",
    BlancoDeviceType.SEPURA: "SEPURA",
    BlancoDeviceType.AQUA: "AQUA",
    BlancoDeviceType.BIOSORT: "BIOSORT",
}
"""Marketing device names shown as the HA device model, keyed by BlancoDeviceType."""


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
