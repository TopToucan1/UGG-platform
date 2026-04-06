"""
FlywheelOS Reward Ledger — idempotent POC reward lifecycle.
Maps to the existing poc_awards collection with flywheel-specific status tracking.
Lifecycle: pending → verified → settled (or → reversed)
"""
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from database import db
from flywheel.actor_profile import get_tier
from flywheel import config as cfg

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_idempotency_key(actor_id: str, rule_key: str, session_id: str = "") -> str:
    """SHA256-based idempotency key: one reward per actor+rule+session+date."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw = f"{actor_id}:{rule_key}:{session_id}:{date_str}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


async def create_reward(action: dict, profile: dict) -> dict | None:
    """
    Create an idempotent POC reward entry.
    Returns the award doc, or None if already exists (idempotent skip).
    """
    poc_base = action.get("poc_amount", 0)
    if poc_base <= 0:
        return None

    actor_id = profile.get("actor_id", "")
    rule_key = action.get("rule_key", "")
    session_id = action.get("object_id", "")

    idemp_key = _make_idempotency_key(actor_id, rule_key, session_id)

    # Check idempotency
    existing = await db.poc_awards.find_one({"flywheel_idempotency_key": idemp_key})
    if existing:
        logger.debug(f"Reward idempotency hit: {idemp_key}")
        return None

    # Apply tier multiplier
    churn = profile.get("churn_score", 50)
    tier = get_tier(churn)
    final_amount = round(poc_base * tier["poc_multiplier"], 2)

    award = {
        "id": str(uuid.uuid4()),
        "player_id": actor_id,
        "player_name": profile.get("player_name", ""),
        "egm_id": action.get("target_device_id", ""),
        "trigger_type": f"flywheel_{action.get('family', '')}",
        "rule_id": action.get("rule_id", ""),
        "rule_name": action.get("rule_name", action.get("rule_key", "")),
        "poc_amount": final_amount,
        "poc_type": "play_only_credits",
        "churn_score_at_award": churn,
        "tier_at_award": tier["id"],
        "tier_multiplier": tier["poc_multiplier"],
        "message_text": action.get("rendered_message", action.get("message_template", "")),
        "delivery_status": "pending",
        # FlywheelOS-specific fields
        "flywheel_status": "pending",  # pending → verified → settled → reversed
        "flywheel_action_id": action.get("id", ""),
        "flywheel_idempotency_key": idemp_key,
        "flywheel_family": action.get("family", ""),
        "awarded_by": "FLYWHEEL_ENGINE",
        "created_at": _now(),
    }

    await db.poc_awards.insert_one(dict(award))

    # Auto-settle if configured (v1 default: yes)
    if cfg.REWARD_AUTO_SETTLE:
        await db.poc_awards.update_one(
            {"id": award["id"]},
            {"$set": {"flywheel_status": "settled", "delivery_status": "delivered"}}
        )
        award["flywheel_status"] = "settled"

    # Update player totals in PIRS
    await db.pirs_players.update_one(
        {"player_id": actor_id},
        {"$inc": {"total_poc_awarded": final_amount, "poc_awards_count": 1}},
        upsert=True,
    )

    logger.info(f"FlywheelOS reward: ${final_amount:.2f} POC to {actor_id} via {rule_key} (tier={tier['id']} x{tier['poc_multiplier']})")
    return award


async def reverse_reward(award_id: str, reason: str = "") -> bool:
    """Reverse a settled reward. Returns True if reversed."""
    award = await db.poc_awards.find_one({"id": award_id}, {"_id": 0})
    if not award:
        return False
    if award.get("flywheel_status") not in ("pending", "verified", "settled"):
        return False

    await db.poc_awards.update_one(
        {"id": award_id},
        {"$set": {
            "flywheel_status": "reversed",
            "delivery_status": "reversed",
            "reversed_at": _now(),
            "reverse_reason": reason,
        }}
    )
    # Decrement player totals
    await db.pirs_players.update_one(
        {"player_id": award.get("player_id")},
        {"$inc": {"total_poc_awarded": -award.get("poc_amount", 0), "poc_awards_count": -1}},
    )
    logger.info(f"FlywheelOS reward reversed: {award_id} reason={reason}")
    return True


async def get_pending_rewards(limit: int = 50) -> list[dict]:
    """Get rewards needing verification (if manual verification is enabled)."""
    return await db.poc_awards.find(
        {"flywheel_status": "pending", "flywheel_action_id": {"$exists": True}},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)


async def get_flywheel_rewards(limit: int = 100, skip: int = 0) -> tuple[list[dict], int]:
    """Get all flywheel-sourced rewards."""
    query = {"flywheel_action_id": {"$exists": True, "$ne": ""}}
    rewards = await db.poc_awards.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.poc_awards.count_documents(query)
    return rewards, total
