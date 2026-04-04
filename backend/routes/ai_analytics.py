"""
Phase 7 — AI-Powered Analytics Portal.
Predictive maintenance, NOR forecasting, exception pattern analysis,
device health predictions, and natural language query interface.
All powered by Gemini 3 Flash via Emergent Integrations.
"""
from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import os
import uuid
import json
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai-analytics", tags=["ai-analytics"])


async def _call_gemini(prompt: str, system_msg: str = None) -> str:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="LLM key not configured")
    chat = LlmChat(api_key=api_key, session_id=f"ugg-analytics-{uuid.uuid4().hex[:8]}", system_message=system_msg or "You are the UGG AI Analytics engine. Analyze gaming operations data and provide actionable insights. Be concise and data-driven. Use specific numbers.")
    chat.with_model("gemini", "gemini-3-flash-preview")
    return await chat.send_message(UserMessage(text=prompt))


async def _gather_estate_context() -> str:
    """Gather current estate data as context for AI queries."""
    device_count = await db.devices.count_documents({})
    online = await db.devices.count_documents({"status": "online"})
    offline = await db.devices.count_documents({"status": "offline"})
    error = await db.devices.count_documents({"status": "error"})
    events = await db.events.count_documents({})
    active_exc = await db.route_exceptions.count_documents({"is_active": True})
    critical_exc = await db.route_exceptions.count_documents({"is_active": True, "severity": "CRITICAL"})

    # NOR data
    d30 = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    nor_pipe = [{"$match": {"period_start": {"$gte": d30}}}, {"$group": {"_id": None, "nor": {"$sum": "$net_operating_revenue"}, "coin_in": {"$sum": "$coin_in"}, "tax": {"$sum": "$tax_amount"}}}]
    nor = await db.route_nor_periods.aggregate(nor_pipe).to_list(1)
    nor_data = nor[0] if nor else {}

    # Top exceptions
    exc_pipe = [{"$match": {"is_active": True}}, {"$group": {"_id": "$type", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 5}]
    top_exc = await db.route_exceptions.aggregate(exc_pipe).to_list(5)

    # Device health from digital twin
    twin_pipe = [{"$group": {"_id": None, "avg_health": {"$avg": {"$ifNull": ["$health_score", 0]}}, "low_health": {"$sum": {"$cond": [{"$lt": [{"$ifNull": ["$health_score", 100]}, 70]}, 1, 0]}}}}]
    twin = await db.device_state_projection.aggregate(twin_pipe).to_list(1)
    twin_data = twin[0] if twin else {}

    return f"""UGG Estate Status:
- Devices: {device_count} total ({online} online, {offline} offline, {error} error)
- Events: {events} canonical events
- Active Exceptions: {active_exc} ({critical_exc} critical)
- Top Exception Types: {json.dumps([{"type": e["_id"], "count": e["count"]} for e in top_exc])}
- 30-day NOR: ${nor_data.get('nor', 0):,} | Coin In: ${nor_data.get('coin_in', 0):,} | Tax: ${nor_data.get('tax', 0):,}
- Device Health: avg {round(twin_data.get('avg_health', 0) or 0, 1)}% | {twin_data.get('low_health', 0)} devices below 70%"""


# ══════════════════════════════════════════════════
# PREDICTIVE MAINTENANCE
# ══════════════════════════════════════════════════

@router.post("/predictive-maintenance")
async def predictive_maintenance(request: Request):
    """AI-powered predictive maintenance analysis."""
    user = await get_current_user(request)
    context = await _gather_estate_context()

    # Get devices with low health or high error counts
    low_health = await db.device_state_projection.find({"health_score": {"$lt": 80}}, {"_id": 0, "device_id": 1, "device_ref": 1, "health_score": 1, "operational_state": 1, "last_event_at": 1}).sort("health_score", 1).limit(15).to_list(15)
    recent_errors = await db.route_exceptions.find({"is_active": True, "severity": "CRITICAL"}, {"_id": 0, "device_ref": 1, "type": 1, "detail": 1, "raised_at": 1}).sort("raised_at", -1).limit(10).to_list(10)

    prompt = f"""{context}

Low Health Devices (< 80%):
{json.dumps(low_health, default=str)}

Recent Critical Exceptions:
{json.dumps(recent_errors, default=str)}

Based on this data, provide:
1. IMMEDIATE ACTIONS: Devices most likely to fail in the next 24-48 hours with probability estimates
2. PATTERN ANALYSIS: Common failure patterns across device types, manufacturers, or locations
3. MAINTENANCE SCHEDULE: Recommended proactive maintenance priorities (rank by urgency)
4. ROOT CAUSES: Likely root causes for the most common exception types
5. COST IMPACT: Estimated revenue impact if these devices go offline

Be specific with device IDs and percentages. Format as structured analysis."""

    try:
        result = await _call_gemini(prompt, "You are a predictive maintenance AI for gaming operations. Analyze device health data and predict failures before they happen. Be specific with device references and probability estimates.")
        record = {"id": str(uuid.uuid4()), "type": "predictive_maintenance", "result": result, "device_count": len(low_health), "exception_count": len(recent_errors), "created_by": user.get("email"), "created_at": datetime.now(timezone.utc).isoformat()}
        await db.ai_analytics_results.insert_one(record)
        record.pop("_id", None)
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════
# NOR FORECASTING
# ══════════════════════════════════════════════════

@router.post("/nor-forecast")
async def nor_forecast(request: Request):
    """AI-powered NOR revenue forecasting."""
    user = await get_current_user(request)
    context = await _gather_estate_context()

    # Get daily NOR trend
    d30 = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    trend_pipe = [{"$match": {"period_start": {"$gte": d30}}}, {"$group": {"_id": "$period_start", "nor": {"$sum": "$net_operating_revenue"}, "coin_in": {"$sum": "$coin_in"}}}, {"$sort": {"_id": 1}}]
    trend = await db.route_nor_periods.aggregate(trend_pipe).to_list(60)

    # Per-distributor NOR
    dist_pipe = [{"$match": {"period_start": {"$gte": d30}}}, {"$group": {"_id": "$distributor_id", "nor": {"$sum": "$net_operating_revenue"}, "devices": {"$addToSet": "$device_id"}}}, {"$sort": {"nor": -1}}]
    dist_nor = await db.route_nor_periods.aggregate(dist_pipe).to_list(10)
    dists = {d["id"]: d["name"] for d in await db.route_distributors.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(10)}

    prompt = f"""{context}

30-Day Daily NOR Trend:
{json.dumps([{"date": t["_id"], "nor": t["nor"], "coin_in": t["coin_in"]} for t in trend], default=str)}

NOR by Distributor (30 days):
{json.dumps([{"distributor": dists.get(d["_id"], "Unknown"), "nor": d["nor"], "devices": len(d["devices"])} for d in dist_nor], default=str)}

Based on this data, provide:
1. 7-DAY FORECAST: Predicted NOR for each of the next 7 days with confidence intervals
2. 30-DAY FORECAST: Predicted total NOR for the next 30 days
3. TREND ANALYSIS: Is revenue trending up, down, or stable? What's the growth rate?
4. DISTRIBUTOR INSIGHTS: Which distributors are outperforming/underperforming and why?
5. RISK FACTORS: What could cause NOR to decline (seasonal, device health, offline devices)?
6. OPTIMIZATION: Specific actions to increase NOR by 5-10%

Use actual dollar amounts and percentages from the data."""

    try:
        result = await _call_gemini(prompt, "You are a revenue forecasting AI for gaming operations. Analyze NOR (Net Operating Revenue) trends and provide actionable forecasts. Use specific dollar amounts and dates.")
        record = {"id": str(uuid.uuid4()), "type": "nor_forecast", "result": result, "trend_days": len(trend), "created_by": user.get("email"), "created_at": datetime.now(timezone.utc).isoformat()}
        await db.ai_analytics_results.insert_one(record)
        record.pop("_id", None)
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════
# EXCEPTION PATTERN ANALYSIS
# ══════════════════════════════════════════════════

@router.post("/exception-patterns")
async def exception_pattern_analysis(request: Request):
    """AI-powered exception pattern analysis."""
    user = await get_current_user(request)
    context = await _gather_estate_context()

    # Get all active exceptions with details
    exceptions = await db.route_exceptions.find({"is_active": True}, {"_id": 0}).sort("raised_at", -1).limit(50).to_list(50)
    # Exception history (resolved)
    resolved = await db.route_exceptions.find({"is_active": False}, {"_id": 0, "type": 1, "severity": 1, "device_ref": 1, "raised_at": 1, "resolved_at": 1}).sort("resolved_at", -1).limit(50).to_list(50)

    prompt = f"""{context}

Active Exceptions ({len(exceptions)}):
{json.dumps([{"type": e.get("type"), "severity": e.get("severity"), "device": e.get("device_ref"), "site": e.get("site_name"), "detail": e.get("detail"), "raised": e.get("raised_at")} for e in exceptions[:20]], default=str)}

Recently Resolved ({len(resolved)}):
{json.dumps([{"type": e.get("type"), "device": e.get("device_ref"), "raised": e.get("raised_at"), "resolved": e.get("resolved_at")} for e in resolved[:15]], default=str)}

Based on this data, provide:
1. PATTERN CLUSTERS: Group exceptions into clusters (e.g., "communication failures at Site X", "integrity issues with Manufacturer Y")
2. CORRELATION ANALYSIS: Are certain exception types appearing together? Time-based patterns?
3. REPEAT OFFENDERS: Devices or sites with recurring exceptions
4. RESOLUTION TIME: Average time to resolve by type, and which take longest
5. PREVENTION RECOMMENDATIONS: Specific actions to reduce each exception type by 50%
6. PRIORITY RANKING: Which exceptions should be addressed first for maximum impact?"""

    try:
        result = await _call_gemini(prompt, "You are an exception analysis AI for gaming operations. Find patterns in device exceptions and recommend preventive actions. Be specific with device IDs and site names.")
        record = {"id": str(uuid.uuid4()), "type": "exception_patterns", "result": result, "active_count": len(exceptions), "resolved_count": len(resolved), "created_by": user.get("email"), "created_at": datetime.now(timezone.utc).isoformat()}
        await db.ai_analytics_results.insert_one(record)
        record.pop("_id", None)
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════
# NATURAL LANGUAGE QUERY
# ══════════════════════════════════════════════════

@router.post("/query")
async def natural_language_query(request: Request):
    """Ask any question about the estate using natural language."""
    user = await get_current_user(request)
    body = await request.json()
    question = body.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="No question provided")

    context = await _gather_estate_context()
    prompt = f"""{context}

User Question: {question}

Answer the question using the estate data above. Be specific, cite actual numbers from the data, and provide actionable recommendations where appropriate."""

    try:
        result = await _call_gemini(prompt)
        record = {"id": str(uuid.uuid4()), "type": "query", "question": question, "result": result, "created_by": user.get("email"), "created_at": datetime.now(timezone.utc).isoformat()}
        await db.ai_analytics_results.insert_one(record)
        record.pop("_id", None)
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_analytics_history(request: Request, limit: int = 20, analysis_type: str = None):
    await get_current_user(request)
    query = {}
    if analysis_type:
        query["type"] = analysis_type
    results = await db.ai_analytics_results.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"results": results}
