import uuid
import random
from datetime import datetime, timezone, timedelta
from database import db
import logging

logger = logging.getLogger(__name__)

SAS_METER_MAP = [
    {"sasCode": "0000", "description": "Total Coin In Credits", "canonicalName": "coinIn", "isVendorExt": False},
    {"sasCode": "0001", "description": "Total Coin Out Credits", "canonicalName": "coinOut", "isVendorExt": False},
    {"sasCode": "0002", "description": "Total Jackpot Credits", "canonicalName": "jackpotTotal", "isVendorExt": True},
    {"sasCode": "0003", "description": "Total Hand Paid Cancelled Credits", "canonicalName": "handpayCash", "isVendorExt": False},
    {"sasCode": "0005", "description": "Games Played", "canonicalName": "gamesPlayed", "isVendorExt": False},
    {"sasCode": "0008", "description": "Total Credits from Bills In", "canonicalName": "billsIn", "isVendorExt": False},
    {"sasCode": "000D", "description": "Total SAS Cashable Ticket In", "canonicalName": "ticketCashOut", "isVendorExt": False},
    {"sasCode": "001D", "description": "Machine Paid Progressive Win", "canonicalName": "progressiveWon", "isVendorExt": False},
    {"sasCode": "0040", "description": "$1 Bills Accepted Count", "canonicalName": "bill1InCnt", "isVendorExt": True},
    {"sasCode": "0041", "description": "$2 Bills Accepted Count", "canonicalName": "bill2InCnt", "isVendorExt": True},
    {"sasCode": "0042", "description": "$5 Bills Accepted Count", "canonicalName": "bill5InCnt", "isVendorExt": True},
    {"sasCode": "0043", "description": "$10 Bills Accepted Count", "canonicalName": "bill10InCnt", "isVendorExt": True},
    {"sasCode": "0044", "description": "$20 Bills Accepted Count", "canonicalName": "bill20InCnt", "isVendorExt": True},
    {"sasCode": "0045", "description": "$50 Bills Accepted Count", "canonicalName": "bill50InCnt", "isVendorExt": True},
    {"sasCode": "0046", "description": "$100 Bills Accepted Count", "canonicalName": "bill100InCnt", "isVendorExt": True},
]

EXCEPTION_TYPES = ["DEVICE_OFFLINE", "SITE_CONTROLLER_OFFLINE", "INTEGRITY_VIOLATION", "DEVICE_DISABLED", "ZERO_PLAY_TODAY", "LOW_PLAY_ALERT", "AUTO_DISABLED_30DAY", "NSF_ALERT", "DOOR_OPEN", "HANDPAY_PENDING"]
EXCEPTION_SEV = {"DEVICE_OFFLINE": "CRITICAL", "SITE_CONTROLLER_OFFLINE": "CRITICAL", "INTEGRITY_VIOLATION": "CRITICAL", "DEVICE_DISABLED": "WARNING", "ZERO_PLAY_TODAY": "WARNING", "LOW_PLAY_ALERT": "INFO", "AUTO_DISABLED_30DAY": "CRITICAL", "NSF_ALERT": "CRITICAL", "DOOR_OPEN": "WARNING", "HANDPAY_PENDING": "WARNING"}
DISTRIBUTORS = [
    {"name": "Starlight Gaming Corp", "bank_routing": "091000019", "bank_account": "1234567890", "state_license": "DIS-2024-001"},
    {"name": "Pacific Route Services", "bank_routing": "021000021", "bank_account": "9876543210", "state_license": "DIS-2024-002"},
    {"name": "Midwest Amusement Group", "bank_routing": "071000013", "bank_account": "5551234567", "state_license": "DIS-2024-003"},
]
RETAILERS = [
    "Joe's Bar & Grill", "Lucky Strike Lanes", "Maverick Tavern", "Roadhouse 66",
    "The Golden Tap", "Sunset Lounge", "Crossroads Pub", "Eagle's Nest Bar",
    "Main Street Diner", "Riverview Tavern", "The Corner Pocket", "Blue Moon Saloon",
]


def _id():
    return str(uuid.uuid4())


