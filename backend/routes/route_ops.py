from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import uuid
import hashlib
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/route", tags=["route"])

SAS_METER_MAP = [
    {"sasCode": "0000", "description": "Total Coin In Credits", "g2sClass": "G2S_cabinet", "g2sAttribute": "G2S_wageredCashableAmt", "canonicalName": "coinIn", "isVendorExt": False},
    {"sasCode": "0001", "description": "Total Coin Out Credits", "g2sClass": "G2S_cabinet", "g2sAttribute": "G2S_egmPaidGameWonAmt", "canonicalName": "coinOut", "isVendorExt": False},
    {"sasCode": "0002", "description": "Total Jackpot Credits", "g2sClass": "G2S_cabinet", "g2sAttribute": "ILT_totalJackpotAmt", "canonicalName": "jackpotTotal", "isVendorExt": True},
    {"sasCode": "0003", "description": "Total Hand Paid Cancelled Credits", "g2sClass": "G2S_handpay", "g2sAttribute": "G2S_cashableOutAmt", "canonicalName": "handpayCash", "isVendorExt": False},
    {"sasCode": "0005", "description": "Games Played", "g2sClass": "G2S_cabinet", "g2sAttribute": "G2S_gamesSinceInitCnt", "canonicalName": "gamesPlayed", "isVendorExt": False},
    {"sasCode": "0008", "description": "Total Credits from Bills In", "g2sClass": "G2S_noteAcceptor", "g2sAttribute": "G2S_currencyInAmt", "canonicalName": "billsIn", "isVendorExt": False},
    {"sasCode": "000D", "description": "Total SAS Cashable Ticket In", "g2sClass": "G2S_voucher", "g2sAttribute": "G2S_cashableOutAmt", "canonicalName": "ticketCashOut", "isVendorExt": False},
    {"sasCode": "001D", "description": "Machine Paid Progressive Win", "g2sClass": "G2S_cabinet", "g2sAttribute": "G2S_egmPaidProgWonAmt", "canonicalName": "progressiveWon", "isVendorExt": False},
    {"sasCode": "0040", "description": "$1 Bills Accepted Count", "g2sClass": "G2S_noteAcceptor", "g2sAttribute": "ILT_note1InCnt", "canonicalName": "bill1InCnt", "isVendorExt": True},
    {"sasCode": "0042", "description": "$5 Bills Accepted Count", "g2sClass": "G2S_noteAcceptor", "g2sAttribute": "ILT_note5InCnt", "canonicalName": "bill5InCnt", "isVendorExt": True},
    {"sasCode": "0043", "description": "$10 Bills Accepted Count", "g2sClass": "G2S_noteAcceptor", "g2sAttribute": "ILT_note10InCnt", "canonicalName": "bill10InCnt", "isVendorExt": True},
    {"sasCode": "0044", "description": "$20 Bills Accepted Count", "g2sClass": "G2S_noteAcceptor", "g2sAttribute": "ILT_note20InCnt", "canonicalName": "bill20InCnt", "isVendorExt": True},
    {"sasCode": "0046", "description": "$100 Bills Accepted Count", "g2sClass": "G2S_noteAcceptor", "g2sAttribute": "ILT_note100InCnt", "canonicalName": "bill100InCnt", "isVendorExt": True},
]


# ── SAS Meter Map ──
@router.get("/sas-meter-map")
async def get_sas_meter_map(request: Request):
    await get_current_user(request)
    return {"meters": SAS_METER_MAP, "total": len(SAS_METER_MAP)}


# ── Distributors ──
@router.get("/distributors")
async def list_distributors(request: Request):
    await get_current_user(request)
    dists = await db.route_distributors.find({}, {"_id": 0}).to_list(100)
    return {"distributors": dists}


@router.get("/retailers")
async def list_retailers(request: Request, distributor_id: str = None):
    await get_current_user(request)
    q = {}
    if distributor_id:
        q["distributor_id"] = distributor_id
    retailers = await db.route_retailers.find(q, {"_id": 0}).to_list(500)
    return {"retailers": retailers, "total": len(retailers)}


