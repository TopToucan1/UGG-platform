"""
UGG Session Engine — Two-layer session tracking for PIN-authenticated players.

Layer 1: credit_sessions (money) — bounded by balance at zero
Layer 2: pin_sessions (player) — bounded by PIN login/logout or credit session end

Invariants:
  - One active credit_session per device
  - One active pin_session per device
  - One active pin_session per player globally (one-PIN-one-EGM, last-wins)
  - Credit session end force-closes any attached pin_session
  - PIN session end does NOT end the credit session

Entry point: dispatch(event) — called by gateway_core pipeline stage.
"""
import uuid
import logging
import bcrypt
from datetime import datetime, timezone
from typing import Optional
from database import db

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Event types this engine listens for
# ─────────────────────────────────────────────
EVT_BILL_STACKED = "device.billAcceptor.stacked"
EVT_VOUCHER_REDEEMED = "device.voucher.redeemed"
EVT_VOUCHER_ISSUED = "device.voucher.issued"
EVT_PIN_LOGIN = "device.player.pinLogin"
EVT_PIN_LOGOUT = "device.player.pinLogout"
EVT_METER_SNAPSHOT = "meter_snapshot"

RELEVANT_EVENT_TYPES = {
    EVT_BILL_STACKED,
    EVT_VOUCHER_REDEEMED,
    EVT_VOUCHER_ISSUED,
    EVT_PIN_LOGIN,
    EVT_PIN_LOGOUT,
    EVT_METER_SNAPSHOT,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_pin(pin: str) -> str:
    """bcrypt cost 10 for PIN storage."""
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("utf-8")


def verify_pin(pin: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pin.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ─────────────────────────────────────────────
# Dispatch
# ─────────────────────────────────────────────
async def dispatch(event: dict) -> None:
    """Route a canonical event to the appropriate handler. No-op if not relevant."""
    evt_type = event.get("event_type", "")
    if evt_type not in RELEVANT_EVENT_TYPES:
        return

    try:
        if evt_type == EVT_BILL_STACKED:
            await _on_bill_stacked(event)
        elif evt_type == EVT_VOUCHER_REDEEMED:
            await _on_voucher_redeemed(event)
        elif evt_type == EVT_VOUCHER_ISSUED:
            await _on_voucher_issued(event)
        elif evt_type == EVT_PIN_LOGIN:
            await _on_pin_login(event)
        elif evt_type == EVT_PIN_LOGOUT:
            await _on_pin_logout(event)
        elif evt_type == EVT_METER_SNAPSHOT:
            await _on_meter_snapshot(event)
    except Exception as e:
        logger.error(f"session_engine dispatch error on {evt_type}: {e}", exc_info=True)


# ─────────────────────────────────────────────
# Credit session lifecycle
# ─────────────────────────────────────────────
async def _get_active_credit_session(device_id: str) -> Optional[dict]:
    return await db.credit_sessions.find_one(
        {"device_id": device_id, "is_active": True}, {"_id": 0}
    )


async def _get_current_credits(device_id: str) -> float:
    """Read credit meter from digital twin projection."""
    twin = await db.device_state_projection.find_one(
        {"device_id": device_id}, {"_id": 0, "current_credits": 1}
    )
    if not twin:
        return 0.0
    return float(twin.get("current_credits") or 0)


async def _open_credit_session(event: dict, trigger: str, amount: float) -> dict:
    """Open a new credit session on a device. Caller must have verified none is active."""
    device_id = event.get("device_id", "")
    device = await db.devices.find_one({"id": device_id}, {"_id": 0}) or {}

    session = {
        "id": str(uuid.uuid4()),
        "device_id": device_id,
        "tenant_id": event.get("tenant_id") or device.get("tenant_id", ""),
        "site_id": event.get("site_id") or device.get("site_id", ""),
        "distributor_id": event.get("distributor_id") or device.get("distributor_id"),
        "started_at": event.get("occurred_at") or _now_iso(),
        "ended_at": None,
        "start_trigger": trigger,
        "start_amount": amount,
        "end_reason": None,
        "total_in": amount,
        "total_out": 0.0,
        "start_meters": {},
        "end_meters": {},
        "coin_in": 0.0,
        "coin_out": 0.0,
        "games_played": 0,
        "net": 0.0,
        "pin_session_ids": [],
        "is_active": True,
        "source_event_id": event.get("id"),
    }

    # Snapshot start meters from digital twin
    twin = await db.device_state_projection.find_one({"device_id": device_id}, {"_id": 0}) or {}
    session["start_meters"] = {
        "coin_in_today": twin.get("coin_in_today", 0),
        "coin_out_today": twin.get("coin_out_today", 0),
        "games_played_today": twin.get("games_played_today", 0),
    }

    await db.credit_sessions.insert_one(dict(session))
    logger.info(f"session_engine: credit_session OPEN {session['id']} device={device_id} trigger={trigger} amount={amount}")

    # If a PIN is currently logged in on this device, attach it now
    claim = await db.player_pin_state.find_one({"device_id": device_id})
    if claim:
        await _attach_orphan_pin_session(claim["player_id"], device_id, session["id"])

    return session


async def _close_credit_session(session: dict, end_reason: str, at: Optional[str] = None) -> None:
    """Close an active credit session and force-close its attached pin_session if any."""
    session_id = session["id"]
    device_id = session["device_id"]
    ended_at = at or _now_iso()

    # Compute deltas from digital twin
    twin = await db.device_state_projection.find_one({"device_id": device_id}, {"_id": 0}) or {}
    start = session.get("start_meters", {})
    coin_in = float(twin.get("coin_in_today", 0)) - float(start.get("coin_in_today", 0))
    coin_out = float(twin.get("coin_out_today", 0)) - float(start.get("coin_out_today", 0))
    games_played = int(twin.get("games_played_today", 0)) - int(start.get("games_played_today", 0))
    # Guard against counter resets (go negative)
    coin_in = max(coin_in, 0.0)
    coin_out = max(coin_out, 0.0)
    games_played = max(games_played, 0)

    await db.credit_sessions.update_one(
        {"id": session_id},
        {"$set": {
            "is_active": False,
            "ended_at": ended_at,
            "end_reason": end_reason,
            "end_meters": {
                "coin_in_today": twin.get("coin_in_today", 0),
                "coin_out_today": twin.get("coin_out_today", 0),
                "games_played_today": twin.get("games_played_today", 0),
            },
            "coin_in": coin_in,
            "coin_out": coin_out,
            "games_played": games_played,
            "net": coin_out - coin_in,
        }},
    )
    logger.info(f"session_engine: credit_session CLOSE {session_id} reason={end_reason} coin_in={coin_in} coin_out={coin_out} games={games_played}")

    # Force-close any active pin_session on this device tied to this credit session
    active_pin = await db.pin_sessions.find_one(
        {"device_id": device_id, "is_active": True, "credit_session_id": session_id},
        {"_id": 0},
    )
    if active_pin:
        await _close_pin_session(active_pin, "credit_session_ended", ended_at)

    # Trigger anomaly scan asynchronously (fire-and-forget)
    try:
        from session_anomaly import scan_on_credit_session_close
        await scan_on_credit_session_close(session_id)
    except Exception as e:
        logger.error(f"anomaly scan error: {e}")


# ─────────────────────────────────────────────
# PIN session lifecycle
# ─────────────────────────────────────────────
async def _open_pin_session(player: dict, device_id: str, event: dict) -> dict:
    """Open a PIN session. Enforces one-PIN-one-EGM last-wins policy."""
    player_id = player["id"]

    # Last-wins: if player has any active pin_session anywhere, force-close it
    existing = await db.pin_sessions.find_one(
        {"player_id": player_id, "is_active": True}, {"_id": 0}
    )
    if existing:
        await _close_pin_session(existing, "forced_logout_other_device", _now_iso())

    # Last-wins: if target device has any active pin_session (different player), close it
    device_active = await db.pin_sessions.find_one(
        {"device_id": device_id, "is_active": True}, {"_id": 0}
    )
    if device_active:
        await _close_pin_session(device_active, "forced_logout_pin_swap", _now_iso())

    # Link to active credit session on this device if any
    credit = await _get_active_credit_session(device_id)
    credit_session_id = credit["id"] if credit else None

    device = await db.devices.find_one({"id": device_id}, {"_id": 0}) or {}
    pin_session = {
        "id": str(uuid.uuid4()),
        "player_id": player_id,
        "player_name": player.get("name", ""),
        "device_id": device_id,
        "tenant_id": device.get("tenant_id", ""),
        "site_id": device.get("site_id", ""),
        "credit_session_id": credit_session_id,
        "started_at": event.get("occurred_at") or _now_iso(),
        "ended_at": None,
        "start_trigger": "pin_login",
        "end_reason": None,
        "start_meters": {},
        "end_meters": {},
        "coin_in": 0.0,
        "coin_out": 0.0,
        "games_played": 0,
        "net": 0.0,
        "bill_in_during": 0.0,
        "is_active": True,
        "source_event_id": event.get("id"),
    }

    twin = await db.device_state_projection.find_one({"device_id": device_id}, {"_id": 0}) or {}
    pin_session["start_meters"] = {
        "coin_in_today": twin.get("coin_in_today", 0),
        "coin_out_today": twin.get("coin_out_today", 0),
        "games_played_today": twin.get("games_played_today", 0),
    }

    await db.pin_sessions.insert_one(dict(pin_session))

    # Claim the PIN on this device
    await db.player_pin_state.update_one(
        {"_id": player_id},
        {"$set": {
            "player_id": player_id,
            "device_id": device_id,
            "pin_session_id": pin_session["id"],
            "login_at": pin_session["started_at"],
        }},
        upsert=True,
    )

    # Append to credit session's pin_session_ids if linked
    if credit_session_id:
        await db.credit_sessions.update_one(
            {"id": credit_session_id},
            {"$push": {"pin_session_ids": pin_session["id"]}},
        )

    logger.info(f"session_engine: pin_session OPEN {pin_session['id']} player={player_id} device={device_id} credit_session={credit_session_id}")
    return pin_session


async def _close_pin_session(pin_session: dict, end_reason: str, at: Optional[str] = None) -> None:
    ended_at = at or _now_iso()
    device_id = pin_session["device_id"]
    player_id = pin_session["player_id"]

    # Deltas from digital twin
    twin = await db.device_state_projection.find_one({"device_id": device_id}, {"_id": 0}) or {}
    start = pin_session.get("start_meters", {})
    coin_in = max(float(twin.get("coin_in_today", 0)) - float(start.get("coin_in_today", 0)), 0.0)
    coin_out = max(float(twin.get("coin_out_today", 0)) - float(start.get("coin_out_today", 0)), 0.0)
    games_played = max(int(twin.get("games_played_today", 0)) - int(start.get("games_played_today", 0)), 0)

    await db.pin_sessions.update_one(
        {"id": pin_session["id"]},
        {"$set": {
            "is_active": False,
            "ended_at": ended_at,
            "end_reason": end_reason,
            "end_meters": {
                "coin_in_today": twin.get("coin_in_today", 0),
                "coin_out_today": twin.get("coin_out_today", 0),
                "games_played_today": twin.get("games_played_today", 0),
            },
            "coin_in": coin_in,
            "coin_out": coin_out,
            "games_played": games_played,
            "net": coin_out - coin_in,
        }},
    )

    # Release the PIN claim only if it still points at this session
    await db.player_pin_state.delete_one(
        {"_id": player_id, "pin_session_id": pin_session["id"]}
    )
    logger.info(f"session_engine: pin_session CLOSE {pin_session['id']} reason={end_reason}")


async def _attach_orphan_pin_session(player_id: str, device_id: str, credit_session_id: str) -> None:
    """If a PIN was logged in before a credit session existed, link them once the credit session opens."""
    orphan = await db.pin_sessions.find_one(
        {"player_id": player_id, "device_id": device_id, "is_active": True, "credit_session_id": None},
        {"_id": 0},
    )
    if not orphan:
        return
    await db.pin_sessions.update_one(
        {"id": orphan["id"]},
        {"$set": {"credit_session_id": credit_session_id}},
    )
    await db.credit_sessions.update_one(
        {"id": credit_session_id},
        {"$push": {"pin_session_ids": orphan["id"]}},
    )
    logger.info(f"session_engine: attached orphan pin_session {orphan['id']} to credit_session {credit_session_id}")


# ─────────────────────────────────────────────
# Event handlers
# ─────────────────────────────────────────────
async def _on_bill_stacked(event: dict) -> None:
    device_id = event.get("device_id", "")
    amount = float(event.get("payload", {}).get("amount", 0) or 0)

    active = await _get_active_credit_session(device_id)
    current_credits = await _get_current_credits(device_id)

    if active:
        # Top-up on existing session
        await db.credit_sessions.update_one(
            {"id": active["id"]},
            {"$inc": {"total_in": amount}},
        )
        # If a pin_session is active, also accumulate bill_in_during
        pin_active = await db.pin_sessions.find_one(
            {"device_id": device_id, "is_active": True}, {"_id": 0}
        )
        if pin_active:
            await db.pin_sessions.update_one(
                {"id": pin_active["id"]},
                {"$inc": {"bill_in_during": amount}},
            )
        return

    # No active session — start one only if balance was zero at time of event
    # (meter may already reflect this bill, so we rely on "no active session" as the zero-balance proxy)
    if current_credits <= 0.0 or not active:
        await _open_credit_session(event, trigger="bill_in", amount=amount)


async def _on_voucher_redeemed(event: dict) -> None:
    """TITO ticket inserted."""
    device_id = event.get("device_id", "")
    amount = float(event.get("payload", {}).get("amount", 0) or 0)

    active = await _get_active_credit_session(device_id)
    if active:
        await db.credit_sessions.update_one(
            {"id": active["id"]},
            {"$inc": {"total_in": amount}},
        )
        pin_active = await db.pin_sessions.find_one(
            {"device_id": device_id, "is_active": True}, {"_id": 0}
        )
        if pin_active:
            await db.pin_sessions.update_one(
                {"id": pin_active["id"]},
                {"$inc": {"bill_in_during": amount}},
            )
        return

    await _open_credit_session(event, trigger="ticket_in", amount=amount)


async def _on_voucher_issued(event: dict) -> None:
    """TITO ticket printed (cashout to ticket)."""
    device_id = event.get("device_id", "")
    amount = float(event.get("payload", {}).get("amount", 0) or 0)
    active = await _get_active_credit_session(device_id)
    if not active:
        return
    await db.credit_sessions.update_one(
        {"id": active["id"]},
        {"$inc": {"total_out": amount}},
    )
    # Actual session close happens when currentCredits hits 0 via meter_snapshot


async def _on_pin_login(event: dict) -> None:
    """EGM reports player logged in with PIN. Gateway verifies PIN and opens pin_session."""
    device_id = event.get("device_id", "")
    payload = event.get("payload", {}) or {}
    raw_pin = payload.get("pin") or payload.get("pin_code")
    player_ref = payload.get("player_ref")  # optional account hint

    if not raw_pin:
        logger.warning(f"session_engine: pinLogin missing pin on device={device_id}")
        return

    # Verify PIN against players_pin collection
    # Lookup by player_ref if provided, else scan active players (bounded by typical fleet size)
    player = None
    if player_ref:
        player = await db.players_pin.find_one(
            {"$or": [{"id": player_ref}, {"account_ref": player_ref}]}, {"_id": 0}
        )
        if player and not verify_pin(raw_pin, player.get("pin_hash", "")):
            player = None
    else:
        # Fallback: iterate (acceptable for small player bases; larger needs a different scheme)
        async for p in db.players_pin.find({"status": "active"}, {"_id": 0}):
            if verify_pin(raw_pin, p.get("pin_hash", "")):
                player = p
                break

    if not player:
        logger.warning(f"session_engine: pinLogin FAILED verify on device={device_id}")
        # Record failed attempt for brute-force tracking
        await db.pin_login_attempts.insert_one({
            "device_id": device_id,
            "occurred_at": _now_iso(),
            "success": False,
            "player_ref": player_ref,
        })
        return

    await db.pin_login_attempts.insert_one({
        "device_id": device_id,
        "player_id": player["id"],
        "occurred_at": _now_iso(),
        "success": True,
    })
    await _open_pin_session(player, device_id, event)


async def _on_pin_logout(event: dict) -> None:
    device_id = event.get("device_id", "")
    active = await db.pin_sessions.find_one(
        {"device_id": device_id, "is_active": True}, {"_id": 0}
    )
    if not active:
        return
    await _close_pin_session(active, "pin_logout", event.get("occurred_at"))


async def _on_meter_snapshot(event: dict) -> None:
    """
    Detect credit session end: currentCredits transitions to 0.
    The gateway_core TWIN stage has already updated device_state_projection by the time
    this runs (session stage is 4.5, after stage 4 TWIN).
    """
    device_id = event.get("device_id", "")
    meters = (event.get("payload", {}) or {}).get("meters", {}) or {}
    cc = meters.get("currentCredits")
    if cc is None:
        return
    # Extract scalar
    if isinstance(cc, dict):
        cc_value = float(cc.get("value", 0) or 0)
    else:
        cc_value = float(cc or 0)

    if cc_value > 0:
        return

    active = await _get_active_credit_session(device_id)
    if not active:
        return

    # Determine end_reason from recent session activity
    end_reason = await _infer_end_reason(active, device_id)
    await _close_credit_session(active, end_reason, event.get("occurred_at"))


async def _infer_end_reason(credit_session: dict, device_id: str) -> str:
    """Look at recent events on device to classify how the session ended."""
    since = credit_session.get("started_at")
    # Most recent cashout/handpay event
    recent = await db.events.find_one(
        {
            "device_id": device_id,
            "occurred_at": {"$gte": since},
            "event_type": {"$in": [
                EVT_VOUCHER_ISSUED,
                "device.jackpot.handpay",
                "device.cashout.cash",
                "device.transfer.out",
            ]},
        },
        sort=[("occurred_at", -1)],
    )
    if not recent:
        return "played_down"
    et = recent.get("event_type", "")
    if et == EVT_VOUCHER_ISSUED:
        return "cashout_ticket"
    if et == "device.jackpot.handpay":
        return "handpay"
    if et == "device.cashout.cash":
        return "cashout_cash"
    if et == "device.transfer.out":
        return "transfer_out"
    return "played_down"


# ─────────────────────────────────────────────
# Index setup — called once at startup
# ─────────────────────────────────────────────
async def ensure_indexes() -> None:
    await db.players_pin.create_index("id", unique=True)
    await db.players_pin.create_index("account_ref")
    await db.players_pin.create_index("status")

    await db.credit_sessions.create_index("id", unique=True)
    await db.credit_sessions.create_index([("device_id", 1), ("is_active", 1)])
    await db.credit_sessions.create_index([("started_at", -1)])
    await db.credit_sessions.create_index("tenant_id")

    await db.pin_sessions.create_index("id", unique=True)
    await db.pin_sessions.create_index([("player_id", 1), ("started_at", -1)])
    await db.pin_sessions.create_index([("device_id", 1), ("is_active", 1)])
    await db.pin_sessions.create_index("credit_session_id")

    await db.player_pin_state.create_index("device_id")
    await db.player_pin_state.create_index("player_id")

    await db.session_anomalies.create_index([("player_id", 1), ("detected_at", -1)])
    await db.session_anomalies.create_index("status")

    await db.pin_login_attempts.create_index([("device_id", 1), ("occurred_at", -1)])
    await db.pin_login_attempts.create_index("occurred_at")
    logger.info("session_engine: indexes ensured")
