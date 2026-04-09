"""TypedDict result types and response-parsing helpers for the BLANCO API.

All typed return types for BlancoApiClient methods and the private helpers
that transform raw API response dicts into those types are defined here.
"""

from __future__ import annotations

from typing import Any, TypedDict

from .models import BlancoActionType, BlancoErrorType, BlancoWaterType


# ── Result types ──────────────────────────────────────────────────────────────


class AppRegistrationResult(TypedDict):
    """Result returned by BlancoApiClient.register_app."""

    app_id: str


class AuthResult(TypedDict):
    """Result returned by BlancoApiClient.authenticate / renew_token."""

    token: str
    token_type: str
    dev_type: int | None


class DeviceEventResult(TypedDict):
    """Parsed response from the /system, /status, or /settings endpoints."""

    params: dict[str, Any]
    info: dict[str, Any]


class DeviceErrorItem(TypedDict):
    """A single normalised error entry from the /errors endpoint."""

    err_code: int | None
    err_type: BlancoErrorType
    err_ts: int | None


class DeviceErrorsResult(TypedDict):
    """Parsed response from the /errors endpoint."""

    errors: list[DeviceErrorItem]
    info: dict[str, Any]


class DeviceActionItem(TypedDict):
    """A single normalised action entry from the /actions endpoint."""

    act_type: BlancoActionType
    evt_ts: int | None
    tap_state: BlancoWaterType
    disp_wtr_amt: int | None


class DeviceActionsResult(TypedDict):
    """Parsed response from the /actions endpoint."""

    actions: list[DeviceActionItem]
    info: dict[str, Any]


class StatTotalItem(TypedDict):
    """One aggregated parameter entry in a stats total list."""

    par: str
    """Parameter name (e.g. 'disp_wtr_amt' or 'wtr_flow')."""
    cnt: int
    """Number of data points aggregated into this total."""
    func: int
    """Aggregation function code used by the API."""
    val: int | float | list[Any]
    """Aggregated value — numeric for totals, list for distributions."""


class StatRangeResult(TypedDict):
    """Result for a single requested time range from the /stats endpoint."""

    range: dict[str, Any]
    """The time range descriptor echoed back by the API."""
    total: list[StatTotalItem]
    """List of aggregated parameter totals for this range."""
    details: list[dict[str, Any]]
    """Detailed breakdown entries (may be empty)."""


class DeviceStatsResult(TypedDict):
    """Top-level result from POST /devices/{dev_id}/stats."""

    ranges: list[StatRangeResult]
    """One entry per requested time range, in request order."""
    info: dict[str, Any]
    """Metadata returned alongside the stats results."""


# ── Private response-parsing helpers ─────────────────────────────────────────


def _safe_error_type(value: Any) -> BlancoErrorType:
    """Convert a raw err_type value to BlancoErrorType, falling back to UNDEF."""
    try:
        return BlancoErrorType(value)
    except (ValueError, TypeError):
        return BlancoErrorType.UNDEF


def _safe_tap_state(value: Any) -> BlancoWaterType:
    """Convert a raw tap_state value to BlancoWaterType, falling back to UNDEF."""
    try:
        return BlancoWaterType(value)
    except (ValueError, TypeError):
        return BlancoWaterType.UNDEF


def _parse_event(body: dict[str, Any]) -> DeviceEventResult:
    """Extract params and info from a standard single-result API response body."""
    result: DeviceEventResult = {
        "params": (body.get("results") or [{}])[0],
        "info": body.get("info", {}),
    }
    return result


def _parse_errors(body: dict[str, Any]) -> DeviceErrorsResult:
    """Extract and normalise the error list from an /errors API response body."""
    errors: list[DeviceErrorItem] = [
        {
            "err_code": entry.get("err_code"),
            "err_type": _safe_error_type(entry.get("err_type")),
            "err_ts": entry.get("err_ts"),
        }
        for entry in (body.get("results") or [])
    ]
    result: DeviceErrorsResult = {"errors": errors, "info": body.get("info", {})}
    return result


def _normalise_action(entry: dict[str, Any]) -> DeviceActionItem:
    """Normalise a single raw action entry to the internal representation.

    Some devices (e.g. AQUA-type units that only dispense still water) do
    not populate disp_wtr_amt / tap_state.  Instead they report the
    dispensed volume in mL via wtr_flow.  When wtr_flow is present it is
    mapped to disp_wtr_amt and tap_state is forced to STILL so that the
    value is attributed to both the STILL bucket and the overall total,
    exactly as AIO devices report it.
    """
    wtr_flow: int | None = entry.get("wtr_flow")
    if wtr_flow is not None:
        disp_wtr_amt: int | None = wtr_flow
        tap_state = BlancoWaterType.STILL
    else:
        disp_wtr_amt = entry.get("disp_wtr_amt")
        tap_state = _safe_tap_state(entry.get("tap_state"))
    raw_act_type = entry.get("act_type")
    try:
        act_type: BlancoActionType = BlancoActionType(raw_act_type)  # type: ignore[arg-type]
        # raw_act_type is Any from dict[str, Any]; runtime raises ValueError/TypeError on bad values
    except (ValueError, TypeError):
        act_type = BlancoActionType.UNDEF
    item: DeviceActionItem = {
        "act_type": act_type,
        "evt_ts": entry.get("evt_ts"),
        "tap_state": tap_state,
        "disp_wtr_amt": disp_wtr_amt,
    }
    return item


def _parse_actions(body: dict[str, Any]) -> DeviceActionsResult:
    """Extract and normalise the action list from an /actions API response body."""
    actions = [_normalise_action(entry) for entry in (body.get("results") or [])]
    result: DeviceActionsResult = {"actions": actions, "info": body.get("info", {})}
    return result


def _parse_stats(body: dict[str, Any]) -> DeviceStatsResult:
    """Parse a raw /stats API response body into a DeviceStatsResult."""
    ranges: list[StatRangeResult] = [
        {
            "range": entry.get("range", {}),
            "total": entry.get("total", []),
            "details": entry.get("details", []),
        }
        for entry in (body.get("results") or [])
    ]
    return {"ranges": ranges, "info": body.get("info", {})}
