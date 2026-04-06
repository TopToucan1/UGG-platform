"""
FlywheelOS MongoDB Storage — helpers for all flywheel collections.
"""
import uuid
from datetime import datetime, timezone
from database import db


def _id() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Events ──
async def save_event(event: dict) -> None:
    event.setdefault("id", _id())
    event.setdefault("received_at", _now())
    event.pop("_id", None)
    await db.flywheel_events.insert_one(dict(event))


async def get_event(event_id: str) -> dict | None:
    return await db.flywheel_events.find_one({"id": event_id}, {"_id": 0})


# ── Profiles ──
async def upsert_profile(actor_id: str, data: dict) -> None:
    data["updated_at"] = _now()
    await db.flywheel_profiles.update_one(
        {"actor_id": actor_id}, {"$set": data}, upsert=True
    )


async def get_profile(actor_id: str) -> dict | None:
    return await db.flywheel_profiles.find_one({"actor_id": actor_id}, {"_id": 0})


async def query_profiles(query: dict, limit: int = 500) -> list[dict]:
    return await db.flywheel_profiles.find(query, {"_id": 0}).limit(limit).to_list(limit)


# ── Rules ──
async def save_rule(rule: dict) -> None:
    rule.setdefault("id", _id())
    rule.pop("_id", None)
    await db.flywheel_rules.update_one(
        {"key": rule["key"], "app_id": rule.get("app_id", "ugg")},
        {"$set": rule}, upsert=True
    )


async def get_rule(rule_key: str) -> dict | None:
    return await db.flywheel_rules.find_one({"key": rule_key}, {"_id": 0})


async def get_rules_for_event(event_family: str) -> list[dict]:
    return await db.flywheel_rules.find(
        {"trigger_type": "event", "trigger_events": event_family, "enabled": True},
        {"_id": 0}
    ).to_list(100)


async def get_scheduled_rules() -> list[dict]:
    return await db.flywheel_rules.find(
        {"trigger_type": "scheduled", "enabled": True}, {"_id": 0}
    ).to_list(100)


async def get_all_rules() -> list[dict]:
    return await db.flywheel_rules.find({}, {"_id": 0}).to_list(200)


# ── Actions ──
async def save_action(action: dict) -> None:
    action.setdefault("id", _id())
    action.setdefault("created_at", _now())
    action.pop("_id", None)
    await db.flywheel_actions.insert_one(dict(action))


async def get_action(action_id: str) -> dict | None:
    return await db.flywheel_actions.find_one({"id": action_id}, {"_id": 0})


async def update_action(action_id: str, updates: dict) -> None:
    await db.flywheel_actions.update_one({"id": action_id}, {"$set": updates})


async def get_actions_for_actor(actor_id: str, limit: int = 20) -> list[dict]:
    return await db.flywheel_actions.find(
        {"actor_id": actor_id}, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)


async def get_action_count_today(actor_id: str) -> int:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()
    return await db.flywheel_actions.count_documents(
        {"actor_id": actor_id, "status": {"$in": ["approved", "dispatched", "delivered"]},
         "created_at": {"$gte": today_start}}
    )


async def get_last_action_for_rule(actor_id: str, rule_key: str) -> dict | None:
    return await db.flywheel_actions.find_one(
        {"actor_id": actor_id, "rule_key": rule_key,
         "status": {"$in": ["approved", "dispatched", "delivered"]}},
        {"_id": 0}, sort=[("created_at", -1)]
    )


async def get_pending_actions(limit: int = 100) -> list[dict]:
    return await db.flywheel_actions.find(
        {"status": "approved", "immediate": False}, {"_id": 0}
    ).sort("score", -1).limit(limit).to_list(limit)


# ── Deliveries ──
async def save_delivery(delivery: dict) -> None:
    delivery.setdefault("id", _id())
    delivery.setdefault("created_at", _now())
    delivery.pop("_id", None)
    await db.flywheel_deliveries.insert_one(dict(delivery))


async def update_delivery(delivery_id: str, updates: dict) -> None:
    await db.flywheel_deliveries.update_one({"id": delivery_id}, {"$set": updates})


# ── Execution Logs ──
async def save_execution_log(log: dict) -> None:
    log.setdefault("id", _id())
    log.pop("_id", None)
    await db.flywheel_execution_logs.insert_one(dict(log))


async def update_execution_log(log_id: str, updates: dict) -> None:
    await db.flywheel_execution_logs.update_one({"id": log_id}, {"$set": updates})


async def get_recent_logs(limit: int = 50) -> list[dict]:
    return await db.flywheel_execution_logs.find(
        {}, {"_id": 0}
    ).sort("started_at", -1).limit(limit).to_list(limit)


# ── Config ──
async def get_config() -> dict:
    cfg = await db.flywheel_config.find_one({"app_id": "ugg"}, {"_id": 0})
    return cfg or {}


async def save_config(config: dict) -> None:
    config["app_id"] = "ugg"
    await db.flywheel_config.update_one({"app_id": "ugg"}, {"$set": config}, upsert=True)


# ── Inbox ──
async def save_inbox_message(msg: dict) -> None:
    msg.setdefault("id", _id())
    msg.setdefault("created_at", _now())
    msg.setdefault("is_read", False)
    msg.pop("_id", None)
    await db.flywheel_inbox.insert_one(dict(msg))


# ── Indexes ──
async def ensure_indexes() -> None:
    await db.flywheel_events.create_index("id", unique=True)
    await db.flywheel_events.create_index([("actor_id", 1), ("occurred_at", -1)])
    await db.flywheel_events.create_index("event_family")

    await db.flywheel_profiles.create_index("actor_id", unique=True)
    await db.flywheel_profiles.create_index("lifecycle_stage")

    await db.flywheel_rules.create_index("id", unique=True)
    await db.flywheel_rules.create_index([("key", 1), ("app_id", 1)], unique=True)
    await db.flywheel_rules.create_index("family")

    await db.flywheel_actions.create_index("id", unique=True)
    await db.flywheel_actions.create_index([("actor_id", 1), ("created_at", -1)])
    await db.flywheel_actions.create_index("status")
    await db.flywheel_actions.create_index([("rule_key", 1), ("actor_id", 1)])

    await db.flywheel_deliveries.create_index("id", unique=True)
    await db.flywheel_deliveries.create_index("status")

    await db.flywheel_execution_logs.create_index([("worker_name", 1), ("started_at", -1)])

    await db.flywheel_inbox.create_index([("player_id", 1), ("created_at", -1)])

    await db.flywheel_config.create_index("app_id", unique=True)
