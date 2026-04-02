import uuid
import random
from datetime import datetime, timezone, timedelta
from database import db
import logging

logger = logging.getLogger(__name__)

PLAYER_FIRST = ["James", "Maria", "David", "Sarah", "Michael", "Linda", "Robert", "Jennifer", "William", "Patricia", "Carlos", "Yuki", "Ahmed", "Olga", "Wei"]
PLAYER_LAST = ["S.", "T.", "R.", "M.", "L.", "W.", "K.", "B.", "J.", "P.", "G.", "H.", "D.", "F.", "C."]
GAME_NAMES = ["Buffalo Gold", "Lightning Link", "Dragon Link", "Wheel of Fortune", "88 Fortunes", "Lock It Link", "Cleopatra", "Dancing Drums", "Quick Hit", "Double Diamond", "Wolf Run", "Jackpot Party", "Fu Dai Lian Lian", "Huff N Puff", "Mighty Cash", "Walking Dead"]
DENOMS = [0.01, 0.05, 0.25, 1.00, 5.00]


def _id():
    return str(uuid.uuid4())


def _past(hours_max=72):
    return (datetime.now(timezone.utc) - timedelta(hours=random.uniform(0, hours_max))).isoformat()


async def seed_financial_and_players():
    """Seed financial_events and player_sessions if not already present."""
    if await db.financial_events.count_documents({}) > 0:
        logger.info("Financial/player data already seeded, skipping")
        return

    logger.info("Seeding financial events and player sessions...")

    # Grab existing devices and sites
    devices = await db.devices.find({}, {"_id": 0, "id": 1, "external_ref": 1, "tenant_id": 1, "site_id": 1, "metadata": 1}).to_list(200)
    sites = await db.sites.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(20)
    if not devices:
        logger.warning("No devices found — skip financial seed")
        return

    tenant_id = devices[0].get("tenant_id")
    site_map = {s["id"]: s["name"] for s in sites}

    # --- Generate 50 player profiles ---
    players = []
    for i in range(50):
        players.append({
            "id": f"PL-{20000 + i}",
            "name": f"{random.choice(PLAYER_FIRST)} {random.choice(PLAYER_LAST)}",
            "tier": random.choice(["Bronze", "Silver", "Gold", "Platinum", "Diamond"]),
            "member_since": _past(8760),
            "total_visits": random.randint(5, 500),
        })

    # --- Financial Events (1200 records over 72 hours) ---
    fin_events = []
    event_types_weights = [
        ("wager", 40), ("payout", 30), ("voucher_in", 5), ("voucher_out", 5),
        ("bill_in", 10), ("jackpot", 2), ("bonus", 3), ("handpay", 1),
    ]
    types_list = [t for t, _ in event_types_weights]
    weights_list = [w for _, w in event_types_weights]

    for _ in range(1200):
        device = random.choice(devices)
        etype = random.choices(types_list, weights=weights_list, k=1)[0]
        player = random.choice(players) if random.random() > 0.3 else None
        denom = device.get("metadata", {}).get("denomination", 0.25)
        game = device.get("metadata", {}).get("game_title", "Unknown")
        occurred = _past(72)

        if etype == "wager":
            amount = round(denom * random.randint(1, 20) * random.choice([1, 2, 3, 5]), 2)
        elif etype == "payout":
            amount = round(random.uniform(0.5, 800.0), 2)
        elif etype in ("voucher_in", "voucher_out"):
            amount = round(random.choice([5, 10, 20, 50, 100, 200, 500]) + random.uniform(0, 0.99), 2)
        elif etype == "bill_in":
            amount = float(random.choice([1, 5, 10, 20, 50, 100]))
        elif etype == "jackpot":
            amount = round(random.uniform(500, 25000), 2)
        elif etype == "handpay":
            amount = round(random.uniform(1200, 50000), 2)
        elif etype == "bonus":
            amount = round(random.uniform(5, 500), 2)
        else:
            amount = round(random.uniform(1, 100), 2)

        fin_events.append({
            "id": _id(),
            "tenant_id": tenant_id,
            "site_id": device.get("site_id"),
            "site_name": site_map.get(device.get("site_id"), ""),
            "device_id": device["id"],
            "device_ref": device["external_ref"],
            "event_type": etype,
            "amount": amount,
            "currency": "USD",
            "player_id": player["id"] if player else None,
            "player_name": player["name"] if player else None,
            "game_title": game,
            "denomination": denom,
            "occurred_at": occurred,
            "correlation_id": _id(),
            "schema_version": 1,
        })

    fin_events.sort(key=lambda e: e["occurred_at"], reverse=True)
    await db.financial_events.insert_many(fin_events)

    # --- Player Sessions (120 sessions over 72 hours) ---
    sessions = []
    for _ in range(120):
        player = random.choice(players)
        device = random.choice(devices)
        hours_ago = random.uniform(0, 72)
        card_in = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        duration = random.randint(5, 240)
        is_active = hours_ago < 2 and random.random() > 0.6
        card_out = None if is_active else (card_in + timedelta(minutes=duration))

        games = random.randint(10, duration * 4)
        avg_bet = random.uniform(0.5, 25.0)
        total_wagered = round(games * avg_bet, 2)
        house_edge = random.uniform(0.02, 0.12)
        total_won = round(total_wagered * (1 - house_edge + random.uniform(-0.3, 0.3)), 2)
        net = round(total_won - total_wagered, 2)

        game_set = random.sample(GAME_NAMES, min(random.randint(1, 4), len(GAME_NAMES)))

        sessions.append({
            "id": _id(),
            "tenant_id": tenant_id,
            "site_id": device.get("site_id"),
            "site_name": site_map.get(device.get("site_id"), ""),
            "device_id": device["id"],
            "device_ref": device["external_ref"],
            "player_id": player["id"],
            "player_name": player["name"],
            "player_tier": player["tier"],
            "card_in_at": card_in.isoformat(),
            "card_out_at": card_out.isoformat() if card_out else None,
            "duration_minutes": duration if not is_active else int((datetime.now(timezone.utc) - card_in).total_seconds() / 60),
            "status": "active" if is_active else "completed",
            "games_played": games,
            "total_wagered": total_wagered,
            "total_won": total_won,
            "net_result": net,
            "game_titles": game_set,
            "denomination": device.get("metadata", {}).get("denomination", 0.25),
            "loyalty_points_earned": random.randint(10, games * 5),
            "vouchers_used": random.randint(0, 3),
            "bonuses_triggered": random.randint(0, 5),
        })

    sessions.sort(key=lambda s: s["card_in_at"], reverse=True)
    await db.player_sessions.insert_many(sessions)

    # Indexes
    await db.financial_events.create_index([("occurred_at", -1)])
    await db.financial_events.create_index("event_type")
    await db.financial_events.create_index("device_id")
    await db.financial_events.create_index("player_id")
    await db.player_sessions.create_index([("card_in_at", -1)])
    await db.player_sessions.create_index("player_id")
    await db.player_sessions.create_index("status")

    logger.info(f"Seeded: {len(fin_events)} financial events, {len(sessions)} player sessions, {len(players)} player profiles")
