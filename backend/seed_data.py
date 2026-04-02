import uuid
import random
import hashlib
import json
from datetime import datetime, timezone, timedelta
from database import db
import logging

logger = logging.getLogger(__name__)

MANUFACTURERS = ["IGT", "Aristocrat", "Scientific Games", "Konami", "Everi", "AGS", "Ainsworth"]
MODELS = {
    "IGT": ["S3000", "CrystalDual", "PeakSlant49", "AvatarUX"],
    "Aristocrat": ["MarsX", "Helix+XT", "Arc Single", "Gen8"],
    "Scientific Games": ["TwinStar J43", "Gamefield xD", "Dualos"],
    "Konami": ["Dimension 49J", "Podium", "SeleXion"],
    "Everi": ["Empire Flex", "Core HDX"],
    "AGS": ["Orion Curve", "Orion Upright"],
    "Ainsworth": ["A640", "A600"],
}
PROTOCOLS = ["sas", "g2s", "vendor"]
PROTOCOL_VERSIONS = {"sas": ["6.02", "6.03"], "g2s": ["2.1", "3.0"], "vendor": ["1.0", "2.0"]}
STATUSES = ["online", "online", "online", "online", "offline", "error", "maintenance"]
GAME_NAMES = [
    "Buffalo Gold", "Lightning Link", "Dragon Link", "Wheel of Fortune",
    "88 Fortunes", "Lock It Link", "Cleopatra", "Dancing Drums",
    "Quick Hit", "Double Diamond", "Wolf Run", "Jackpot Party",
    "Fu Dai Lian Lian", "Huff N Puff", "Mighty Cash", "Walking Dead",
]
EVENT_TYPES = [
    "device.game.start", "device.game.end", "device.door.opened", "device.door.closed",
    "device.tilt", "device.voucher.in", "device.voucher.out", "device.jackpot.handpay",
    "device.meter.changed", "device.player.card.in", "device.player.card.out",
    "device.remote.disabled", "device.status.online", "device.status.offline",
    "device.health.check", "device.bonus.triggered",
]
EVENT_SEVERITIES = {
    "device.game.start": "info", "device.game.end": "info",
    "device.door.opened": "warning", "device.door.closed": "info",
    "device.tilt": "critical", "device.voucher.in": "info",
    "device.voucher.out": "info", "device.jackpot.handpay": "warning",
    "device.meter.changed": "info", "device.player.card.in": "info",
    "device.player.card.out": "info", "device.remote.disabled": "warning",
    "device.status.online": "info", "device.status.offline": "critical",
    "device.health.check": "info", "device.bonus.triggered": "info",
}
COMMAND_TYPES = ["device.enable", "device.disable", "device.send_message", "device.meter.read", "device.reboot", "device.config.update"]
ALERT_TYPES = [
    "Communication Lost", "Door Open Alert", "Tilt Detected",
    "Meter Discrepancy", "Low Paper", "Bill Jam",
    "Handpay Required", "RAM Error", "Progressive Link Down",
]


def gen_id():
    return str(uuid.uuid4())


def gen_serial():
    return f"{random.choice('ABCDEFGHIJ')}{random.randint(10000, 99999)}-{random.randint(100, 999)}"


def gen_firmware():
    return f"v{random.randint(2, 8)}.{random.randint(0, 9)}.{random.randint(0, 99)}"


def past_time(hours_ago_max=72):
    delta = timedelta(hours=random.uniform(0, hours_ago_max))
    return (datetime.now(timezone.utc) - delta).isoformat()


def recent_time(minutes_ago_max=60):
    delta = timedelta(minutes=random.uniform(0, minutes_ago_max))
    return (datetime.now(timezone.utc) - delta).isoformat()