def _past(hours_max=720):
    return (datetime.now(timezone.utc) - timedelta(hours=random.uniform(0, hours_max))).isoformat()


async def seed_route_module():
    if await db.route_distributors.count_documents({}) > 0:
        logger.info("Route module data already seeded, skipping")
        return

    logger.info("Seeding route module data...")
    devices = await db.devices.find({}, {"_id": 0}).to_list(200)
    sites = await db.sites.find({}, {"_id": 0}).to_list(20)
    if not devices or not sites:
        return
    tenant_id = devices[0].get("tenant_id")

    # Distributors
    distributors = []
    for i, d in enumerate(DISTRIBUTORS):
        dist = {"id": _id(), "tenant_id": tenant_id, "name": d["name"], "bank_routing": d["bank_routing"], "bank_account": d["bank_account"], "state_license": d["state_license"], "contact_email": f"ops@{d['name'].lower().replace(' ', '')}.com", "status": "active", "tax_rate_bps": random.choice([500, 600, 700]), "created_at": "2024-01-01T00:00:00Z"}
        distributors.append(dist)
    await db.route_distributors.insert_many(distributors)

    # Assign devices to distributors and create retailer sites
    retailer_sites = []
    device_assignments = []
    for i, device in enumerate(devices):
        dist = distributors[i % len(distributors)]
        retailer_name = RETAILERS[i % len(RETAILERS)]
        site = sites[i % len(sites)]
        counties = ["Clark", "Washoe", "Carson City", "Douglas", "Elko", "Lyon"]
        retailer = {
            "id": _id(), "tenant_id": tenant_id, "distributor_id": dist["id"],
            "name": retailer_name, "address": f"{random.randint(100,9999)} {random.choice(['Main', 'Oak', 'Elm', 'Pine', 'Cedar'])} St",
            "city": random.choice(["Las Vegas", "Reno", "Carson City", "Henderson", "Sparks"]),
            "county": random.choice(counties), "state": "NV", "zip": f"89{random.randint(100,999)}",
            "device_count": 0, "status": "active",
        }
        retailer_sites.append(retailer)
        device_assignments.append({"device_id": device["id"], "distributor_id": dist["id"], "retailer_id": retailer["id"]})

    await db.route_retailers.insert_many(retailer_sites)

    # Update devices with route info
    for da in device_assignments:
        await db.devices.update_one({"id": da["device_id"]}, {"$set": {"distributor_id": da["distributor_id"], "retailer_id": da["retailer_id"]}})

    # NOR Periods (daily for last 30 days)
    nor_periods = []
    now = datetime.now(timezone.utc)
    for device in devices:
        da = next(a for a in device_assignments if a["device_id"] == device["id"])
        for day in range(30):
            dt = now - timedelta(days=day)
            coin_in = random.randint(5000, 80000)
            coin_out = int(coin_in * random.uniform(0.75, 0.95))
            handpay = random.randint(0, int(coin_in * 0.05))
            voucher_out = random.randint(0, int(coin_in * 0.1))
            nor = coin_in - coin_out - handpay - voucher_out
            tax_rate = next(d for d in distributors if d["id"] == da["distributor_id"])["tax_rate_bps"]
            tax = int(nor * tax_rate / 10000)
            nor_periods.append({
                "id": _id(), "device_id": device["id"], "device_ref": device["external_ref"],
                "distributor_id": da["distributor_id"], "retailer_id": da["retailer_id"],
                "period_start": dt.strftime("%Y-%m-%d"), "period_end": dt.strftime("%Y-%m-%d"), "period_type": "DAILY",
                "coin_in": coin_in, "coin_out": coin_out, "handpay_total": handpay, "voucher_out": voucher_out,
                "gross_revenue": coin_in, "prizes_paid": coin_out + handpay + voucher_out,
                "net_operating_revenue": nor, "tax_rate_bps": tax_rate, "tax_amount": tax,
                "computed_at": dt.isoformat(),
            })
    await db.route_nor_periods.insert_many(nor_periods)

    # Monitoring Exceptions
    exceptions = []
    for _ in range(60):
        device = random.choice(devices)
        da = next(a for a in device_assignments if a["device_id"] == device["id"])
        etype = random.choice(EXCEPTION_TYPES)
        resolved = random.random() > 0.4
        retailer = next((r for r in retailer_sites if r["id"] == da["retailer_id"]), None)
        exc = {
            "id": _id(), "type": etype, "severity": EXCEPTION_SEV[etype],
            "device_id": device["id"], "device_ref": device["external_ref"],
            "device_description": f"{device['manufacturer']} {device['model']}",
            "site_id": da["retailer_id"], "site_name": retailer["name"] if retailer else "",
            "distributor_id": da["distributor_id"],
            "raised_at": _past(168), "resolved_at": _past(48) if resolved else None,
            "resolved_by": "admin@ugg.io" if resolved else None, "resolution_note": "Resolved by operator" if resolved else None,
            "detail": f"{etype.replace('_', ' ').title()} on {device['external_ref']} at {retailer['name'] if retailer else 'Unknown'}",
            "is_active": not resolved,
        }
        exceptions.append(exc)
    await db.route_exceptions.insert_many(exceptions)

    # Integrity Checks
    integrity_checks = []
    for device in devices[:40]:
        for _ in range(random.randint(1, 5)):
            passed = random.random() > 0.05
            integrity_checks.append({
                "id": _id(), "device_id": device["id"], "device_ref": device["external_ref"],
                "check_time": _past(168), "trigger": random.choice(["SCHEDULED", "REBOOT", "RECONNECT", "OPERATOR"]),
                "software_version": device.get("firmware_version", "v1.0"),
                "reported_signature": f"{'a' * 64}" if passed else f"{'b' * 64}",
                "expected_signature": f"{'a' * 64}",
                "result": "PASS" if passed else "FAIL",
                "action_taken": "NONE" if passed else "DEVICE_DISABLED",
            })
    await db.route_integrity_checks.insert_many(integrity_checks)

    # Offline Buffer State (per agent)
    agents = await db.agent_registrations.find({}, {"_id": 0}).to_list(20)
    buffer_states = []
    for agent in agents:
        buffer_states.append({
            "id": _id(), "agent_id": agent["id"], "agent_name": agent["name"],
            "site_id": agent.get("site_id"), "connectivity_state": random.choice(["ONLINE", "ONLINE", "ONLINE", "DEGRADED", "OFFLINE"]),
            "went_offline_at": _past(48) if random.random() > 0.7 else None,
            "last_sync_at": _past(1), "pending_events": random.randint(0, 500),
            "total_buffered": random.randint(0, 50000), "auto_disable_fired": False,
        })
    await db.route_buffer_states.insert_many(buffer_states)

    # EFT Files
    eft_files = []
    for week in range(4):
        dt = now - timedelta(weeks=week)
        total = random.randint(50000, 500000)
        eft_files.append({
            "id": _id(), "filename": f"UGG_EFT_{dt.strftime('%Y%m%d')}_120000.ach",
            "period_start": (dt - timedelta(days=7)).strftime("%Y-%m-%d"), "period_end": dt.strftime("%Y-%m-%d"),
            "sweep_type": "WEEKLY", "total_amount_cents": total, "entry_count": random.randint(20, 85),
            "generated_at": dt.isoformat(), "generated_by": "system",
            "file_hash": f"{uuid.uuid4().hex}{uuid.uuid4().hex}", "status": random.choice(["GENERATED", "TRANSMITTED", "TRANSMITTED"]),
            "transmitted_at": dt.isoformat() if random.random() > 0.3 else None, "notes": None,
        })
    await db.route_eft_files.insert_many(eft_files)

    # Indexes
    await db.route_nor_periods.create_index([("distributor_id", 1), ("period_start", -1)])
    await db.route_nor_periods.create_index("device_id")
    await db.route_exceptions.create_index([("is_active", 1), ("raised_at", -1)])
    await db.route_exceptions.create_index("distributor_id")
    await db.route_integrity_checks.create_index([("check_time", -1)])

    logger.info(f"Seeded route module: {len(distributors)} distributors, {len(retailer_sites)} retailers, {len(nor_periods)} NOR periods, {len(exceptions)} exceptions, {len(integrity_checks)} integrity checks, {len(eft_files)} EFT files")
