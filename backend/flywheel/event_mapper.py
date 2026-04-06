"""
FlywheelOS Event Mapper — translates UGG CanonicalEvents into FlywheelOS EventFamily.
"""
import uuid
import logging
from datetime import datetime, timezone
from database import db

logger = logging.getLogger(__name__)

# ── UGG event_type → FlywheelOS EventFamily mapping ──
EVENT_MAP = {
    # Player PIN
    "device.player.pinLogin":           "progress_start",
    "device.player.pinLogout":          "negative_signal",
    # Money
    "device.billAcceptor.stacked":      "commitment",
    "device.voucher.redeemed":          "commitment",
    "device.voucher.issued":            "resource_spend",
    "device.cashout.cash":              "resource_spend",
    "device.transfer.out":              "resource_spend",
    "device.transfer.in":               "resource_gain",
    # Gameplay
    "meter_snapshot":                   "progress_advance",
    "device.game.start":                "progress_advance",
    "device.game.end":                  "progress_advance",
    # Wins
    "device.jackpot.handpay":           "competition_win",
    "device.bonus.triggered":           "competition_win",
    # Faults (suppress engagement)
    "device.tilt":                      "negative_signal",
    "device.door.opened":               "negative_signal",
    "device.integrity.check":           "negative_signal",
    # Status
    "device.status.online":             "return_visit",
    "device.health.check":              None,  # ignored
}

# ── Internal synthetic events (emitted by session_engine, not adapters) ──
SYNTHETIC_EVENTS = {
    "flywheel.credit_session.closed.loss": "competition_loss",
    "flywheel.credit_session.closed.win":  "competition_win",
    "flywheel.anomaly.raised":             "negative_signal",
}


async def _resolve_player_for_device(device_id: str) -> tuple[str | None, str | None]:
    """Look up the active PIN session on a device. Returns (player_id, player_name) or (None, None)."""
    claim = await db.player_pin_state.find_one({"device_id": device_id})
    if not claim:
        return None, None
    player = await db.players_pin.find_one({"id": claim["player_id"]}, {"_id": 0, "id": 1, "name": 1})
    if not player:
        return claim["player_id"], ""
    return player["id"], player.get("name", "")


async def map_event(ugg_event: dict) -> dict | None:
    """
    Convert a UGG pipeline event into a FlywheelOS event.
    Returns None if the event doesn't map to any family.
    """
    event_type = ugg_event.get("event_type", "")

    # Try direct map first
    family = EVENT_MAP.get(event_type)
    if family is None and event_type not in EVENT_MAP:
        # Check synthetic
        family = SYNTHETIC_EVENTS.get(event_type)
    if family is None:
        return None

    device_id = ugg_event.get("device_id", "")
    payload = ugg_event.get("payload", {}) or {}

    # Resolve actor: prefer player, fall back to device
    actor_id = None
    actor_type = "device"
    player_name = ""

    # If the event itself carries player info (pinLogin/pinLogout)
    if event_type in ("device.player.pinLogin", "device.player.pinLogout"):
        # Player ID is resolved during session_engine processing; look up active claim
        pid, pname = await _resolve_player_for_device(device_id)
        if pid:
            actor_id = pid
            actor_type = "player"
            player_name = pname or ""

    # For synthetic events, actor_id is in the payload
    if event_type.startswith("flywheel."):
        actor_id = payload.get("player_id") or payload.get("actor_id")
        actor_type = "player" if actor_id else "device"
        player_name = payload.get("player_name", "")

    # For all other events, try to find logged-in player on this device
    if not actor_id and device_id:
        pid, pname = await _resolve_player_for_device(device_id)
        if pid:
            actor_id = pid
            actor_type = "player"
            player_name = pname or ""

    if not actor_id:
        actor_id = device_id
        actor_type = "device"

    # Build flywheel event
    now = datetime.now(timezone.utc).isoformat()
    fw_event = {
        "id": str(uuid.uuid4()),
        "app_id": "ugg",
        "tenant_id": ugg_event.get("tenant_id", ""),
        "actor_id": actor_id,
        "actor_type": actor_type,
        "player_name": player_name,
        "event_family": family,
        "event_name": event_type,
        "object_id": _infer_object_id(ugg_event),
        "object_type": _infer_object_type(ugg_event),
        "object_category": "",
        "value": _extract_value(ugg_event),
        "properties": {
            "device_id": device_id,
            "site_id": ugg_event.get("site_id", ""),
            "distributor_id": ugg_event.get("distributor_id", ""),
            **{k: v for k, v in payload.items() if isinstance(v, (str, int, float, bool))},
        },
        "source_event_id": ugg_event.get("id", ""),
        "occurred_at": ugg_event.get("occurred_at") or now,
        "received_at": now,
    }
    return fw_event


def _infer_object_id(event: dict) -> str:
    """Determine the best object_id for this event."""
    et = event.get("event_type", "")
    if "session" in et:
        return event.get("payload", {}).get("session_id", event.get("device_id", ""))
    return event.get("device_id", "")


def _infer_object_type(event: dict) -> str:
    et = event.get("event_type", "")
    if "session" in et:
        return "credit_session"
    if "jackpot" in et or "bonus" in et:
        return "jackpot"
    if "voucher" in et or "bill" in et:
        return "transaction"
    if "meter" in et:
        return "meter"
    return "device"


def _extract_value(event: dict) -> float:
    """Extract a numeric value from the event payload."""
    payload = event.get("payload", {}) or {}
    for key in ("amount", "value", "win", "bet", "poc_amount"):
        v = payload.get(key)
        if v is not None:
            try:
                return float(v)
            except (ValueError, TypeError):
                pass
    return 0.0