# ── NOR Accounting ──
@router.get("/nor")
async def list_nor_periods(request: Request, distributor_id: str = None, device_id: str = None, period_type: str = "DAILY", days: int = 30, limit: int = 500):
    await get_current_user(request)
    q = {"period_type": period_type}
    if distributor_id:
        q["distributor_id"] = distributor_id
    if device_id:
        q["device_id"] = device_id
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    q["period_start"] = {"$gte": cutoff}
    periods = await db.route_nor_periods.find(q, {"_id": 0}).sort("period_start", -1).limit(limit).to_list(limit)
    return {"periods": periods, "total": len(periods)}


@router.get("/nor/summary")
async def nor_summary(request: Request, distributor_id: str = None, days: int = 30):
    await get_current_user(request)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    match = {"period_start": {"$gte": cutoff}}
    if distributor_id:
        match["distributor_id"] = distributor_id
    pipe = [{"$match": match}, {"$group": {
        "_id": "$distributor_id",
        "total_coin_in": {"$sum": "$coin_in"}, "total_coin_out": {"$sum": "$coin_out"},
        "total_handpay": {"$sum": "$handpay_total"}, "total_voucher_out": {"$sum": "$voucher_out"},
        "total_nor": {"$sum": "$net_operating_revenue"}, "total_tax": {"$sum": "$tax_amount"},
        "device_count": {"$addToSet": "$device_id"}, "period_count": {"$sum": 1},
    }}]
    results = await db.route_nor_periods.aggregate(pipe).to_list(100)
    dists = {d["id"]: d["name"] for d in await db.route_distributors.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(100)}
    summary = []
    grand = {"total_coin_in": 0, "total_nor": 0, "total_tax": 0, "total_devices": 0}
    for r in results:
        s = {
            "distributor_id": r["_id"], "distributor_name": dists.get(r["_id"], "Unknown"),
            "total_coin_in": r["total_coin_in"], "total_coin_out": r["total_coin_out"],
            "total_handpay": r["total_handpay"], "total_voucher_out": r["total_voucher_out"],
            "total_nor": r["total_nor"], "total_tax": r["total_tax"],
            "device_count": len(r["device_count"]),
        }
        summary.append(s)
        grand["total_coin_in"] += s["total_coin_in"]
        grand["total_nor"] += s["total_nor"]
        grand["total_tax"] += s["total_tax"]
        grand["total_devices"] += s["device_count"]
    return {"by_distributor": summary, "grand_total": grand, "days": days}


@router.get("/nor/daily-trend")
async def nor_daily_trend(request: Request, distributor_id: str = None, days: int = 30):
    await get_current_user(request)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    match = {"period_start": {"$gte": cutoff}}
    if distributor_id:
        match["distributor_id"] = distributor_id
    pipe = [{"$match": match}, {"$group": {"_id": "$period_start", "nor": {"$sum": "$net_operating_revenue"}, "coin_in": {"$sum": "$coin_in"}, "tax": {"$sum": "$tax_amount"}}}, {"$sort": {"_id": 1}}]
    results = await db.route_nor_periods.aggregate(pipe).to_list(60)
    return {"trend": [{"date": r["_id"], "nor": r["nor"], "coin_in": r["coin_in"], "tax": r["tax"]} for r in results]}


# ── Monitoring Exceptions ──
@router.get("/exceptions")
async def list_exceptions(request: Request, distributor_id: str = None, exc_type: str = None, severity: str = None, active_only: bool = True, limit: int = 100):
    await get_current_user(request)
    q = {}
    if distributor_id:
        q["distributor_id"] = distributor_id
    if exc_type:
        q["type"] = exc_type
    if severity:
        q["severity"] = severity
    if active_only:
        q["is_active"] = True
    exceptions = await db.route_exceptions.find(q, {"_id": 0}).sort("raised_at", -1).limit(limit).to_list(limit)
    return {"exceptions": exceptions, "total": len(exceptions)}


