"""
FlywheelOS API Routes — admin console, rule management, action queue, analytics, engine control.
"""
from fastapi import APIRouter, Request, HTTPException
from typing import Optional
from datetime import datetime, timezone
from database import db
from auth import get_current_user, require_role
from flywheel import flywheel_engine
from flywheel.storage import (
    get_all_rules, get_recent_logs, save_rule, get_config, save_config,
    get_action, update_action
)
from flywheel.actor_profile import get_actor_profile
from flywheel.rule_engine import evaluate_event, evaluate_scheduled
from flywheel.decision_engine import decide
from flywheel.reward_ledger import get_flywheel_rewards, reverse_reward

router = APIRouter(prefix="/api/flywheel", tags=["flywheel"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Dashboard ──
@router.get("/dashboard")
async def dashboard(request: Request):
    await get_current_user(request)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()

    actions_today = await db.flywheel_actions.count_documents(
        {"created_at": {"$gte": today_start}}
    )
    actions_approved = await db.flywheel_actions.count_documents(
        {"created_at": {"$gte": today_start}, "status": {"$in": ["approved", "dispatched", "delivered"]}}
    )
    actions_rejected = await db.flywheel_actions.count_documents(
        {"created_at": {"$gte": today_start}, "status": "rejected"}
    )
    poc_today_pipe = [
        {"$match": {"created_at": {"$gte": today_start}, "flywheel_action_id": {"$exists": True, "$ne": ""}}},
        {"$group": {"_id": None, "total": {"$sum": "$poc_amount"}, "count": {"$sum": 1}}},
    ]
    poc_agg = await db.poc_awards.aggregate(poc_today_pipe).to_list(1)
    poc_data = poc_agg[0] if poc_agg else {"total": 0, "count": 0}

    events_today = await db.flywheel_events.count_documents(
        {"occurred_at": {"$gte": today_start}}
    )
    profiles_total = await db.flywheel_profiles.count_documents({})
    rules_active = await db.flywheel_rules.count_documents({"enabled": True})

    # Lifecycle distribution
    lifecycle_pipe = [
        {"$group": {"_id": "$lifecycle_stage", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    lifecycle = await db.flywheel_profiles.aggregate(lifecycle_pipe).to_list(10)

    # Top families today
    family_pipe = [
        {"$match": {"created_at": {"$gte": today_start}}},
        {"$group": {"_id": "$family", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    families = await db.flywheel_actions.aggregate(family_pipe).to_list(10)

    return {
        "actions_today": actions_today,
        "actions_approved": actions_approved,
        "actions_rejected": actions_rejected,
        "poc_awarded_today": round(poc_data.get("total", 0), 2),
        "poc_count_today": poc_data.get("count", 0),
        "events_today": events_today,
        "profiles_total": profiles_total,
        "rules_active": rules_active,
        "lifecycle_distribution": [{"stage": l["_id"], "count": l["count"]} for l in lifecycle],
        "top_families": [{"family": f["_id"], "count": f["count"]} for f in families],
        "engine": flywheel_engine.get_status(),
    }


# ── Rules ──
@router.get("/rules")
async def list_rules(request: Request):
    await get_current_user(request)
    rules = await get_all_rules()
    return {"rules": rules, "total": len(rules)}


@router.post("/rules")
async def create_rule(request: Request):
    user = await require_role(request, ["admin", "operator"])
    body = await request.json()
    if not body.get("key") or not body.get("family"):
        raise HTTPException(400, "key and family are required")
    body.setdefault("app_id", "ugg")
    body.setdefault("enabled", True)
    await save_rule(body)
    return {"created": True, "key": body["key"]}


@router.put("/rules/{rule_key}")
async def update_rule(rule_key: str, request: Request):
    await require_role(request, ["admin", "operator"])
    body = await request.json()
    body["key"] = rule_key
    body.setdefault("app_id", "ugg")
    await save_rule(body)
    return {"updated": True}


@router.post("/rules/{rule_key}/toggle")
async def toggle_rule(rule_key: str, request: Request):
    await require_role(request, ["admin", "operator"])
    rule = await db.flywheel_rules.find_one({"key": rule_key}, {"_id": 0})
    if not rule:
        raise HTTPException(404, "Rule not found")
    new_enabled = not rule.get("enabled", True)
    await db.flywheel_rules.update_one({"key": rule_key}, {"$set": {"enabled": new_enabled}})
    return {"key": rule_key, "enabled": new_enabled}


# ── Actions ──
@router.get("/actions")
async def list_actions(
    request: Request,
    status: Optional[str] = None,
    family: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    await get_current_user(request)
    query = {}
    if status:
        query["status"] = status
    if family:
        query["family"] = family
    actions = await db.flywheel_actions.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.flywheel_actions.count_documents(query)
    return {"actions": actions, "total": total}


@router.get("/actions/{action_id}")
async def get_action_detail(action_id: str, request: Request):
    await get_current_user(request)
    action = await get_action(action_id)
    if not action:
        raise HTTPException(404, "Action not found")
    return action


@router.post("/actions/{action_id}/approve")
async def approve_action(action_id: str, request: Request):
    await require_role(request, ["admin", "operator"])
    await update_action(action_id, {"status": "approved", "approved_at": _now()})
    return {"approved": True}


@router.post("/actions/{action_id}/reject")
async def reject_action(action_id: str, request: Request):
    await require_role(request, ["admin", "operator"])
    await update_action(action_id, {"status": "rejected", "rejected_at": _now()})
    return {"rejected": True}


# ── Profiles ──
@router.get("/profiles")
async def list_profiles(
    request: Request,
    lifecycle_stage: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    await get_current_user(request)
    query = {}
    if lifecycle_stage:
        query["lifecycle_stage"] = lifecycle_stage
    profiles = await db.flywheel_profiles.find(query, {"_id": 0}).sort("updated_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.flywheel_profiles.count_documents(query)
    return {"profiles": profiles, "total": total}


@router.get("/profiles/{player_id}")
async def get_profile_detail(player_id: str, request: Request):
    await get_current_user(request)
    profile = await get_actor_profile(player_id)
    return profile


@router.get("/profiles/{player_id}/nba")
async def get_player_nba(player_id: str, request: Request):
    """Get the current NBA recommendation for a specific player."""
    await get_current_user(request)
    profile = await get_actor_profile(player_id)
    # Try scheduled rules evaluation for this player
    candidates = await evaluate_scheduled(profile)
    if not candidates:
        return {"recommendation": None, "reason": "No rules matched"}
    action = await decide(candidates, profile)
    if not action:
        return {"recommendation": None, "reason": "All candidates suppressed by policy"}
    return {"recommendation": action}


# ── Deliveries ──
@router.get("/deliveries")
async def list_deliveries(request: Request, limit: int = 50, skip: int = 0):
    await get_current_user(request)
    deliveries = await db.flywheel_deliveries.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.flywheel_deliveries.count_documents({})
    return {"deliveries": deliveries, "total": total}


# ── Rewards ──
@router.get("/rewards")
async def list_rewards(request: Request, limit: int = 50, skip: int = 0):
    await get_current_user(request)
    rewards, total = await get_flywheel_rewards(limit, skip)
    return {"rewards": rewards, "total": total}


@router.post("/rewards/{award_id}/reverse")
async def reverse_reward_route(award_id: str, request: Request):
    user = await require_role(request, ["admin"])
    body = await request.json()
    reason = body.get("reason", "Admin reversal")
    ok = await reverse_reward(award_id, reason)
    if not ok:
        raise HTTPException(400, "Cannot reverse this reward")
    return {"reversed": True}


# ── Config ──
@router.get("/config")
async def get_engine_config(request: Request):
    await get_current_user(request)
    cfg = await get_config()
    return cfg or {"message": "Using defaults (no overrides stored)"}


@router.put("/config")
async def update_config(request: Request):
    await require_role(request, ["admin"])
    body = await request.json()
    await save_config(body)
    return {"updated": True}


# ── Engine Control ──
@router.get("/status")
async def engine_status(request: Request):
    await get_current_user(request)
    return flywheel_engine.get_status()


@router.post("/engine/pause")
async def pause_engine(request: Request):
    await require_role(request, ["admin"])
    flywheel_engine.workers.pause()
    return {"paused": True}


@router.post("/engine/resume")
async def resume_engine(request: Request):
    await require_role(request, ["admin"])
    flywheel_engine.workers.resume()
    return {"resumed": True}


@router.post("/engine/run-now/{worker_name}")
async def run_worker_now(worker_name: str, request: Request):
    await require_role(request, ["admin"])
    result = await flywheel_engine.workers.run_one(worker_name)
    return result


# ── Execution Logs ──
@router.get("/logs")
async def list_logs(request: Request, limit: int = 50):
    await get_current_user(request)
    logs = await get_recent_logs(limit)
    return {"logs": logs, "total": len(logs)}


# ── NBA for active sessions (consumed by PinSessionsPage) ──
@router.get("/nba/active-sessions")
async def nba_active_sessions(request: Request):
    """Returns NBA recommendation for every active PIN session."""
    await get_current_user(request)
    active_pins = await db.pin_sessions.find({"is_active": True}, {"_id": 0}).limit(200).to_list(200)
    results = []
    for ps in active_pins:
        player_id = ps.get("player_id")
        if not player_id:
            continue
        try:
            profile = await get_actor_profile(player_id)
            candidates = await evaluate_scheduled(profile)
            action = await decide(candidates, profile) if candidates else None
            results.append({
                "player_id": player_id,
                "player_name": ps.get("player_name", ""),
                "device_id": ps.get("device_id", ""),
                "recommendation": {
                    "family": action.get("family", "") if action else None,
                    "rule_key": action.get("rule_key", "") if action else None,
                    "poc_amount": action.get("poc_amount", 0) if action else 0,
                    "score": action.get("score", 0) if action else 0,
                    "message": action.get("message_template", "") if action else None,
                } if action else None,
            })
        except Exception:
            results.append({"player_id": player_id, "recommendation": None})
    return {"sessions": results, "total": len(results)}
