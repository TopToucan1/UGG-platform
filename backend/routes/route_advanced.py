from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse
from database import db
from auth import get_current_user, require_role
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
import time
import os

router = APIRouter(prefix="/api/route/advanced", tags=["route-advanced"])

# ══════════════════════════════════════════════════
# MODULE 4 — STATUTORY REPORTING FIELDS
# ══════════════════════════════════════════════════

STATUTORY_FIELDS = [
    "distributor_id", "operator_id", "site_address", "site_city",
    "site_county", "software_version", "software_signature", "device_serial",
]


@router.get("/statutory/fields")
async def get_statutory_fields(request: Request):
    await get_current_user(request)
    return {"fields": STATUTORY_FIELDS, "description": "Mandatory fields on every event per state legislation"}


@router.get("/statutory/enrichment-status")
async def statutory_enrichment_status(request: Request):
    """Check how many events have been enriched with statutory fields."""
    await get_current_user(request)
    total_events = await db.events.count_documents({})
    enriched = await db.events.count_documents({"distributor_id": {"$exists": True, "$ne": None}})
    missing = total_events - enriched
    # Count by county
    county_pipe = [
        {"$match": {"site_county": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$site_county", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    by_county = await db.events.aggregate(county_pipe).to_list(50)
    return {
        "total_events": total_events,
        "enriched_events": enriched,
        "missing_enrichment": missing,
        "enrichment_rate": round(enriched / total_events * 100, 1) if total_events > 0 else 0,
        "by_county": [{"county": c["_id"], "count": c["count"]} for c in by_county],
    }


@router.post("/statutory/enrich-batch")
async def enrich_events_batch(request: Request):
    """Batch-enrich existing events with statutory fields from device/site registry."""
    user = await get_current_user(request)
    body = await request.json()
    limit = body.get("limit", 10000)

    # Find unenriched events
    events = await db.events.find(
        {"$or": [{"distributor_id": {"$exists": False}}, {"distributor_id": None}]},
        {"_id": 1, "device_id": 1}
    ).limit(limit).to_list(limit)

    if not events:
        return {"enriched": 0, "message": "All events already enriched", "remaining": 0}

    # Build device lookup
    device_ids = list(set(e.get("device_id") for e in events if e.get("device_id")))
    devices = await db.devices.find({"id": {"$in": device_ids}}, {"_id": 0}).to_list(len(device_ids) + 10)
    dev_map = {d["id"]: d for d in devices}

    # Build retailer lookup
    retailer_ids = list(set(d.get("retailer_id") for d in devices if d.get("retailer_id")))
    retailers = await db.route_retailers.find({"id": {"$in": retailer_ids}}, {"_id": 0}).to_list(len(retailer_ids) + 10)
    ret_map = {r["id"]: r for r in retailers}

    enriched = 0
    for evt in events:
        dev = dev_map.get(evt.get("device_id"), {})
        ret = ret_map.get(dev.get("retailer_id"), {})
        update = {
            "distributor_id": dev.get("distributor_id", "unknown"),
            "operator_id": dev.get("retailer_id", "unknown"),
            "site_address": ret.get("address", ""),
            "site_city": ret.get("city", ""),
            "site_county": ret.get("county", ""),
            "software_version": dev.get("firmware_version", ""),
            "software_signature": "",
            "device_serial": dev.get("serial_number", ""),
        }
        await db.events.update_one({"_id": evt["_id"]}, {"$set": update})
        enriched += 1

    remaining = await db.events.count_documents({"$or": [{"distributor_id": {"$exists": False}}, {"distributor_id": None}]})
    return {"enriched": enriched, "remaining": remaining, "message": f"Enriched {enriched} events" + (" — all done!" if remaining == 0 else f", {remaining} remaining")}


@router.get("/statutory/duration-of-play")
async def duration_of_play_report(request: Request, distributor_id: str = None, days: int = 7):
    """Duration of play report as required by state law."""
    await get_current_user(request)
    sessions = await db.player_sessions.find(
        {"status": "completed"} if not distributor_id else {"status": "completed"},
        {"_id": 0, "player_name": 1, "device_ref": 1, "duration_minutes": 1, "games_played": 1,
         "total_wagered": 1, "total_won": 1, "card_in_at": 1, "card_out_at": 1, "site_name": 1}
    ).sort("card_in_at", -1).limit(200).to_list(200)

    total_duration = sum(s.get("duration_minutes", 0) for s in sessions)
    avg_duration = round(total_duration / len(sessions), 1) if sessions else 0
    total_wagered = sum(s.get("total_wagered", 0) for s in sessions)

    return {
        "sessions": sessions,
        "total_sessions": len(sessions),
        "total_duration_minutes": total_duration,
        "avg_duration_minutes": avg_duration,
        "total_wagered": total_wagered,
        "report_period_days": days,
    }


# ══════════════════════════════════════════════════
# MODULE 7 — 4-TIER RBAC PORTAL
# ══════════════════════════════════════════════════

ROLE_PERMISSIONS = {
    "state_regulator": {
        "tier": 1, "label": "State Regulator", "description": "Full estate view, all distributors",
        "can_view_all_distributors": True, "can_view_revenue": True, "can_view_devices": True,
        "can_view_integrity": True, "can_view_eft": True, "can_view_tax": True,
        "can_enable_disable_devices": True, "can_create_announcements": True,
        "can_view_player_data": "aggregate", "data_scope": "all",
    },
    "distributor_admin": {
        "tier": 2, "label": "Distributor Admin", "description": "Own route only",
        "can_view_all_distributors": False, "can_view_revenue": True, "can_view_devices": True,
        "can_view_integrity": True, "can_view_eft": True, "can_view_tax": True,
        "can_enable_disable_devices": True, "can_create_announcements": True,
        "can_view_player_data": "own_route", "data_scope": "own_distributor",
    },
    "retailer_viewer": {
        "tier": 3, "label": "Retailer/Operator", "description": "Own venue only, read-only",
        "can_view_all_distributors": False, "can_view_revenue": True, "can_view_devices": True,
        "can_view_integrity": False, "can_view_eft": False, "can_view_tax": False,
        "can_enable_disable_devices": False, "can_create_announcements": False,
        "can_view_player_data": False, "data_scope": "own_site",
    },
    "manufacturer_viewer": {
        "tier": 4, "label": "Manufacturer", "description": "Own device models only, read-only",
        "can_view_all_distributors": False, "can_view_revenue": False, "can_view_devices": False,
        "can_view_integrity": True, "can_view_eft": False, "can_view_tax": False,
        "can_enable_disable_devices": False, "can_create_announcements": False,
        "can_view_player_data": False, "data_scope": "own_models",
    },
}


@router.get("/rbac/roles")
async def get_rbac_roles(request: Request):
    await get_current_user(request)
    return {"roles": ROLE_PERMISSIONS}


@router.get("/rbac/users")
async def list_rbac_users(request: Request):
    await require_role(request, ["admin", "state_regulator"])
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(200)
    for u in users:
        u["id"] = str(u.pop("_id", "")) if "_id" in u else u.get("id", "")
        u["permissions"] = ROLE_PERMISSIONS.get(u.get("role"), {})
    return {"users": users}


@router.get("/rbac/my-permissions")
async def my_permissions(request: Request):
    user = await get_current_user(request)
    role = user.get("role", "operator")
    perms = ROLE_PERMISSIONS.get(role, {})
    return {"role": role, "permissions": perms, "user": {"email": user.get("email"), "name": user.get("name")}}


@router.post("/rbac/users/{user_id}/assign-scope")
async def assign_user_scope(request: Request, user_id: str):
    """Assign distributor/retailer/manufacturer scope to a user."""
    await require_role(request, ["admin", "state_regulator"])
    body = await request.json()
    from bson import ObjectId
    update = {}
    if "distributor_id" in body:
        update["distributor_id"] = body["distributor_id"]
    if "retailer_id" in body:
        update["retailer_id"] = body["retailer_id"]
    if "manufacturer_id" in body:
        update["manufacturer_id"] = body["manufacturer_id"]
    if "role" in body and body["role"] in ROLE_PERMISSIONS:
        update["role"] = body["role"]
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User scope updated"}


# ══════════════════════════════════════════════════
# MODULE 8 — PERFORMANCE METRICS & NACHA COMPLIANCE
# ══════════════════════════════════════════════════

@router.get("/performance/metrics")
async def performance_metrics(request: Request):
    """Real-time performance metrics for the platform."""
    await get_current_user(request)
    start = time.time()

    # Database sizes
    collections = ["events", "devices", "meter_snapshots", "route_nor_periods", "financial_events",
                   "player_sessions", "route_exceptions", "route_integrity_checks", "audit_records"]
    db_stats = {}
    for coll in collections:
        count = await db[coll].count_documents({})
        db_stats[coll] = count

    # Query performance benchmarks
    benchmarks = []

    t = time.time()
    await db.events.find({}).limit(100).to_list(100)
    benchmarks.append({"query": "events.find(limit=100)", "ms": round((time.time() - t) * 1000, 1)})

    t = time.time()
    await db.route_nor_periods.aggregate([{"$group": {"_id": "$distributor_id", "t": {"$sum": "$net_operating_revenue"}}}]).to_list(10)
    benchmarks.append({"query": "NOR aggregation by distributor", "ms": round((time.time() - t) * 1000, 1)})

    t = time.time()
    await db.route_exceptions.find({"is_active": True}).to_list(100)
    benchmarks.append({"query": "active exceptions query", "ms": round((time.time() - t) * 1000, 1)})

    t = time.time()
    await db.devices.find({}).limit(85).to_list(85)
    benchmarks.append({"query": "all devices query", "ms": round((time.time() - t) * 1000, 1)})

    t = time.time()
    await db.financial_events.aggregate([{"$group": {"_id": "$event_type", "t": {"$sum": "$amount"}}}]).to_list(20)
    benchmarks.append({"query": "financial aggregation by type", "ms": round((time.time() - t) * 1000, 1)})

    # Indexes
    index_info = {}
    for coll in ["events", "devices", "route_nor_periods", "route_exceptions"]:
        try:
            indexes = await db[coll].index_information()
            index_info[coll] = list(indexes.keys())
        except Exception:
            index_info[coll] = []

    # Scale projections
    current_devices = db_stats.get("devices", 0)
    year1_target = 6750
    year5_target = 9956
    events_per_min = 5
    hours_per_day = 16

    scale = {
        "current_devices": current_devices,
        "year1_target": year1_target,
        "year5_target": year5_target,
        "year1_daily_events": year1_target * events_per_min * 60 * hours_per_day,
        "year5_daily_events": year5_target * events_per_min * 60 * hours_per_day,
        "year1_events_per_sec": round(year1_target * events_per_min / 60, 1),
        "year5_events_per_sec": round(year5_target * events_per_min / 60, 1),
        "year5_annual_events_billions": round(year5_target * events_per_min * 60 * hours_per_day * 365 / 1e9, 2),
        "year5_meter_rows_billions": round(year5_target * 38 * 96 * 365 / 1e9, 2),
    }

    total_ms = round((time.time() - start) * 1000, 1)

    return {
        "db_stats": db_stats,
        "benchmarks": benchmarks,
        "indexes": index_info,
        "scale_projections": scale,
        "total_metrics_time_ms": total_ms,
        "targets": {
            "event_batch_target_ms": 200,
            "nor_query_target_ms": 2000,
            "exception_api_target_ms": 500,
            "dashboard_update_target_ms": 5000,
        },
    }


@router.get("/performance/indexes")
async def ensure_performance_indexes(request: Request):
    """Create/verify all performance indexes required for Module 8."""
    await require_role(request, ["admin"])
    created = []
    idx_specs = [
        ("events", [("occurred_at", -1)]),
        ("events", [("device_id", 1), ("occurred_at", -1)]),
        ("events", [("event_type", 1), ("occurred_at", -1)]),
        ("events", [("distributor_id", 1), ("occurred_at", -1)]),
        ("events", [("site_county", 1), ("occurred_at", -1)]),
        ("route_nor_periods", [("distributor_id", 1), ("period_start", -1)]),
        ("route_nor_periods", [("device_id", 1), ("period_start", -1)]),
        ("route_exceptions", [("is_active", 1), ("raised_at", -1)]),
        ("route_exceptions", [("distributor_id", 1), ("is_active", 1)]),
        ("route_integrity_checks", [("check_time", -1)]),
        ("route_integrity_checks", [("device_id", 1), ("check_time", -1)]),
        ("financial_events", [("occurred_at", -1)]),
        ("financial_events", [("event_type", 1), ("occurred_at", -1)]),
        ("meter_snapshots", [("device_id", 1), ("recorded_at", -1)]),
    ]
    for coll, keys in idx_specs:
        try:
            name = await db[coll].create_index(keys)
            created.append({"collection": coll, "index": name, "keys": str(keys)})
        except Exception as e:
            created.append({"collection": coll, "error": str(e)})
    return {"indexes_created": len(created), "details": created}


# ══════════════════════════════════════════════════
# NACHA ACH FILE FORMAT COMPLIANCE
# ══════════════════════════════════════════════════

def _pad(value, length, align='left', fill=' '):
    s = str(value)[:length]
    return s.ljust(length, fill) if align == 'left' else s.rjust(length, fill)

def _num(value, length):
    return str(int(value)).rjust(length, '0')[:length]

def _rec94(*fields):
    """Join fields and enforce exactly 94 characters."""
    line = ''.join(fields)
    if len(line) < 94:
        line = line + ' ' * (94 - len(line))
    return line[:94]


@router.post("/eft/generate-nacha")
async def generate_nacha_compliant(request: Request):
    """Generate a NACHA-compliant ACH file from NOR data."""
    user = await get_current_user(request)
    body = await request.json()
    period_start = body.get("period_start", (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d"))
    period_end = body.get("period_end", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    # Get distributor NOR totals
    match = {"period_start": {"$gte": period_start, "$lte": period_end}}
    pipe = [{"$match": match}, {"$group": {
        "_id": "$distributor_id",
        "total_nor": {"$sum": "$net_operating_revenue"},
        "device_count": {"$addToSet": "$device_id"},
    }}]
    results = await db.route_nor_periods.aggregate(pipe).to_list(100)

    distributors = {}
    for d in await db.route_distributors.find({}, {"_id": 0}).to_list(100):
        distributors[d["id"]] = d

    now = datetime.now(timezone.utc)
    file_date = now.strftime("%y%m%d")
    file_time = now.strftime("%H%M")
    lines = []

    # ── File Header Record (1) — exactly 94 chars ──
    # Positions: RecordType(1) PriorityCode(2) ImmDest(10) ImmOrigin(10) Date(6) Time(4) FileIDMod(1) RecSize(3) BlockFact(2) FormatCode(1) DestName(23) OriginName(23) RefCode(8)
    lines.append(_rec94(
        "1",                              # 1: Record Type Code
        "01",                             # 2-3: Priority Code
        _pad(" 091000019", 10),           # 4-13: Immediate Destination (b+routing)
        _pad("1234567890", 10),           # 14-23: Immediate Origin (company ID)
        file_date,                        # 24-29: File Creation Date YYMMDD
        file_time,                        # 30-33: File Creation Time HHMM
        "A",                              # 34: File ID Modifier
        "094",                            # 35-37: Record Size
        "10",                             # 38-39: Blocking Factor
        "1",                              # 40: Format Code
        _pad("FEDERAL RESERVE", 23),      # 41-63: Immediate Dest Name
        _pad("UGG GAMING GATEWAY", 23),   # 64-86: Immediate Origin Name
        _pad("UGGEFT", 8),               # 87-94: Reference Code
    ))

    batch_num = 0
    total_debit = 0
    total_credit = 0
    total_entries = 0
    entry_hash = 0

    for r in results:
        dist = distributors.get(r["_id"])
        if not dist or r["total_nor"] <= 0:
            continue

        batch_num += 1
        amount_cents = max(0, r["total_nor"])

        # ── Batch Header Record (5) — 94 chars ──
        # RecordType(1) ServiceClass(3) CompanyName(16) DiscretionaryData(20) CompanyID(10) SECCode(3) EntryDesc(10) CompDescDate(6) EffectiveDate(6) SettlementDate(3) OriginatorStatus(1) OriginatingDFI(8) BatchNum(7)
        lines.append(_rec94(
            "5",
            "220",
            _pad(dist.get("name", ""), 16),
            _pad("", 20),
            _pad(dist.get("state_license", ""), 10),
            "PPD",
            _pad("NOR SWEEP", 10),
            file_date,
            file_date,
            "   ",
            "1",
            _pad("09100001", 8),
            _num(batch_num, 7),
        ))

        # ── Entry Detail Record (6) — 94 chars ──
        # RecordType(1) TransCode(2) RDFI_Routing(9) DFIAcct(17) Amount(10) IndivID(15) IndivName(22) DiscData(2) AddendaInd(1) TraceNum(15)
        trace_seq = 1
        routing = dist.get("bank_routing", "091000019")[:9]
        account = dist.get("bank_account", "0000000000")
        entry_hash += int(routing[:8])

        lines.append(_rec94(
            "6",
            "22",
            _pad(routing, 9),
            _pad(account, 17),
            _num(amount_cents, 10),
            _pad(dist.get("state_license", ""), 15),
            _pad(dist.get("name", ""), 22),
            "  ",
            "0",
            _pad(routing[:8], 8) + _num(trace_seq, 7),
        ))
        total_credit += amount_cents
        total_entries += 1

        # ── Batch Control Record (8) — 94 chars ──
        # RecordType(1) ServiceClass(3) EntryCount(6) EntryHash(10) TotalDebit(12) TotalCredit(12) CompanyID(10) MsgAuthCode(19) Reserved(6) OriginatingDFI(8) BatchNum(7)
        lines.append(_rec94(
            "8",
            "220",
            _num(1, 6),
            _num(entry_hash % 10000000000, 10),
            _num(0, 12),
            _num(amount_cents, 12),
            _pad(dist.get("state_license", ""), 10),
            _pad("", 19),
            _pad("", 6),
            _pad("09100001", 8),
            _num(batch_num, 7),
        ))

    # ── File Control Record (9) — 94 chars ──
    # RecordType(1) BatchCount(6) BlockCount(6) EntryCount(8) EntryHash(10) TotalDebit(12) TotalCredit(12) Reserved(39)
    block_count = (len(lines) + 1 + 9) // 10
    lines.append(_rec94(
        "9",
        _num(batch_num, 6),
        _num(block_count, 6),
        _num(total_entries, 8),
        _num(entry_hash % 10000000000, 10),
        _num(total_debit, 12),
        _num(total_credit, 12),
        _pad("", 39),
    ))

    # Pad to blocking factor of 10
    while len(lines) % 10 != 0:
        lines.append("9" * 94)

    file_content = "\n".join(lines)
    filename = f"UGG_EFT_{now.strftime('%Y%m%d_%H%M%S')}.ach"
    file_hash = hashlib.sha256(file_content.encode()).hexdigest()

    # Validate
    validation = _validate_nacha(lines)

    # Store
    eft = {
        "id": str(uuid.uuid4()), "filename": filename,
        "period_start": period_start, "period_end": period_end,
        "sweep_type": body.get("sweep_type", "WEEKLY"),
        "total_amount_cents": total_credit, "entry_count": total_entries,
        "generated_at": now.isoformat(), "generated_by": user.get("email"),
        "file_hash": file_hash, "status": "GENERATED",
        "nacha_compliant": validation["valid"],
        "validation": validation,
        "transmitted_at": None, "notes": None,
    }
    await db.route_eft_files.insert_one(eft)
    eft.pop("_id", None)

    return {**eft, "file_content_preview": file_content[:500], "line_count": len(lines)}


def _validate_nacha(lines):
    """Validate NACHA file structure."""
    errors = []
    warnings = []

    if not lines:
        return {"valid": False, "errors": ["Empty file"], "warnings": []}

    # Check file header
    if lines[0][0] != "1":
        errors.append("Missing File Header Record (type 1)")
    elif len(lines[0]) != 94:
        errors.append(f"File Header wrong length: {len(lines[0])} (expected 94)")

    # Check file control
    non_pad = [l for l in lines if l != "9" * 94]
    if non_pad and non_pad[-1][0] != "9":
        errors.append("Missing File Control Record (type 9)")

    # Check blocking
    if len(lines) % 10 != 0:
        warnings.append(f"File not blocked to factor of 10 ({len(lines)} lines)")

    # Check record lengths
    for i, line in enumerate(lines):
        if len(line) != 94 and line != "9" * 94:
            errors.append(f"Line {i+1}: wrong length {len(line)} (expected 94)")
            break

    # Check batch pairing
    batch_headers = sum(1 for l in lines if l and l[0] == "5")
    batch_controls = sum(1 for l in lines if l and l[0] == "8")
    if batch_headers != batch_controls:
        errors.append(f"Batch mismatch: {batch_headers} headers vs {batch_controls} controls")

    checks_passed = [
        {"check": "File Header Record (1)", "passed": lines[0][0] == "1" if lines else False},
        {"check": "File Control Record (9)", "passed": non_pad[-1][0] == "9" if non_pad else False},
        {"check": "Record Length (94 chars)", "passed": all(len(l) == 94 for l in lines)},
        {"check": "Blocking Factor (10)", "passed": len(lines) % 10 == 0},
        {"check": "Batch Header/Control Pairs", "passed": batch_headers == batch_controls},
        {"check": "Entry Detail Records (6)", "passed": any(l[0] == "6" for l in lines if l)},
    ]

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "checks": checks_passed,
        "record_counts": {
            "file_header": sum(1 for l in lines if l and l[0] == "1"),
            "batch_header": batch_headers,
            "entry_detail": sum(1 for l in lines if l and l[0] == "6"),
            "batch_control": batch_controls,
            "file_control": 1 if non_pad and non_pad[-1][0] == "9" else 0,
            "padding": sum(1 for l in lines if l == "9" * 94),
        },
    }


@router.post("/eft/validate")
async def validate_nacha_file(request: Request):
    """Validate a NACHA file structure."""
    await get_current_user(request)
    body = await request.json()
    content = body.get("content", "")
    lines = content.strip().split("\n") if content else []
    validation = _validate_nacha(lines)
    return validation



# ══════════════════════════════════════════════════
# REGULATORY COMPLIANCE DASHBOARD — state_regulator
# ══════════════════════════════════════════════════

@router.get("/regulatory/dashboard")
async def regulatory_dashboard(request: Request):
    """Full regulatory compliance dashboard — requires state_regulator or admin role."""
    user = await get_current_user(request)
    role = user.get("role")
    if role not in ("state_regulator", "admin"):
        raise HTTPException(status_code=403, detail="Requires state_regulator or admin role")

    now = datetime.now(timezone.utc)
    d30 = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    d7 = (now - timedelta(days=7)).strftime("%Y-%m-%d")

    # ── Estate Overview ──
    total_devices = await db.devices.count_documents({})
    online_devices = await db.devices.count_documents({"status": "online"})
    total_distributors = await db.route_distributors.count_documents({})
    total_retailers = await db.route_retailers.count_documents({})

    # ── Statutory Compliance ──
    total_events = await db.events.count_documents({})
    enriched = await db.events.count_documents({"distributor_id": {"$exists": True, "$ne": None}})
    enrichment_rate = round(enriched / total_events * 100, 1) if total_events > 0 else 0

    # By county
    county_pipe = [
        {"$match": {"site_county": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$site_county", "events": {"$sum": 1}}},
        {"$sort": {"events": -1}},
    ]
    by_county = await db.events.aggregate(county_pipe).to_list(20)

    # ── Integrity Compliance ──
    int_total = await db.route_integrity_checks.count_documents({})
    int_pass = await db.route_integrity_checks.count_documents({"result": "PASS"})
    int_fail = await db.route_integrity_checks.count_documents({"result": "FAIL"})
    int_rate = round(int_pass / int_total * 100, 2) if int_total > 0 else 0

    # Failed checks detail
    failed_checks = await db.route_integrity_checks.find(
        {"result": "FAIL"}, {"_id": 0}
    ).sort("check_time", -1).limit(20).to_list(20)

    # By trigger type
    trigger_pipe = [{"$group": {"_id": "$trigger", "total": {"$sum": 1}, "passed": {"$sum": {"$cond": [{"$eq": ["$result", "PASS"]}, 1, 0]}}, "failed": {"$sum": {"$cond": [{"$eq": ["$result", "FAIL"]}, 1, 0]}}}}]
    by_trigger = await db.route_integrity_checks.aggregate(trigger_pipe).to_list(10)

    # ── NOR & Tax Revenue ──
    nor_pipe = [
        {"$match": {"period_start": {"$gte": d30}}},
        {"$group": {
            "_id": "$distributor_id",
            "coin_in": {"$sum": "$coin_in"}, "coin_out": {"$sum": "$coin_out"},
            "handpay": {"$sum": "$handpay_total"}, "voucher_out": {"$sum": "$voucher_out"},
            "nor": {"$sum": "$net_operating_revenue"}, "tax": {"$sum": "$tax_amount"},
            "devices": {"$addToSet": "$device_id"},
        }},
    ]
    nor_results = await db.route_nor_periods.aggregate(nor_pipe).to_list(100)
    dist_names = {d["id"]: d for d in await db.route_distributors.find({}, {"_id": 0}).to_list(100)}
    distributor_compliance = []
    grand_nor = 0
    grand_tax = 0
    grand_coin_in = 0
    for r in nor_results:
        dist = dist_names.get(r["_id"], {})
        nor_val = r["nor"]
        tax_val = r["tax"]
        coin_in = r["coin_in"]
        grand_nor += nor_val
        grand_tax += tax_val
        grand_coin_in += coin_in
        # Check device integrity compliance for this distributor
        dist_devices = r["devices"]
        dist_int_total = await db.route_integrity_checks.count_documents({"device_id": {"$in": dist_devices}})
        dist_int_pass = await db.route_integrity_checks.count_documents({"device_id": {"$in": dist_devices}, "result": "PASS"})
        dist_int_rate = round(dist_int_pass / dist_int_total * 100, 1) if dist_int_total > 0 else 0
        # Exception count
        dist_exc = await db.route_exceptions.count_documents({"distributor_id": r["_id"], "is_active": True})
        distributor_compliance.append({
            "distributor_id": r["_id"],
            "distributor_name": dist.get("name", "Unknown"),
            "state_license": dist.get("state_license", ""),
            "device_count": len(dist_devices),
            "coin_in": coin_in,
            "nor": nor_val,
            "tax_collected": tax_val,
            "tax_rate_bps": dist.get("tax_rate_bps", 500),
            "hold_pct": round(nor_val / coin_in * 100, 2) if coin_in > 0 else 0,
            "integrity_pass_rate": dist_int_rate,
            "active_exceptions": dist_exc,
            "compliance_score": _calc_compliance_score(enrichment_rate, dist_int_rate, dist_exc),
        })
    distributor_compliance.sort(key=lambda x: x["compliance_score"])

    # ── Daily NOR trend for all distributors ──
    trend_pipe = [
        {"$match": {"period_start": {"$gte": d30}}},
        {"$group": {"_id": "$period_start", "nor": {"$sum": "$net_operating_revenue"}, "tax": {"$sum": "$tax_amount"}, "coin_in": {"$sum": "$coin_in"}}},
        {"$sort": {"_id": 1}},
    ]
    daily_trend = await db.route_nor_periods.aggregate(trend_pipe).to_list(60)

    # ── Exception Summary ──
    exc_total = await db.route_exceptions.count_documents({"is_active": True})
    exc_critical = await db.route_exceptions.count_documents({"is_active": True, "severity": "CRITICAL"})
    exc_pipe = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    exc_by_type = await db.route_exceptions.aggregate(exc_pipe).to_list(20)

    # ── EFT Compliance ──
    eft_total = await db.route_eft_files.count_documents({})
    eft_transmitted = await db.route_eft_files.count_documents({"status": "TRANSMITTED"})
    eft_nacha_ok = await db.route_eft_files.count_documents({"nacha_compliant": True})
    eft_amount_pipe = [{"$group": {"_id": None, "total": {"$sum": "$total_amount_cents"}}}]
    eft_amounts = await db.route_eft_files.aggregate(eft_amount_pipe).to_list(1)
    total_eft_cents = eft_amounts[0]["total"] if eft_amounts else 0

    # ── Offline Buffer Risk ──
    buffer_states = await db.route_buffer_states.find({}, {"_id": 0}).to_list(100)
    agents_online = sum(1 for s in buffer_states if s["connectivity_state"] == "ONLINE")
    agents_offline = sum(1 for s in buffer_states if s["connectivity_state"] in ("OFFLINE", "AUTO_DISABLED"))
    total_pending = sum(s.get("pending_events", 0) for s in buffer_states)

    # ── Overall Compliance Score ──
    overall_score = _calc_compliance_score(enrichment_rate, int_rate, exc_critical)

    return {
        "estate": {"devices": total_devices, "online": online_devices, "distributors": total_distributors, "retailers": total_retailers},
        "statutory_compliance": {
            "total_events": total_events, "enriched": enriched, "rate": enrichment_rate,
            "by_county": [{"county": c["_id"], "events": c["events"]} for c in by_county],
        },
        "integrity_compliance": {
            "total_checks": int_total, "passed": int_pass, "failed": int_fail, "pass_rate": int_rate,
            "failed_checks": failed_checks,
            "by_trigger": [{"trigger": t["_id"], "total": t["total"], "passed": t["passed"], "failed": t["failed"]} for t in by_trigger],
        },
        "revenue": {
            "grand_coin_in": grand_coin_in, "grand_nor": grand_nor, "grand_tax": grand_tax,
            "hold_pct": round(grand_nor / grand_coin_in * 100, 2) if grand_coin_in > 0 else 0,
            "daily_trend": [{"date": d["_id"], "nor": d["nor"], "tax": d["tax"], "coin_in": d["coin_in"]} for d in daily_trend],
        },
        "distributor_compliance": distributor_compliance,
        "exceptions": {
            "total_active": exc_total, "critical": exc_critical,
            "by_type": [{"type": e["_id"], "count": e["count"]} for e in exc_by_type],
        },
        "eft_compliance": {
            "total_files": eft_total, "transmitted": eft_transmitted, "nacha_compliant": eft_nacha_ok,
            "total_swept_cents": total_eft_cents,
        },
        "buffer_risk": {"agents_online": agents_online, "agents_offline": agents_offline, "total_agents": len(buffer_states), "pending_events": total_pending},
        "overall_compliance_score": overall_score,
        "generated_at": now.isoformat(),
    }


def _calc_compliance_score(enrichment_rate, integrity_rate, critical_exceptions):
    """Calculate a 0-100 compliance score."""
    score = 0
    score += min(enrichment_rate, 100) * 0.30          # 30% weight: statutory enrichment
    score += min(integrity_rate, 100) * 0.40            # 40% weight: software integrity
    score += max(0, 100 - critical_exceptions * 10) * 0.20  # 20% weight: no critical exceptions
    score += 10                                          # 10% base for having the system running
    return round(min(score, 100), 1)


@router.get("/regulatory/distributor/{distributor_id}")
async def regulatory_distributor_detail(request: Request, distributor_id: str):
    """Detailed regulatory view for a single distributor."""
    user = await get_current_user(request)
    if user.get("role") not in ("state_regulator", "admin"):
        raise HTTPException(status_code=403, detail="Requires state_regulator or admin role")

    dist = await db.route_distributors.find_one({"id": distributor_id}, {"_id": 0})
    if not dist:
        raise HTTPException(status_code=404, detail="Distributor not found")

    d30 = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")

    # Devices
    devices = await db.devices.find({"distributor_id": distributor_id}, {"_id": 0, "id": 1, "external_ref": 1, "status": 1, "manufacturer": 1, "model": 1}).to_list(500)

    # NOR
    nor_pipe = [
        {"$match": {"distributor_id": distributor_id, "period_start": {"$gte": d30}}},
        {"$group": {"_id": "$period_start", "nor": {"$sum": "$net_operating_revenue"}, "coin_in": {"$sum": "$coin_in"}, "tax": {"$sum": "$tax_amount"}}},
        {"$sort": {"_id": 1}},
    ]
    nor_trend = await db.route_nor_periods.aggregate(nor_pipe).to_list(60)

    # Integrity for this distributor's devices
    device_ids = [d["id"] for d in devices]
    integrity = await db.route_integrity_checks.find({"device_id": {"$in": device_ids}}, {"_id": 0}).sort("check_time", -1).limit(50).to_list(50)

    # Exceptions
    exceptions = await db.route_exceptions.find({"distributor_id": distributor_id, "is_active": True}, {"_id": 0}).sort("raised_at", -1).to_list(50)

    # Retailers
    retailers = await db.route_retailers.find({"distributor_id": distributor_id}, {"_id": 0}).to_list(200)

    return {
        "distributor": dist,
        "devices": devices,
        "device_count": len(devices),
        "retailers": retailers,
        "retailer_count": len(retailers),
        "nor_trend": [{"date": n["_id"], "nor": n["nor"], "coin_in": n["coin_in"], "tax": n["tax"]} for n in nor_trend],
        "integrity_checks": integrity,
        "active_exceptions": exceptions,
    }