@router.get("/exceptions/summary")
async def exceptions_summary(request: Request, distributor_id: str = None):
    await get_current_user(request)
    match = {"is_active": True}
    if distributor_id:
        match["distributor_id"] = distributor_id
    total = await db.route_exceptions.count_documents(match)
    critical = await db.route_exceptions.count_documents({**match, "severity": "CRITICAL"})
    by_type = {}
    for t in ["DEVICE_OFFLINE", "SITE_CONTROLLER_OFFLINE", "INTEGRITY_VIOLATION", "DEVICE_DISABLED", "ZERO_PLAY_TODAY", "LOW_PLAY_ALERT", "DOOR_OPEN", "HANDPAY_PENDING", "NSF_ALERT", "AUTO_DISABLED_30DAY"]:
        c = await db.route_exceptions.count_documents({**match, "type": t})
        if c > 0:
            by_type[t] = c
    oldest = await db.route_exceptions.find(match, {"_id": 0, "raised_at": 1}).sort("raised_at", 1).limit(1).to_list(1)
    oldest_min = 0
    if oldest:
        raised = datetime.fromisoformat(oldest[0]["raised_at"].replace("Z", "+00:00")) if isinstance(oldest[0]["raised_at"], str) else oldest[0]["raised_at"]
        oldest_min = int((datetime.now(timezone.utc) - raised).total_seconds() / 60)
    return {"total_active": total, "critical_count": critical, "by_type": by_type, "oldest_unresolved_minutes": oldest_min}


