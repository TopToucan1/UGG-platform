"""
Phase 7 Route Module Gaps — NOR Split Engine, Operators, Revenue Shares,
NSF Handler, Statutory Periods, License Expiry, New Exception Types.
"""
from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import uuid
import random
import math
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/route/v2", tags=["route-v2"])


# ══════════════════════════════════════════════════
# NOR SPLIT ENGINE — BigInt precision
# ══════════════════════════════════════════════════

def calculate_nor(coin_in: int, coin_out: int, handpay: int, vouchers_out: int) -> dict:
    nor = coin_in - coin_out - handpay - vouchers_out
    return {"coin_in": coin_in, "coin_out": coin_out, "handpay": handpay, "vouchers_out": vouchers_out, "nor": nor, "nor_dollars": round(nor / 100, 2), "is_positive": nor >= 0}


def split_nor(nor_cents: int, share_dist: float, share_op: float, share_ret: float, state_tax_rate: float) -> dict:
    """Split NOR among stakeholders with exact precision. Retailer absorbs rounding."""
    state_share = math.floor(nor_cents * state_tax_rate)
    remainder = nor_cents - state_share
    dist_share = math.floor(remainder * share_dist)
    op_share = math.floor(remainder * share_op)
    ret_share = remainder - dist_share - op_share  # absorbs rounding
    checksum = state_share + dist_share + op_share + ret_share
    if checksum != nor_cents:
        raise ValueError(f"NOR split integrity failure: {checksum} != {nor_cents}")
    return {"total": nor_cents, "distributor": dist_share, "operator": op_share, "retailer": ret_share, "state": state_share, "checksum": checksum, "integrity_ok": True}


@router.get("/nor/split")
async def get_nor_splits(request: Request, distributor_id: str = None, days: int = 30):
    """NOR with full 4-way split (distributor, operator, retailer, state)."""
    await get_current_user(request)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    match = {"period_start": {"$gte": cutoff}}
    if distributor_id:
        match["distributor_id"] = distributor_id

    periods = await db.route_nor_periods.find(match, {"_id": 0}).to_list(5000)
    splits = []
    for p in periods:
        nor = p.get("net_operating_revenue", 0)
        if nor <= 0:
            continue
        # Get device revenue shares
        device = await db.route_device_shares.find_one({"device_id": p.get("device_id")}, {"_id": 0})
        shares = device or {"revenue_share_dist": 0.34, "revenue_share_op": 0.33, "revenue_share_ret": 0.33}
        tax_rate = p.get("tax_rate_bps", 500) / 10000
        try:
            s = split_nor(nor, shares.get("revenue_share_dist", 0.34), shares.get("revenue_share_op", 0.33), shares.get("revenue_share_ret", 0.33), tax_rate)
            splits.append({**p, "split": s, "device_id": p.get("device_id"), "device_ref": p.get("device_ref")})
        except ValueError:
            pass

    # Aggregate by distributor
    dist_totals = {}
    for sp in splits:
        did = sp.get("distributor_id", "unknown")
        if did not in dist_totals:
            dist_totals[did] = {"distributor_id": did, "total_nor": 0, "dist_share": 0, "op_share": 0, "ret_share": 0, "state_share": 0, "devices": set()}
        dist_totals[did]["total_nor"] += sp["split"]["total"]
        dist_totals[did]["dist_share"] += sp["split"]["distributor"]
        dist_totals[did]["op_share"] += sp["split"]["operator"]
        dist_totals[did]["ret_share"] += sp["split"]["retailer"]
        dist_totals[did]["state_share"] += sp["split"]["state"]
        dist_totals[did]["devices"].add(sp.get("device_id", ""))

    # Resolve names
    dist_names = {d["id"]: d["name"] for d in await db.route_distributors.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(100)}
    result = []
    for did, t in dist_totals.items():
        result.append({
            "distributor_id": did, "distributor_name": dist_names.get(did, "Unknown"),
            "total_nor": t["total_nor"], "total_nor_dollars": round(t["total_nor"] / 100, 2),
            "distributor_share": t["dist_share"], "distributor_share_dollars": round(t["dist_share"] / 100, 2),
            "operator_share": t["op_share"], "operator_share_dollars": round(t["op_share"] / 100, 2),
            "retailer_share": t["ret_share"], "retailer_share_dollars": round(t["ret_share"] / 100, 2),
            "state_share": t["state_share"], "state_share_dollars": round(t["state_share"] / 100, 2),
            "device_count": len(t["devices"]),
        })
    return {"splits": result, "period_days": days}


