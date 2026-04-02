import uuid
import random
from datetime import datetime, timezone, timedelta
from database import db
import logging

logger = logging.getLogger(__name__)

CONNECTOR_VENDORS = [
    {"name": "SlotTech Solutions", "verified": True},
    {"name": "GamingBridge Inc.", "verified": True},
    {"name": "CasinoConnect Pro", "verified": True},
    {"name": "EGM Integrators Ltd", "verified": False},
    {"name": "PlayLink Systems", "verified": True},
    {"name": "WagerWorks Labs", "verified": False},
    {"name": "BetStream Analytics", "verified": True},
]

PROGRESSIVE_NAMES = [
    "Mega Jackpot", "Grand Fortune", "Diamond Millions", "Lightning Millions",
    "Royal Flush Progressive", "Lucky 7s Linked", "Golden Dragon Progressive",
    "Cash Wheel Mega", "Power Jackpot", "Ultra Hot Progressive",
]


def _id():
    return str(uuid.uuid4())


def _past(hours_max=72):
    return (datetime.now(timezone.utc) - timedelta(hours=random.uniform(0, hours_max))).isoformat()


async def seed_marketplace_and_jackpots():
    if await db.marketplace_connectors.count_documents({}) > 0:
        logger.info("Marketplace/jackpot data already seeded, skipping")
        return

    logger.info("Seeding marketplace connectors and progressive jackpots...")

    devices = await db.devices.find({}, {"_id": 0, "id": 1, "external_ref": 1, "tenant_id": 1, "site_id": 1}).to_list(200)
    sites = await db.sites.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(20)
    if not devices:
        return
    tenant_id = devices[0].get("tenant_id")
    site_map = {s["id"]: s["name"] for s in sites}

    # --- Marketplace Connectors ---
    categories = ["SAS Adapters", "G2S Adapters", "Vendor REST", "Analytics", "Loyalty", "CMS Integration", "Regulatory"]
    marketplace = []
    connector_names = [
        ("SAS 6.03 Advanced Adapter", "SAS Adapters", "Full SAS 6.03 support with AFT, multi-denomination, and progressive metering"),
        ("G2S 3.0 Premium Suite", "G2S Adapters", "Complete G2S 3.0 class coverage with subscription management"),
        ("Aristocrat Gen8 REST Bridge", "Vendor REST", "Native REST API connector for Aristocrat Gen8 platform"),
        ("Konami Synkros Connector", "Vendor REST", "Full bidirectional integration with Konami Synkros CMS"),
        ("IGT Advantage Adapter", "CMS Integration", "Direct integration with IGT Advantage player tracking"),
        ("Real-Time Floor Analytics", "Analytics", "Live floor performance analytics with AI predictions"),
        ("Compliance Reporter Pro", "Regulatory", "Automated regulatory reporting for multi-jurisdiction estates"),
        ("Player Loyalty Bridge", "Loyalty", "Universal loyalty system connector supporting points, tiers, offers"),
        ("Everi CashClub Connector", "Vendor REST", "Connect Everi CashClub systems to UGG event pipeline"),
        ("Scientific Games SDS Link", "Vendor REST", "Bidirectional SDS integration for Scientific Games estate"),
        ("Multi-Site Meter Aggregator", "Analytics", "Cross-site meter aggregation with variance detection"),
        ("TITO Voucher Manager", "CMS Integration", "Advanced TITO management with cross-property voucher support"),
    ]

    for i, (name, cat, desc) in enumerate(connector_names):
        vendor = random.choice(CONNECTOR_VENDORS)
        marketplace.append({
            "id": _id(),
            "name": name,
            "vendor_name": vendor["name"],
            "vendor_verified": vendor["verified"],
            "category": cat,
            "description": desc,
            "version": f"{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}",
            "protocol_support": random.sample(["sas", "g2s", "vendor", "hybrid"], random.randint(1, 3)),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "reviews": random.randint(3, 120),
            "installs": random.randint(10, 500),
            "price_model": random.choice(["free", "per_device", "subscription", "one_time"]),
            "price": round(random.choice([0, 0, 2.50, 5.00, 10.00, 25.00, 50.00, 99.00]), 2),
            "status": random.choice(["published", "published", "published", "beta"]),
            "certified": random.choice([True, True, False]),
            "tags": random.sample(["production-ready", "multi-site", "real-time", "analytics", "compliance", "loyalty", "progressive", "AFT", "TITO"], random.randint(2, 5)),
            "created_at": _past(2160),
            "updated_at": _past(168),
        })
    await db.marketplace_connectors.insert_many(marketplace)

    # --- Progressive Jackpots ---
    jackpots = []
    for i, name in enumerate(PROGRESSIVE_NAMES):
        site_id = random.choice([s["id"] for s in sites])
        linked_devices = random.sample([d["id"] for d in devices if d.get("site_id") == site_id] or [d["id"] for d in devices[:10]], min(random.randint(3, 15), 10))
        base = random.choice([1000, 5000, 10000, 25000, 50000, 100000])
        current = base + random.uniform(base * 0.1, base * 2.5)
        ceiling = base * 5

        jackpots.append({
            "id": _id(),
            "tenant_id": tenant_id,
            "site_id": site_id,
            "site_name": site_map.get(site_id, ""),
            "name": name,
            "type": random.choice(["standalone", "linked", "wide_area"]),
            "base_amount": float(base),
            "current_amount": round(current, 2),
            "ceiling_amount": float(ceiling),
            "contribution_rate": round(random.uniform(0.5, 3.0), 2),
            "linked_device_count": len(linked_devices),
            "linked_device_ids": linked_devices,
            "status": random.choice(["active", "active", "active", "hit_pending", "suspended"]),
            "last_hit_amount": round(random.uniform(base, current), 2) if random.random() > 0.3 else None,
            "last_hit_at": _past(720) if random.random() > 0.3 else None,
            "last_hit_device": random.choice(linked_devices) if random.random() > 0.3 else None,
            "total_hits": random.randint(0, 25),
            "total_paid": round(random.uniform(0, base * 10), 2),
            "created_at": _past(4380),
        })
    await db.progressive_jackpots.insert_many(jackpots)

    # --- Jackpot History ---
    jp_history = []
    for jp in jackpots:
        for _ in range(jp["total_hits"]):
            hit_amount = round(random.uniform(jp["base_amount"], jp["ceiling_amount"] * 0.8), 2)
            dev = random.choice(jp["linked_device_ids"]) if jp["linked_device_ids"] else None
            dev_doc = next((d for d in devices if d["id"] == dev), None) if dev else None
            jp_history.append({
                "id": _id(),
                "jackpot_id": jp["id"],
                "jackpot_name": jp["name"],
                "tenant_id": tenant_id,
                "site_id": jp["site_id"],
                "device_id": dev,
                "device_ref": dev_doc["external_ref"] if dev_doc else None,
                "hit_amount": hit_amount,
                "hit_at": _past(2160),
                "player_id": f"PL-{random.randint(20000, 20049)}" if random.random() > 0.4 else None,
                "status": "paid",
            })
    if jp_history:
        jp_history.sort(key=lambda x: x["hit_at"], reverse=True)
        await db.jackpot_history.insert_many(jp_history)

    await db.marketplace_connectors.create_index("category")
    await db.progressive_jackpots.create_index("status")
    await db.jackpot_history.create_index([("hit_at", -1)])

    logger.info(f"Seeded: {len(marketplace)} marketplace connectors, {len(jackpots)} jackpots, {len(jp_history)} jackpot hits")