@router.post("/exceptions/{exc_id}/resolve")
async def resolve_exception(request: Request, exc_id: str):
    user = await get_current_user(request)
    body = await request.json()
    now = datetime.now(timezone.utc).isoformat()
    result = await db.route_exceptions.update_one(
        {"id": exc_id, "is_active": True},
        {"$set": {"resolved_at": now, "resolved_by": user.get("email"), "resolution_note": body.get("note", ""), "is_active": False}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Exception not found or already resolved")
    return {"message": "Exception resolved"}


# ── Integrity Checks ──
@router.get("/integrity")
async def list_integrity_checks(request: Request, device_id: str = None, result: str = None, limit: int = 100):
    await get_current_user(request)
    q = {}
    if device_id:
        q["device_id"] = device_id
    if result:
        q["result"] = result
    checks = await db.route_integrity_checks.find(q, {"_id": 0}).sort("check_time", -1).limit(limit).to_list(limit)
    return {"checks": checks, "total": len(checks)}


@router.get("/integrity/summary")
async def integrity_summary(request: Request):
    await get_current_user(request)
    total = await db.route_integrity_checks.count_documents({})
    passed = await db.route_integrity_checks.count_documents({"result": "PASS"})
    failed = await db.route_integrity_checks.count_documents({"result": "FAIL"})
    no_image = await db.route_integrity_checks.count_documents({"result": "NO_IMAGE_FOUND"})
    by_trigger = {}
    for t in ["SCHEDULED", "REBOOT", "RECONNECT", "OPERATOR"]:
        by_trigger[t] = await db.route_integrity_checks.count_documents({"trigger": t})
    return {"total": total, "passed": passed, "failed": failed, "no_image": no_image, "pass_rate": round(passed / total * 100, 1) if total > 0 else 0, "by_trigger": by_trigger}


# ── Offline Buffer ──
@router.get("/buffer-status")
async def buffer_status(request: Request):
    await get_current_user(request)
    states = await db.route_buffer_states.find({}, {"_id": 0}).to_list(100)
    online = sum(1 for s in states if s["connectivity_state"] == "ONLINE")
    degraded = sum(1 for s in states if s["connectivity_state"] == "DEGRADED")
    offline = sum(1 for s in states if s["connectivity_state"] in ["OFFLINE", "AUTO_DISABLED"])
    total_pending = sum(s.get("pending_events", 0) for s in states)
    return {"agents": states, "summary": {"online": online, "degraded": degraded, "offline": offline, "total_agents": len(states), "total_pending_events": total_pending}}


# ── EFT Files ──
@router.get("/eft")
async def list_eft_files(request: Request):
    await get_current_user(request)
    files = await db.route_eft_files.find({}, {"_id": 0}).sort("generated_at", -1).to_list(100)
    return {"files": files}


@router.post("/eft/generate")
async def generate_eft(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    period_start = body.get("period_start", (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d"))
    period_end = body.get("period_end", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    sweep_type = body.get("sweep_type", "WEEKLY")

    # Calculate totals from NOR periods
    match = {"period_start": {"$gte": period_start, "$lte": period_end}}
    pipe = [{"$match": match}, {"$group": {"_id": "$distributor_id", "total_nor": {"$sum": "$net_operating_revenue"}, "device_count": {"$addToSet": "$device_id"}}}]
    results = await db.route_nor_periods.aggregate(pipe).to_list(100)
    total_cents = sum(max(0, r["total_nor"]) for r in results)
    entry_count = sum(len(r["device_count"]) for r in results)

    now = datetime.now(timezone.utc)
    filename = f"UGG_EFT_{now.strftime('%Y%m%d_%H%M%S')}.ach"
    file_content = f"NACHA ACH FILE — {filename}\nPeriod: {period_start} to {period_end}\nEntries: {entry_count}\nTotal: ${total_cents / 100:,.2f}"
    file_hash = hashlib.sha256(file_content.encode()).hexdigest()

    eft = {
        "id": str(uuid.uuid4()), "filename": filename, "period_start": period_start, "period_end": period_end,
        "sweep_type": sweep_type, "total_amount_cents": total_cents, "entry_count": entry_count,
        "generated_at": now.isoformat(), "generated_by": user.get("email"),
        "file_hash": file_hash, "status": "GENERATED", "transmitted_at": None, "notes": None,
    }
    await db.route_eft_files.insert_one(eft)
    eft.pop("_id", None)
    return eft


# ── Route Dashboard Summary ──
@router.get("/dashboard")
async def route_dashboard(request: Request):
    await get_current_user(request)
    total_devices = await db.devices.count_documents({})
    online_devices = await db.devices.count_documents({"status": "online"})
    exc_summary = await db.route_exceptions.count_documents({"is_active": True})
    exc_critical = await db.route_exceptions.count_documents({"is_active": True, "severity": "CRITICAL"})
    dist_count = await db.route_distributors.count_documents({})
    retailer_count = await db.route_retailers.count_documents({})

    # 30-day NOR
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    nor_pipe = [{"$match": {"period_start": {"$gte": cutoff}}}, {"$group": {"_id": None, "total_nor": {"$sum": "$net_operating_revenue"}, "total_coin_in": {"$sum": "$coin_in"}, "total_tax": {"$sum": "$tax_amount"}}}]
    nor_agg = await db.route_nor_periods.aggregate(nor_pipe).to_list(1)
    nor_data = nor_agg[0] if nor_agg else {}

    integrity_total = await db.route_integrity_checks.count_documents({})
    integrity_pass = await db.route_integrity_checks.count_documents({"result": "PASS"})

    buffer_states = await db.route_buffer_states.find({}, {"_id": 0}).to_list(100)
    agents_online = sum(1 for s in buffer_states if s["connectivity_state"] == "ONLINE")

    return {
        "devices": {"total": total_devices, "online": online_devices},
        "exceptions": {"active": exc_summary, "critical": exc_critical},
        "distributors": dist_count, "retailers": retailer_count,
        "nor_30d": {"total_nor": nor_data.get("total_nor", 0), "total_coin_in": nor_data.get("total_coin_in", 0), "total_tax": nor_data.get("total_tax", 0)},
        "integrity": {"total_checks": integrity_total, "pass_rate": round(integrity_pass / integrity_total * 100, 1) if integrity_total > 0 else 0},
        "agents": {"total": len(buffer_states), "online": agents_online},
    }
