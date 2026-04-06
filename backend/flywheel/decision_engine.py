"""
FlywheelOS Decision Engine — NBA scoring, policy enforcement, action approval.
Converts candidates into approved actions.
"""
import logging
from datetime import datetime, timezone
from flywheel import config as cfg
from flywheel.storage import get_action_count_today, get_last_action_for_rule
from flywheel.actor_profile import _parse_iso

logger = logging.getLogger(__name__)


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def score_candidate(candidate: dict, profile: dict) -> dict:
    """
    Apply multi-factor scoring formula:
    score = (priority × 0.25) + (relevance × 0.25) + (urgency × 0.20)
          + (channel_confidence × 0.15) + (tier_bonus × 0.15) − fatigue_penalty
    """
    # Extract inputs
    priority = min(candidate.get("urgency", 0.5), 1.0)  # rule priority normalized
    # Use rule-level priority from the candidate's source
    rule_priority = 0.5
    # Try to infer from candidate data
    if "score_components" in candidate and "rule_priority" in candidate["score_components"]:
        rule_priority = candidate["score_components"]["rule_priority"]

    relevance = min(candidate.get("relevance", 0.5), 1.0)
    urgency = min(candidate.get("urgency", 0.5), 1.0)

    # Channel confidence: in_app_surface is best (player is AT the EGM)
    channel = candidate.get("channel", "in_app_surface")
    channel_conf = {"in_app_surface": 1.0, "in_app_inbox": 0.7, "websocket": 0.5}.get(channel, 0.5)

    # Tier bonus: normalize multiplier (1.0→2.0 maps to 0.0→1.0)
    tier_mult = profile.get("tier_multiplier", 1.0)
    tier_bonus = min((tier_mult - 1.0) / 1.0, 1.0)  # 0.0 for bronze, 1.0 for diamond

    # Fatigue penalty
    fatigue = profile.get("fatigue_score", 0.0) * cfg.SCORE_FATIGUE_MULT

    # Compute
    score = (
        rule_priority * cfg.SCORE_W_PRIORITY
        + relevance * cfg.SCORE_W_RELEVANCE
        + urgency * cfg.SCORE_W_URGENCY
        + channel_conf * cfg.SCORE_W_CHANNEL
        + tier_bonus * cfg.SCORE_W_TIER
        - fatigue
    )
    score = max(0.0, min(1.0, score))

    candidate["score"] = round(score, 4)
    candidate["score_components"] = {
        "rule_priority": round(rule_priority, 3),
        "relevance": round(relevance, 3),
        "urgency": round(urgency, 3),
        "channel_confidence": round(channel_conf, 3),
        "tier_bonus": round(tier_bonus, 3),
        "fatigue_penalty": round(fatigue, 3),
        "final": round(score, 4),
    }
    return candidate


async def enforce_policies(candidate: dict, profile: dict) -> tuple[bool, str]:
    """
    Apply 6 policy checks in order. Returns (approved: bool, reason: str).
    """
    actor_id = profile.get("actor_id", "")

    # 1. Global daily cap
    actions_today = profile.get("actions_today", 0)
    if actions_today >= cfg.GLOBAL_DAILY_CAP:
        return False, "global_daily_cap_exceeded"

    # 2. Per-rule frequency cap
    rule_key = candidate.get("rule_key", "")
    if rule_key:
        last = await get_last_action_for_rule(actor_id, rule_key)
        if last and last.get("created_at"):
            cap_hours = 24.0  # default
            # Read from rule metadata if available
            since = _parse_iso(last["created_at"])
            hours_elapsed = (_now_dt() - since).total_seconds() / 3600
            if hours_elapsed < cap_hours:
                return False, f"per_rule_cap_{rule_key}"

    # 3. Anomaly suppression
    suppressed = profile.get("suppressed_until")
    if suppressed:
        sup_dt = _parse_iso(suppressed)
        if _now_dt() < sup_dt:
            return False, "anomaly_suppression"

    # 4. Quiet hours (configurable; default None = no quiet hours for 24/7 gaming)
    if cfg.DEFAULT_QUIET_HOURS_START is not None:
        current_hour = _now_dt().hour
        start = cfg.DEFAULT_QUIET_HOURS_START
        end = cfg.DEFAULT_QUIET_HOURS_END or 6
        if start <= current_hour or current_hour < end:
            return False, "quiet_hours"

    # 5. Channel availability — device must be online for in_app_surface
    channel = candidate.get("channel", "in_app_surface")
    if channel == "in_app_surface":
        device_id = candidate.get("target_device_id", "")
        if device_id:
            from database import db
            twin = await db.device_state_projection.find_one(
                {"device_id": device_id}, {"_id": 0, "operational_state": 1}
            )
            if twin and twin.get("operational_state") not in ("ONLINE", None):
                return False, "device_offline"

    # 6. Channel opt-in
    opted = profile.get("opted_in_channels", ["in_app_surface", "in_app_inbox"])
    if channel not in opted and channel != "in_app_surface":
        return False, "channel_opt_out"

    return True, "approved"


async def decide(candidates: list[dict], profile: dict) -> dict | None:
    """
    Top-level NBA: score all candidates, rank, enforce policies, return best or None.
    """
    if not candidates:
        return None

    # Score each candidate
    scored = [score_candidate(c, profile) for c in candidates]

    # Filter below threshold
    scored = [c for c in scored if c.get("score", 0) >= cfg.SCORE_MIN_THRESHOLD]

    # Sort by score descending
    scored.sort(key=lambda c: c.get("score", 0), reverse=True)

    # Apply policies to each in order until one passes
    for candidate in scored:
        approved, reason = await enforce_policies(candidate, profile)
        if approved:
            candidate["status"] = "approved"
            candidate["policies_passed"] = [
                "global_cap", "per_rule_cap", "suppression", "quiet_hours", "channel", "opt_in"
            ]
            candidate["decision_rationale"] = (
                f"Score {candidate['score']:.3f} "
                f"(pri={candidate['score_components']['rule_priority']:.2f} "
                f"rel={candidate['score_components']['relevance']:.2f} "
                f"urg={candidate['score_components']['urgency']:.2f} "
                f"ch={candidate['score_components']['channel_confidence']:.2f} "
                f"tier={candidate['score_components']['tier_bonus']:.2f} "
                f"-fat={candidate['score_components']['fatigue_penalty']:.2f})"
            )
            return candidate
        else:
            candidate["status"] = "rejected"
            candidate["policies_blocked_by"] = reason
            logger.debug(f"Candidate {candidate.get('rule_key')} rejected: {reason}")

    return None