async def seed_all():
    # Check if already seeded
    existing = await db.tenants.count_documents({})
    if existing > 0:
        logger.info("Data already seeded, skipping")
        return

    logger.info("Seeding UGG platform data...")

    # --- Tenants ---
    tenant_id = gen_id()
    tenant = {
        "id": tenant_id,
        "name": "Starlight Casino Group",
        "config": {"timezone": "America/Los_Angeles", "currency": "USD"},
        "plan": "enterprise",
        "status": "active",
        "feature_flags": {"ai_studio": True, "emulator_lab": True, "messaging": True},
        "created_at": "2024-01-15T00:00:00Z",
    }
    await db.tenants.insert_one(tenant)

    # --- Sites ---
    sites = [
        {"id": gen_id(), "tenant_id": tenant_id, "name": "Starlight Las Vegas", "location": "3700 Las Vegas Blvd S, Las Vegas, NV", "timezone": "America/Los_Angeles", "device_count": 0, "status": "active"},
        {"id": gen_id(), "tenant_id": tenant_id, "name": "Starlight Atlantic City", "location": "2100 Pacific Ave, Atlantic City, NJ", "timezone": "America/New_York", "device_count": 0, "status": "active"},
        {"id": gen_id(), "tenant_id": tenant_id, "name": "Starlight Reno", "location": "450 N Virginia St, Reno, NV", "timezone": "America/Los_Angeles", "device_count": 0, "status": "active"},
    ]
    await db.sites.insert_many(sites)
    site_ids = [s["id"] for s in sites]

    # --- Connectors ---
    connectors = [
        {"id": gen_id(), "name": "SAS Primary Adapter", "type": "sas", "language": "python", "version": "2.1.0", "status": "active", "created_at": "2024-03-01T00:00:00Z"},
        {"id": gen_id(), "name": "G2S XML Adapter", "type": "g2s", "language": "python", "version": "1.4.2", "status": "active", "created_at": "2024-03-15T00:00:00Z"},
        {"id": gen_id(), "name": "Konami REST Connector", "type": "rest_poll", "language": "python", "version": "1.0.0", "status": "active", "created_at": "2024-06-01T00:00:00Z"},
        {"id": gen_id(), "name": "Everi DB Connector", "type": "db_poll", "language": "python", "version": "0.9.1", "status": "draft", "created_at": "2024-08-01T00:00:00Z"},
    ]
    await db.connectors.insert_many(connectors)
    connector_map = {"sas": connectors[0]["id"], "g2s": connectors[1]["id"], "vendor": connectors[2]["id"]}

    # --- Devices ---
    devices = []
    for i in range(85):
        mfr = random.choice(MANUFACTURERS)
        model = random.choice(MODELS[mfr])
        proto = random.choice(PROTOCOLS)
        status = random.choices(STATUSES, weights=[4, 4, 4, 4, 1, 1, 1])[0]
        site_id = random.choice(site_ids)
        device = {
            "id": gen_id(),
            "external_ref": f"EGM-{1000 + i:04d}",
            "tenant_id": tenant_id,
            "site_id": site_id,
            "device_type": "egm",
            "manufacturer": mfr,
            "model": model,
            "serial_number": gen_serial(),
            "protocol_family": proto,
            "protocol_version": random.choice(PROTOCOL_VERSIONS[proto]),
            "connector_id": connector_map.get(proto, connectors[0]["id"]),
            "status": status,
            "last_seen_at": recent_time(30) if status == "online" else past_time(48),
            "registered_at": past_time(720),
            "firmware_version": gen_firmware(),
            "location_tag": {"floor": random.randint(1, 3), "zone": random.choice(["A", "B", "C", "D"]), "position": random.randint(1, 50)},
            "metadata": {"game_title": random.choice(GAME_NAMES), "denomination": random.choice([0.01, 0.05, 0.25, 1.00, 5.00])},
            "schema_version": 1,
        }
        devices.append(device)
    await db.devices.insert_many(devices)

    # Update site device counts
    for site in sites:
        count = sum(1 for d in devices if d["site_id"] == site["id"])
        await db.sites.update_one({"id": site["id"]}, {"$set": {"device_count": count}})

    # --- Device Capabilities ---
    capabilities = []
    for d in devices:
        cap = {
            "device_id": d["id"],
            "supports_messaging": random.choice([True, True, False]),
            "message_surface_type": random.choice(["native_g2s", "overlay", "external_display", "none"]),
            "supports_remote_disable": True,
            "supports_remote_enable": True,
            "supports_meter_readback": True,
            "supports_player_tracking": random.choice([True, True, False]),
            "supports_voucher": random.choice([True, True, True, False]),
            "supports_progressive": random.choice([True, False]),
            "supports_bonus": random.choice([True, False]),
            "supports_health_telemetry": random.choice([True, True, False]),
            "capability_schema_version": 1,
            "last_negotiated_at": recent_time(60),
        }
        capabilities.append(cap)
    await db.device_capabilities.insert_many(capabilities)

    # --- Events ---
    events = []
    for _ in range(500):
        device = random.choice(devices)
        event_type = random.choice(EVENT_TYPES)
        occurred = past_time(24)
        payload_data = {}
        if "game" in event_type:
            payload_data = {"game_id": random.randint(1, 50), "denomination": device["metadata"]["denomination"], "bet": round(random.uniform(0.25, 50.0), 2)}
            if event_type == "device.game.end":
                payload_data["win"] = round(random.uniform(0, 500.0), 2)
        elif "meter" in event_type:
            payload_data = {"coin_in": random.randint(10000, 999999), "coin_out": random.randint(5000, 800000), "games_played": random.randint(100, 50000)}
        elif "door" in event_type:
            payload_data = {"door_type": random.choice(["main", "belly", "stacker", "top_box"])}
        elif "voucher" in event_type:
            payload_data = {"amount": round(random.uniform(1.0, 1000.0), 2), "barcode": f"VCH{random.randint(100000000, 999999999)}"}
        elif "player" in event_type:
            payload_data = {"player_id": f"PL-{random.randint(10000, 99999)}"}

        payload_json = json.dumps(payload_data)
        integrity = hashlib.sha256(payload_json.encode()).hexdigest()

        event = {
            "id": gen_id(),
            "tenant_id": tenant_id,
            "site_id": device["site_id"],
            "device_id": device["id"],
            "connector_id": device["connector_id"],
            "event_type": event_type,
            "source_protocol": device["protocol_family"],
            "severity": EVENT_SEVERITIES.get(event_type, "info"),
            "occurred_at": occurred,
            "ingested_at": occurred,
            "payload": payload_data,
            "integrity_hash": integrity[:32],
            "correlation_id": gen_id(),
            "replay_marker": False,
            "schema_version": 1,
        }
        events.append(event)
    events.sort(key=lambda e: e["occurred_at"], reverse=True)
    await db.events.insert_many(events)

    # --- Commands ---
    commands = []
    cmd_statuses = ["completed", "completed", "completed", "pending", "dispatched", "failed", "timeout"]
    for _ in range(50):
        device = random.choice(devices)
        cmd_type = random.choice(COMMAND_TYPES)
        status = random.choice(cmd_statuses)
        issued = past_time(48)
        cmd = {
            "id": gen_id(),
            "idempotency_key": gen_id()[:16],
            "tenant_id": tenant_id,
            "target_device_id": device["id"],
            "device_ref": device["external_ref"],
            "command_type": cmd_type,
            "parameters": {},
            "issued_by": "admin",
            "issued_at": issued,
            "status": status,
            "result": {"success": True} if status == "completed" else None,
            "error_detail": {"code": "TIMEOUT", "message": "Device did not respond"} if status in ["failed", "timeout"] else None,
            "retry_count": random.randint(0, 2) if status in ["failed", "timeout"] else 0,
            "correlation_id": gen_id(),
            "schema_version": 1,
        }
        commands.append(cmd)
    await db.commands.insert_many(commands)

    # --- Alerts ---
    alerts = []
    alert_statuses = ["active", "active", "active", "acknowledged", "resolved"]
    severities = ["critical", "warning", "warning", "info"]
    for _ in range(40):
        device = random.choice(devices)
        alert = {
            "id": gen_id(),
            "tenant_id": tenant_id,
            "site_id": device["site_id"],
            "device_id": device["id"],
            "device_ref": device["external_ref"],
            "alert_type": random.choice(ALERT_TYPES),
            "severity": random.choice(severities),
            "message": "",
            "status": random.choice(alert_statuses),
            "created_at": past_time(48),
            "acknowledged_at": None,
            "resolved_at": None,
        }
        alert["message"] = f"{alert['alert_type']} on {device['external_ref']} ({device['manufacturer']} {device['model']})"
        if alert["status"] == "acknowledged":
            alert["acknowledged_at"] = recent_time(120)
        elif alert["status"] == "resolved":
            alert["acknowledged_at"] = past_time(24)
            alert["resolved_at"] = recent_time(120)
        alerts.append(alert)
    await db.alerts.insert_many(alerts)

    # --- Meter Snapshots ---
    meter_snapshots = []
    for device in devices[:30]:
        for h in range(0, 24, 4):
            snap = {
                "id": gen_id(),
                "device_id": device["id"],
                "tenant_id": tenant_id,
                "coin_in": random.randint(50000, 999999),
                "coin_out": random.randint(30000, 800000),
                "games_played": random.randint(500, 10000),
                "jackpots": random.randint(0, 5),
                "bills_in": random.randint(1000, 50000),
                "voucher_in": random.randint(0, 20000),
                "voucher_out": random.randint(0, 15000),
                "recorded_at": (datetime.now(timezone.utc) - timedelta(hours=h)).isoformat(),
            }
            meter_snapshots.append(snap)
    await db.meter_snapshots.insert_many(meter_snapshots)

    # --- Audit Records ---
    audit_records = []
    actions = ["device.registered", "command.issued", "connector.deployed", "user.login", "alert.acknowledged", "config.updated"]
    for _ in range(100):
        record = {
            "id": gen_id(),
            "tenant_id": tenant_id,
            "actor": random.choice(["admin@ugg.io", "operator@ugg.io", "system"]),
            "action": random.choice(actions),
            "target_type": random.choice(["device", "connector", "user", "alert"]),
            "target_id": gen_id(),
            "before": None,
            "after": None,
            "evidence_ref": f"evt-{gen_id()[:8]}",
            "timestamp": past_time(72),
        }
        audit_records.append(record)
    await db.audit_records.insert_many(audit_records)

    # --- Agent Registrations ---
    agents = [
        {"id": gen_id(), "name": f"ugg-agent-{sites[i]['name'].split()[-1].lower()}", "site_id": sites[i]["id"], "tenant_id": tenant_id, "version": "1.2.0", "status": "connected", "last_heartbeat": recent_time(5), "os": random.choice(["Windows Server 2022", "Ubuntu 22.04"]), "ip_address": f"10.0.{i+1}.100"}
        for i in range(len(sites))
    ]
    await db.agent_registrations.insert_many(agents)

    # --- Manifests ---
    manifests = [
        {"id": gen_id(), "connector_id": connectors[0]["id"], "name": "SAS 6.02 Standard Manifest", "version": "1.0.0", "status": "approved", "field_mappings": 42, "command_bindings": 8, "approved_by": "admin@ugg.io", "approved_at": "2024-04-01T00:00:00Z", "created_at": "2024-03-28T00:00:00Z"},
        {"id": gen_id(), "connector_id": connectors[1]["id"], "name": "G2S 2.1 Full Coverage", "version": "1.0.0", "status": "approved", "field_mappings": 67, "command_bindings": 15, "approved_by": "admin@ugg.io", "approved_at": "2024-04-15T00:00:00Z", "created_at": "2024-04-10T00:00:00Z"},
        {"id": gen_id(), "connector_id": connectors[2]["id"], "name": "Konami REST Mapping", "version": "0.9.0", "status": "draft", "field_mappings": 28, "command_bindings": 4, "approved_by": None, "approved_at": None, "created_at": "2024-07-01T00:00:00Z"},
    ]
    await db.manifests.insert_many(manifests)

    # --- Message Campaigns ---
    campaigns = [
        {"id": gen_id(), "tenant_id": tenant_id, "name": "Weekend Bonus Promo", "content": "Earn 2X points this weekend!", "target_sites": [sites[0]["id"]], "target_device_count": 30, "status": "delivered", "created_at": past_time(48), "delivered_count": 28, "failed_count": 2},
        {"id": gen_id(), "tenant_id": tenant_id, "name": "Maintenance Notice", "content": "Scheduled maintenance tonight 2-4 AM", "target_sites": site_ids, "target_device_count": 85, "status": "scheduled", "created_at": recent_time(120), "delivered_count": 0, "failed_count": 0},
    ]
    await db.message_campaigns.insert_many(campaigns)

    # Create indexes
    await db.devices.create_index("id", unique=True)
    await db.devices.create_index("tenant_id")
    await db.devices.create_index("site_id")
    await db.devices.create_index("status")
    await db.events.create_index("id", unique=True)
    await db.events.create_index([("occurred_at", -1)])
    await db.events.create_index("device_id")
    await db.events.create_index("event_type")
    await db.commands.create_index("id", unique=True)
    await db.alerts.create_index("id", unique=True)
    await db.alerts.create_index("status")
    await db.audit_records.create_index([("timestamp", -1)])
    await db.connectors.create_index("id", unique=True)

    logger.info(f"Seeded: {len(devices)} devices, {len(events)} events, {len(commands)} commands, {len(alerts)} alerts, {len(audit_records)} audit records")