# ══════════════════════════════════════════════════
# OPERATORS ENTITY (between Distributor and Retailer)
# ══════════════════════════════════════════════════

@router.get("/operators")
async def list_operators(request: Request, distributor_id: str = None):
    await get_current_user(request)
    query = {}
    if distributor_id:
        query["distributor_id"] = distributor_id
    operators = await db.route_operators.find(query, {"_id": 0}).to_list(200)
    return {"operators": operators, "total": len(operators)}


@router.post("/operators")
async def create_operator(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    op = {
        "id": str(uuid.uuid4()), "distributor_id": body.get("distributor_id"),
        "legal_name": body.get("legal_name", ""), "license_number": body.get("license_number", ""),
        "license_expires": body.get("license_expires"), "revenue_share": body.get("revenue_share", 0.33),
        "contact_email": body.get("contact_email", ""), "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.route_operators.insert_one(op)
    op.pop("_id", None)
    return op


# ══════════════════════════════════════════════════
# REVENUE SHARES per device
# ══════════════════════════════════════════════════

@router.get("/device-shares")
async def list_device_shares(request: Request, distributor_id: str = None):
    await get_current_user(request)
    query = {}
    if distributor_id:
        query["distributor_id"] = distributor_id
    shares = await db.route_device_shares.find(query, {"_id": 0}).to_list(500)
    return {"shares": shares}


@router.post("/device-shares")
async def set_device_shares(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    dist = body.get("revenue_share_dist", 0.34)
    op = body.get("revenue_share_op", 0.33)
    ret = body.get("revenue_share_ret", 0.33)
    if abs(dist + op + ret - 1.0) >= 0.0001:
        raise HTTPException(status_code=400, detail=f"Revenue shares must sum to 1.0 (got {dist + op + ret})")
    share = {
        "device_id": body["device_id"], "distributor_id": body.get("distributor_id"),
        "operator_id": body.get("operator_id"), "retailer_id": body.get("retailer_id"),
        "revenue_share_dist": dist, "revenue_share_op": op, "revenue_share_ret": ret,
        "terminal_number": body.get("terminal_number", ""),
        "placement_date": body.get("placement_date"), "removal_date": None,
        "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user.get("email"),
    }
    await db.route_device_shares.update_one({"device_id": body["device_id"]}, {"$set": share}, upsert=True)
    return {"message": "Revenue shares updated", "share": share}


# ══════════════════════════════════════════════════
# STATUTORY PERIODS — OPEN → CLOSED → SUBMITTED → ACCEPTED
# ══════════════════════════════════════════════════

@router.get("/statutory-periods")
async def list_statutory_periods(request: Request, distributor_id: str = None, status: str = None, limit: int = 20):
    await get_current_user(request)
    query = {}
    if distributor_id:
        query["distributor_id"] = distributor_id
    if status:
        query["status"] = status
    periods = await db.route_statutory_periods.find(query, {"_id": 0}).sort("period_start", -1).limit(limit).to_list(limit)
    return {"periods": periods}


@router.post("/statutory-periods/close")
async def close_statutory_period(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    period_id = body.get("period_id")
    period = await db.route_statutory_periods.find_one({"id": period_id})
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
    if period.get("status") != "OPEN":
        raise HTTPException(status_code=400, detail=f"Period must be OPEN to close (current: {period.get('status')})")

    # Calculate NOR totals for this period
    pipe = [{"$match": {"distributor_id": period.get("distributor_id"), "period_start": {"$gte": period.get("period_start"), "$lte": period.get("period_end")}}}, {"$group": {"_id": None, "nor": {"$sum": "$net_operating_revenue"}}}]
    agg = await db.route_nor_periods.aggregate(pipe).to_list(1)
    nor_total = agg[0]["nor"] if agg else 0

    await db.route_statutory_periods.update_one({"id": period_id}, {"$set": {"status": "CLOSED", "nor_total": nor_total, "closed_at": datetime.now(timezone.utc).isoformat(), "closed_by": user.get("email")}})
    return {"message": "Period closed", "nor_total": nor_total}


@router.post("/statutory-periods/submit")
async def submit_statutory_period(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    period_id = body.get("period_id")
    result = await db.route_statutory_periods.update_one({"id": period_id, "status": "CLOSED"}, {"$set": {"status": "SUBMITTED", "submitted_at": datetime.now(timezone.utc).isoformat()}})
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Period must be CLOSED to submit")
    return {"message": "Period submitted"}


# ══════════════════════════════════════════════════
# LICENSE EXPIRY TRACKING
# ══════════════════════════════════════════════════

@router.get("/licenses/expiring")
async def get_expiring_licenses(request: Request, days: int = 30):
    await get_current_user(request)
    cutoff = (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    expiring = []
    # Check distributors
    for d in await db.route_distributors.find({"license_expires": {"$lte": cutoff, "$gte": today}}, {"_id": 0}).to_list(100):
        expiring.append({"holder_type": "DISTRIBUTOR", "holder_name": d.get("name"), "license_number": d.get("state_license"), "expires": d.get("license_expires"), "holder_id": d.get("id")})
    # Check operators
    for o in await db.route_operators.find({"license_expires": {"$lte": cutoff, "$gte": today}}, {"_id": 0}).to_list(200):
        expiring.append({"holder_type": "OPERATOR", "holder_name": o.get("legal_name"), "license_number": o.get("license_number"), "expires": o.get("license_expires"), "holder_id": o.get("id")})

    return {"expiring_licenses": expiring, "total": len(expiring), "within_days": days}


# ══════════════════════════════════════════════════
# NEW EXCEPTION TYPES + NSF HANDLER
# ══════════════════════════════════════════════════

@router.post("/exceptions/check-anomalies")
async def check_revenue_anomalies(request: Request):
    """Check for REVENUE_ANOMALY — NOR < 40% of 90-day average."""
    user = await get_current_user(request)
    d90 = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")
    d7 = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

    # Per-device 90-day average
    avg_pipe = [{"$match": {"period_start": {"$gte": d90}}}, {"$group": {"_id": "$device_id", "avg_nor": {"$avg": "$net_operating_revenue"}, "count": {"$sum": 1}}}, {"$match": {"count": {"$gte": 7}}}]
    device_avgs = {r["_id"]: r["avg_nor"] for r in await db.route_nor_periods.aggregate(avg_pipe).to_list(500)}

    # Per-device current period
    cur_pipe = [{"$match": {"period_start": {"$gte": d7}}}, {"$group": {"_id": "$device_id", "cur_nor": {"$sum": "$net_operating_revenue"}}}]
    device_current = {r["_id"]: r["cur_nor"] for r in await db.route_nor_periods.aggregate(cur_pipe).to_list(500)}

    anomalies = []
    for device_id, avg in device_avgs.items():
        cur = device_current.get(device_id, 0)
        if avg > 0 and cur < avg * 0.4:
            device = await db.devices.find_one({"id": device_id}, {"_id": 0, "external_ref": 1, "retailer_id": 1, "distributor_id": 1})
            if not device:
                continue
            # Check if exception already exists
            existing = await db.route_exceptions.find_one({"device_id": device_id, "type": "REVENUE_ANOMALY", "is_active": True})
            if existing:
                continue
            retailer = await db.route_retailers.find_one({"id": device.get("retailer_id")}, {"_id": 0, "name": 1})
            exc = {
                "id": str(uuid.uuid4()), "type": "REVENUE_ANOMALY", "severity": "WARNING",
                "device_id": device_id, "device_ref": device.get("external_ref", ""),
                "site_id": device.get("retailer_id", ""), "site_name": retailer.get("name", "") if retailer else "",
                "distributor_id": device.get("distributor_id", ""),
                "detail": f"NOR {round(cur)} is {round(cur/avg*100 if avg else 0)}% of 90-day avg {round(avg)} — below 40% threshold",
                "raised_at": datetime.now(timezone.utc).isoformat(), "is_active": True,
            }
            await db.route_exceptions.insert_one(exc)
            anomalies.append(exc)
    return {"anomalies_detected": len(anomalies), "devices_checked": len(device_avgs)}


@router.post("/exceptions/check-terminals")
async def check_max_terminals(request: Request):
    """Check for MAX_TERMINALS_EXCEEDED — more devices than max_terminals allows."""
    await get_current_user(request)
    retailers = await db.route_retailers.find({}, {"_id": 0}).to_list(500)
    violations = []
    for r in retailers:
        max_t = r.get("max_terminals", 5)
        actual = await db.devices.count_documents({"retailer_id": r["id"], "status": {"$ne": "removed"}})
        if actual > max_t:
            existing = await db.route_exceptions.find_one({"site_id": r["id"], "type": "MAX_TERMINALS_EXCEEDED", "is_active": True})
            if existing:
                continue
            exc = {
                "id": str(uuid.uuid4()), "type": "MAX_TERMINALS_EXCEEDED", "severity": "ERROR",
                "device_id": None, "device_ref": "", "site_id": r["id"], "site_name": r.get("name", ""),
                "distributor_id": r.get("distributor_id", ""),
                "detail": f"{r.get('name', '')} has {actual} active devices but max_terminals is {max_t}",
                "raised_at": datetime.now(timezone.utc).isoformat(), "is_active": True,
            }
            await db.route_exceptions.insert_one(exc)
            violations.append(exc)
    return {"violations": len(violations), "retailers_checked": len(retailers)}


@router.post("/exceptions/check-gameplay")
async def check_excessive_gameplay(request: Request):
    """Check for EXCESSIVE_GAMEPLAY — sessions > 4 hours."""
    await get_current_user(request)
    threshold_min = 240
    long_sessions = await db.player_sessions.find({"status": "active", "duration_minutes": {"$gte": threshold_min}}, {"_id": 0}).to_list(100)
    alerts = []
    for s in long_sessions:
        existing = await db.route_exceptions.find_one({"device_id": s.get("device_id"), "type": "EXCESSIVE_GAMEPLAY", "is_active": True})
        if existing:
            continue
        exc = {
            "id": str(uuid.uuid4()), "type": "EXCESSIVE_GAMEPLAY", "severity": "WARNING",
            "device_id": s.get("device_id"), "device_ref": s.get("device_ref", ""),
            "site_id": s.get("site_id", ""), "site_name": s.get("site_name", ""),
            "distributor_id": "",
            "detail": f"Player {s.get('player_name', '')} session at {s.get('device_ref', '')} for {s.get('duration_minutes', 0)} minutes (threshold: {threshold_min})",
            "raised_at": datetime.now(timezone.utc).isoformat(), "is_active": True,
        }
        await db.route_exceptions.insert_one(exc)
        alerts.append(exc)
    return {"excessive_sessions": len(alerts), "sessions_checked": len(long_sessions)}


@router.post("/nsf/handle")
async def handle_nsf_return(request: Request):
    """Process an NSF (Non-Sufficient Funds) ACH return."""
    user = await get_current_user(request)
    body = await request.json()
    trace_number = body.get("trace_number", "")
    return_code = body.get("return_code", "R01")
    payee_id = body.get("payee_id", "")
    payee_name = body.get("payee_name", "Unknown")
    amount = body.get("amount_cents", 0)
    distributor_id = body.get("distributor_id", "")

    # 1. Create CRITICAL exception
    exc = {
        "id": str(uuid.uuid4()), "type": "NSF_RETURN", "severity": "CRITICAL",
        "device_id": None, "device_ref": "", "site_id": "", "site_name": payee_name,
        "distributor_id": distributor_id,
        "detail": f"NSF return for {payee_name}: ${amount/100:.2f} — Return code {return_code} (trace: {trace_number})",
        "raised_at": datetime.now(timezone.utc).isoformat(), "is_active": True,
    }
    await db.route_exceptions.insert_one(exc)

    # 2. Flag the EFT entry
    await db.route_eft_files.update_many(
        {"status": {"$in": ["GENERATED", "TRANSMITTED"]}},
        {"$set": {"nsf_flagged": True}}
    )

    # 3. Hold future payments to this payee
    hold_count = 0
    # (In production, this would update eft_entries table)

    return {
        "message": f"NSF return processed for {payee_name}",
        "exception_id": exc["id"],
        "return_code": return_code,
        "amount_cents": amount,
        "future_payments_held": hold_count,
    }


# ══════════════════════════════════════════════════
# DEVICE COMPLIANCE STATUS
# ══════════════════════════════════════════════════

@router.get("/devices/{device_id}/compliance")
async def get_device_compliance(request: Request, device_id: str):
    await get_current_user(request)
    device = await db.devices.find_one({"id": device_id}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    integrity = await db.route_integrity_checks.find({"device_id": device_id}, {"_id": 0}).sort("check_time", -1).limit(5).to_list(5)
    exceptions = await db.route_exceptions.count_documents({"device_id": device_id, "is_active": True})
    nor_pipe = [{"$match": {"device_id": device_id}}, {"$group": {"_id": None, "total_nor": {"$sum": "$net_operating_revenue"}, "days": {"$sum": 1}}}]
    nor = await db.route_nor_periods.aggregate(nor_pipe).to_list(1)
    twin = await db.device_state_projection.find_one({"device_id": device_id}, {"_id": 0})
    shares = await db.route_device_shares.find_one({"device_id": device_id}, {"_id": 0})

    return {
        "device": device,
        "integrity_history": integrity,
        "integrity_pass_rate": round(sum(1 for i in integrity if i.get("result") == "PASS") / len(integrity) * 100, 1) if integrity else 0,
        "active_exceptions": exceptions,
        "nor_summary": nor[0] if nor else {"total_nor": 0, "days": 0},
        "digital_twin": twin,
        "revenue_shares": shares,
    }


# ══════════════════════════════════════════════════
# SEED OPERATORS + REVENUE SHARES + STATUTORY PERIODS
# ══════════════════════════════════════════════════

async def seed_route_v2():
    if await db.route_operators.count_documents({}) > 0:
        return

    distributors = await db.route_distributors.find({}, {"_id": 0}).to_list(10)
    retailers = await db.route_retailers.find({}, {"_id": 0}).to_list(200)
    devices = await db.devices.find({}, {"_id": 0, "id": 1, "distributor_id": 1, "retailer_id": 1}).to_list(200)
    if not distributors:
        return

    import logging
    logging.getLogger(__name__).info("Seeding Route v2 data...")

    # Operators (2 per distributor)
    operators = []
    op_names = ["Metro Route Ops", "Valley Gaming Services", "Mountain Amusement Co", "Lakeshore Routes LLC", "Desert Route Partners", "Riverside Gaming Ops"]
    for i, dist in enumerate(distributors):
        for j in range(2):
            op = {
                "id": str(uuid.uuid4()), "distributor_id": dist["id"],
                "legal_name": op_names[(i * 2 + j) % len(op_names)],
                "license_number": f"OP-2024-{i*2+j+1:03d}",
                "license_expires": (datetime.now(timezone.utc) + timedelta(days=random.randint(10, 365))).strftime("%Y-%m-%d"),
                "revenue_share": round(random.uniform(0.28, 0.38), 4),
                "contact_email": f"ops{i*2+j}@route.com", "status": "active",
                "created_at": "2024-01-15T00:00:00Z",
            }
            operators.append(op)
    await db.route_operators.insert_many(operators)

    # Assign operators to retailers
    for i, r in enumerate(retailers):
        dist_ops = [o for o in operators if o["distributor_id"] == r.get("distributor_id")]
        if dist_ops:
            op = dist_ops[i % len(dist_ops)]
            await db.route_retailers.update_one({"id": r["id"]}, {"$set": {"operator_id": op["id"], "max_terminals": random.choice([3, 5, 5, 5, 7, 10])}})

    # Revenue shares per device
    shares = []
    for d in devices:
        dist_share = round(random.uniform(0.30, 0.40), 4)
        op_share = round(random.uniform(0.25, 0.35), 4)
        ret_share = round(1.0 - dist_share - op_share, 4)
        shares.append({
            "device_id": d["id"], "distributor_id": d.get("distributor_id"),
            "operator_id": None, "retailer_id": d.get("retailer_id"),
            "revenue_share_dist": dist_share, "revenue_share_op": op_share, "revenue_share_ret": ret_share,
            "terminal_number": f"T-{random.randint(10000, 99999)}",
            "placement_date": "2024-06-01", "removal_date": None,
        })
    await db.route_device_shares.insert_many(shares)

    # Statutory periods (last 4 weeks)
    stat_periods = []
    now = datetime.now(timezone.utc)
    for dist in distributors:
        for w in range(4):
            start = (now - timedelta(weeks=w + 1)).strftime("%Y-%m-%d")
            end = (now - timedelta(weeks=w)).strftime("%Y-%m-%d")
            status = "ACCEPTED" if w >= 2 else "CLOSED" if w == 1 else "OPEN"
            stat_periods.append({
                "id": str(uuid.uuid4()), "distributor_id": dist["id"],
                "period_start": start, "period_end": end, "period_type": "WEEKLY",
                "status": status, "nor_total": random.randint(50000, 500000) if status != "OPEN" else None,
                "closed_at": (now - timedelta(weeks=w)).isoformat() if status in ("CLOSED", "ACCEPTED") else None,
                "submitted_at": (now - timedelta(weeks=w)).isoformat() if status == "ACCEPTED" else None,
            })
    await db.route_statutory_periods.insert_many(stat_periods)

    # Add license_expires to distributors
    for dist in distributors:
        await db.route_distributors.update_one({"id": dist["id"]}, {"$set": {"license_expires": (now + timedelta(days=random.randint(15, 400))).strftime("%Y-%m-%d")}})

    logging.getLogger(__name__).info(f"Seeded Route v2: {len(operators)} operators, {len(shares)} device shares, {len(stat_periods)} statutory periods")
