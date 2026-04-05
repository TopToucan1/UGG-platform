"""
Demo simulator for PIN session tracking.

Unlike routes/events.py which writes directly to db.events, this simulator routes
events through gateway_core.pipeline.ingest() so the session_engine stage actually
fires and populates credit_sessions, pin_sessions, and session_anomalies.

Seeds a handful of demo players (PINs) and runs a background task that simulates
realistic session lifecycles on demo devices:
    pin_login → bill_in → meter snapshots (gameplay) → cashout/voucher_out → pin_logout

Only runs in SEED_MODE=demo.
"""
import asyncio
import random
import uuid
import logging
from datetime import datetime, timezone
from database import db
from session_engine import hash_pin

logger = logging.getLogger(__name__)

_demo_task = None

DEMO_PLAYERS = [
    {"name": "Alice Morgan",     "pin": "1234", "account_ref": "PIN-10001"},
    {"name": "Bob Thompson",     "pin": "4321", "account_ref": "PIN-10002"},
    {"name": "Carla Rodriguez",  "pin": "5678", "account_ref": "PIN-10003"},
    {"name": "Derek Chen",       "pin": "8765", "account_ref": "PIN-10004"},
    {"name": "Elena Vasquez",    "pin": "2468", "account_ref": "PIN-10005"},
    {"name": "Frank Miller",     "pin": "1357", "account_ref": "PIN-10006"},
    # One player used to trigger anomalies
    {"name": "Grace Anomaly",    "pin": "9999", "account_ref": "PIN-10007"},
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def seed_demo_pin_players() -> list[dict]:
    """Idempotent seed of the demo PIN player list. Returns the full player docs."""
    players = []
    for p in DEMO_PLAYERS:
        existing = await db.players_pin.find_one({"account_ref": p["account_ref"]}, {"_id": 0})
        if existing:
            players.append(existing)
            continue
        doc = {
            "id": str(uuid.uuid4()),
            "name": p["name"],
            "pin_hash": hash_pin(p["pin"]),
            "account_ref": p["account_ref"],
            "email": None,
            "phone": None,
            "tenant_id": None,
            "notes": "Demo player (seeded)",
            "status": "active",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        await db.players_pin.insert_one(dict(doc))
        players.append(doc)
    logger.info(f"session_demo: seeded {len(players)} demo PIN players")
    return players


async def _ingest(event: dict) -> None:
    """Send a canonical event through the gateway_core pipeline."""
    from gateway_core import gateway_core
    await gateway_core.pipeline.ingest(event)


def _make_event(device: dict, event_type: str, payload: dict) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "tenant_id": device.get("tenant_id", ""),
        "site_id": device.get("site_id", ""),
        "device_id": device["id"],
        "event_type": event_type,
        "protocol": device.get("protocol_family", "SAS").upper(),
        "occurred_at": _now_iso(),
        "received_at": _now_iso(),
        "payload": payload,
    }


async def _simulate_session(device: dict, player: dict, gaming_the_system: bool = False) -> None:
    """
    Simulate one full session lifecycle on a device.
    If gaming_the_system is True, behavior is tuned to trigger anomaly rules
    (small play count + large bill + matching cashout).
    """
    pin = None
    for p in DEMO_PLAYERS:
        if p["account_ref"] == player.get("account_ref"):
            pin = p["pin"]
            break
    if not pin:
        return

    # 1. PIN login
    await _ingest(_make_event(device, "device.player.pinLogin", {
        "pin": pin, "player_ref": player.get("account_ref")
    }))
    await asyncio.sleep(0.2)

    # 2. Bill in
    bill_amount = random.choice([20.0, 40.0, 100.0]) if gaming_the_system else random.choice([5.0, 10.0, 20.0, 50.0])
    await _ingest(_make_event(device, "device.billAcceptor.stacked", {
        "amount": bill_amount, "denom": int(bill_amount), "currency": "USD"
    }))
    await asyncio.sleep(0.3)

    # 3. Simulate gameplay via meter snapshots — advance coin_in/coin_out and currentCredits
    twin = await db.device_state_projection.find_one({"device_id": device["id"]}, {"_id": 0}) or {}
    start_coin_in = float(twin.get("coin_in_today", 0) or 0)
    start_coin_out = float(twin.get("coin_out_today", 0) or 0)
    start_games = int(twin.get("games_played_today", 0) or 0)

    games = 1 if gaming_the_system else random.randint(8, 40)
    total_wager = 0.0
    total_win = 0.0
    balance = bill_amount

    for i in range(games):
        bet = round(random.uniform(0.25, min(5.0, balance)), 2) if balance > 0.25 else 0.25
        if bet > balance:
            break
        win = round(bet * random.choice([0, 0, 0, 0.5, 1.0, 1.5, 2.0]), 2)
        total_wager += bet
        total_win += win
        balance = round(balance - bet + win, 2)
        if balance < 0:
            balance = 0
        # Emit meter snapshot periodically
        if i % 3 == 0 or i == games - 1:
            await _ingest(_make_event(device, "meter_snapshot", {
                "meters": {
                    "coinIn": {"value": start_coin_in + total_wager, "sas_code": "0000"},
                    "coinOut": {"value": start_coin_out + total_win, "sas_code": "0001"},
                    "currentCredits": {"value": balance, "sas_code": "000C"},
                    "gamesPlayed": {"value": start_games + i + 1, "sas_code": "0005"},
                }
            }))
            # Persist counters to twin so session_engine reads current values
            await db.device_state_projection.update_one(
                {"device_id": device["id"]},
                {"$set": {
                    "coin_in_today": start_coin_in + total_wager,
                    "coin_out_today": start_coin_out + total_win,
                    "games_played_today": start_games + i + 1,
                    "current_credits": balance,
                    "updated_at": _now_iso(),
                }},
                upsert=True,
            )
            await asyncio.sleep(0.1)
        if balance == 0:
            break

    # 4. Cashout remaining balance (if any) — voucher out, then zero meter snapshot
    if balance > 0:
        if gaming_the_system:
            # Cash out to match bill in, creating LOW_PLAY_FLIP pattern
            cashout_amount = round(balance, 2)
        else:
            cashout_amount = round(balance, 2)
        await _ingest(_make_event(device, "device.voucher.issued", {
            "amount": cashout_amount, "voucher_id": f"TKT-{random.randint(100000, 999999)}"
        }))
        await asyncio.sleep(0.1)
        balance = 0.0
        await db.device_state_projection.update_one(
            {"device_id": device["id"]},
            {"$set": {"current_credits": 0.0, "updated_at": _now_iso()}},
        )
        await _ingest(_make_event(device, "meter_snapshot", {
            "meters": {
                "currentCredits": {"value": 0, "sas_code": "000C"},
            }
        }))
    else:
        # Played down — emit zero snapshot to trigger close
        await _ingest(_make_event(device, "meter_snapshot", {
            "meters": {"currentCredits": {"value": 0, "sas_code": "000C"}}
        }))

    await asyncio.sleep(0.2)

    # 5. PIN logout
    await _ingest(_make_event(device, "device.player.pinLogout", {"reason": "user"}))


async def _demo_loop() -> None:
    """Run session simulations forever on demo devices."""
    # Wait for seed to finish
    await asyncio.sleep(10)
    players = await db.players_pin.find({"account_ref": {"$regex": "^PIN-1000"}}, {"_id": 0}).to_list(50)
    if not players:
        logger.warning("session_demo: no demo players found, skipping loop")
        return

    while True:
        try:
            devices = await db.devices.find(
                {"status": "online"}, {"_id": 0, "id": 1, "tenant_id": 1, "site_id": 1, "protocol_family": 1}
            ).to_list(50)
            if not devices:
                await asyncio.sleep(20)
                continue

            # Pick a random device that currently has no active credit session
            random.shuffle(devices)
            chosen_device = None
            for d in devices:
                active = await db.credit_sessions.find_one({"device_id": d["id"], "is_active": True})
                if not active:
                    chosen_device = d
                    break
            if not chosen_device:
                await asyncio.sleep(15)
                continue

            # 20% chance to run a "gaming the system" player to trigger anomalies
            if random.random() < 0.20:
                player = next((p for p in players if p.get("account_ref") == "PIN-10007"), players[0])
                await _simulate_session(chosen_device, player, gaming_the_system=True)
            else:
                player = random.choice([p for p in players if p.get("account_ref") != "PIN-10007"])
                await _simulate_session(chosen_device, player, gaming_the_system=False)

            await asyncio.sleep(random.uniform(8.0, 20.0))
        except Exception as e:
            logger.error(f"session_demo loop error: {e}", exc_info=True)
            await asyncio.sleep(10)


def start_session_demo() -> None:
    global _demo_task
    if _demo_task is None or _demo_task.done():
        _demo_task = asyncio.create_task(_demo_loop())
        logger.info("session_demo: background simulator started")
