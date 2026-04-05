"""
Session anomaly detector — gaming-the-system watch.

Runs on credit session close. Correlates credit + PIN sessions per player
to flag patterns that suggest abuse, bonus farming, or money movement.

Rules v1:
  R1 RAPID_CYCLING   — same player ≥ N credit sessions on same device within M minutes
  R2 LOW_PLAY_FLIP   — bill in > $X with games_played < Y and cashout ≥ 90% of bill in
  R3 HOPPER          — same player active on ≥ N devices within M minutes
  R4 PIN_CHURN       — PIN logouts while credits > 0 above threshold per hour
  R5 MICRO_SESSION   — session duration < 60s with near-zero play

Writes to session_anomalies. Never throws — errors are logged.
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta
from database import db

logger = logging.getLogger(__name__)

# ─── Configurable thresholds ───
R1_WINDOW_MIN = 30
R1_SESSION_COUNT = 4

R2_MIN_BILL_IN = 50.0
R2_MAX_GAMES = 3
R2_CASHOUT_RATIO = 0.90

R3_WINDOW_MIN = 60
R3_DEVICE_COUNT = 3

R4_WINDOW_MIN = 60
R4_CHURN_COUNT = 5

R5_MAX_DURATION_SEC = 60
R5_MAX_GAMES = 1


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(iso: str) -> datetime:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:
        return _now()


async def _raise_anomaly(rule_code: str, severity: str, player_id: str | None, detail: str, related_session_ids: list[str], extra: dict | None = None):
    doc = {
        "id": str(uuid.uuid4()),
        "rule_code": rule_code,
        "severity": severity,
        "player_id": player_id,
        "detected_at": _now().isoformat(),
        "detail": detail,
        "related_session_ids": related_session_ids,
        "status": "open",
        "extra": extra or {},
    }
    await db.session_anomalies.insert_one(dict(doc))
    logger.info(f"anomaly: [{severity}] {rule_code} player={player_id} detail={detail}")


async def scan_on_credit_session_close(credit_session_id: str) -> None:
    """Entry point called by session_engine when a credit session closes."""
    try:
        session = await db.credit_sessions.find_one({"id": credit_session_id}, {"_id": 0})
        if not session:
            return

        # Determine the player(s) involved via linked pin_sessions
        pin_session_ids = session.get("pin_session_ids", []) or []
        pin_sessions = []
        if pin_session_ids:
            pin_sessions = await db.pin_sessions.find(
                {"id": {"$in": pin_session_ids}}, {"_id": 0}
            ).to_list(100)

        player_ids = list({ps["player_id"] for ps in pin_sessions if ps.get("player_id")})

        # R5: MICRO_SESSION (applies even to anonymous)
        await _check_micro_session(session)

        # R2: LOW_PLAY_FLIP
        await _check_low_play_flip(session, player_ids)

        # Per-player rules
        for pid in player_ids:
            await _check_rapid_cycling(pid, session)
            await _check_hopper(pid, session)
            await _check_pin_churn(pid)

    except Exception as e:
        logger.error(f"anomaly scan_on_credit_session_close error: {e}", exc_info=True)


async def _check_micro_session(session: dict) -> None:
    started = _parse(session.get("started_at", ""))
    ended = _parse(session.get("ended_at") or _now().isoformat())
    duration = (ended - started).total_seconds()
    games = int(session.get("games_played", 0) or 0)
    if duration <= R5_MAX_DURATION_SEC and games <= R5_MAX_GAMES:
        # Try to pull a player from pin_session_ids for attribution
        player_id = None
        pin_ids = session.get("pin_session_ids", []) or []
        if pin_ids:
            first = await db.pin_sessions.find_one({"id": pin_ids[0]}, {"_id": 0})
            if first:
                player_id = first.get("player_id")
        await _raise_anomaly(
            "MICRO_SESSION", "LOW", player_id,
            f"Session lasted {duration:.0f}s with {games} games",
            [session["id"]],
            {"duration_sec": duration, "games": games},
        )


async def _check_low_play_flip(session: dict, player_ids: list[str]) -> None:
    total_in = float(session.get("total_in", 0) or 0)
    total_out = float(session.get("total_out", 0) or 0)
    games = int(session.get("games_played", 0) or 0)
    if total_in < R2_MIN_BILL_IN:
        return
    if games > R2_MAX_GAMES:
        return
    if total_in <= 0:
        return
    ratio = total_out / total_in
    if ratio < R2_CASHOUT_RATIO:
        return
    pid = player_ids[0] if player_ids else None
    await _raise_anomaly(
        "LOW_PLAY_FLIP", "HIGH", pid,
        f"${total_in:.2f} in, ${total_out:.2f} out, {games} games (ratio {ratio:.0%})",
        [session["id"]],
        {"total_in": total_in, "total_out": total_out, "games": games, "ratio": ratio},
    )


async def _check_rapid_cycling(player_id: str, current_session: dict) -> None:
    device_id = current_session.get("device_id")
    window_start = (_now() - timedelta(minutes=R1_WINDOW_MIN)).isoformat()
    # Find pin_sessions for this player+device in window
    recent_pin = await db.pin_sessions.find(
        {
            "player_id": player_id,
            "device_id": device_id,
            "started_at": {"$gte": window_start},
        },
        {"_id": 0},
    ).to_list(100)
    credit_ids = list({p.get("credit_session_id") for p in recent_pin if p.get("credit_session_id")})
    if len(credit_ids) >= R1_SESSION_COUNT:
        await _raise_anomaly(
            "RAPID_CYCLING", "HIGH", player_id,
            f"{len(credit_ids)} credit sessions on device {device_id} in last {R1_WINDOW_MIN} min",
            credit_ids,
            {"device_id": device_id, "window_min": R1_WINDOW_MIN},
        )


async def _check_hopper(player_id: str, current_session: dict) -> None:
    window_start = (_now() - timedelta(minutes=R3_WINDOW_MIN)).isoformat()
    recent = await db.pin_sessions.find(
        {"player_id": player_id, "started_at": {"$gte": window_start}},
        {"_id": 0},
    ).to_list(200)
    device_ids = list({p.get("device_id") for p in recent if p.get("device_id")})
    if len(device_ids) >= R3_DEVICE_COUNT:
        await _raise_anomaly(
            "HOPPER", "HIGH", player_id,
            f"Active on {len(device_ids)} devices in last {R3_WINDOW_MIN} min",
            [p["id"] for p in recent],
            {"device_ids": device_ids, "window_min": R3_WINDOW_MIN},
        )


async def _check_pin_churn(player_id: str) -> None:
    window_start = (_now() - timedelta(minutes=R4_WINDOW_MIN)).isoformat()
    # Count pin_sessions ending with pin_logout while the linked credit_session was still active after
    recent = await db.pin_sessions.find(
        {
            "player_id": player_id,
            "ended_at": {"$gte": window_start},
            "end_reason": "pin_logout",
        },
        {"_id": 0},
    ).to_list(200)
    walk_aways = 0
    related = []
    for ps in recent:
        cs_id = ps.get("credit_session_id")
        if not cs_id:
            continue
        cs = await db.credit_sessions.find_one({"id": cs_id}, {"_id": 0, "ended_at": 1, "is_active": 1})
        # Logout happened before credit session closed (still active, or closed after logout)
        if not cs:
            continue
        if cs.get("is_active") or (cs.get("ended_at") and cs["ended_at"] > ps.get("ended_at", "")):
            walk_aways += 1
            related.append(ps["id"])
    if walk_aways >= R4_CHURN_COUNT:
        await _raise_anomaly(
            "PIN_CHURN", "MEDIUM", player_id,
            f"{walk_aways} PIN logouts with credits remaining in last {R4_WINDOW_MIN} min",
            related,
            {"walk_away_count": walk_aways, "window_min": R4_WINDOW_MIN},
        )
