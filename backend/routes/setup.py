"""
Production Setup — First-run wizard, SEED_MODE control, clean database initialization.
Handles the transition from demo/development to live production deployment.
"""
from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import hash_password
import os
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/setup", tags=["setup"])

SEED_MODE = os.environ.get("SEED_MODE", "demo")  # "demo" | "production"


def is_production():
    return SEED_MODE == "production"


async def is_first_run() -> bool:
    """Check if this is a fresh database with no admin user."""
    admin_count = await db.users.count_documents({"role": "admin"})
    return admin_count == 0


@router.get("/status")
async def get_setup_status():
    """Public endpoint — check if the system needs initial setup."""
    first_run = await is_first_run()
    user_count = await db.users.count_documents({})
    device_count = await db.devices.count_documents({})
    tenant_count = await db.tenants.count_documents({})

    return {
        "needs_setup": first_run,
        "seed_mode": SEED_MODE,
        "is_production": is_production(),
        "has_admin": not first_run,
        "has_users": user_count > 0,
        "has_devices": device_count > 0,
        "has_tenants": tenant_count > 0,
        "user_count": user_count,
        "device_count": device_count,
        "version": "1.0.0",
    }


@router.post("/initialize")
async def initialize_system(request: Request):
    """
    First-run initialization. Creates the admin account and optional tenant.
    Only works if no admin exists yet.
    """
    first_run = await is_first_run()
    if not first_run:
        raise HTTPException(status_code=400, detail="System already initialized. An admin account exists.")

    body = await request.json()

    # Validate required fields
    admin_email = body.get("admin_email", "").strip().lower()
    admin_password = body.get("admin_password", "")
    admin_name = body.get("admin_name", "Administrator")

    if not admin_email or "@" not in admin_email:
        raise HTTPException(status_code=400, detail="Valid admin email is required")
    if not admin_password or len(admin_password) < 8:
        raise HTTPException(status_code=400, detail="Admin password must be at least 8 characters")

    now = datetime.now(timezone.utc).isoformat()

    # Create admin user
    admin_user = {
        "email": admin_email,
        "password_hash": hash_password(admin_password),
        "name": admin_name,
        "role": "admin",
        "tenant_id": None,
        "distributor_id": None,
        "retailer_id": None,
        "manufacturer_id": None,
        "created_at": now,
    }
    result = await db.users.insert_one(admin_user)
    admin_id = str(result.inserted_id)

    # Create tenant if provided
    tenant_id = None
    if body.get("company_name"):
        tenant_id = str(uuid.uuid4())
        await db.tenants.insert_one({
            "id": tenant_id,
            "name": body["company_name"],
            "config": {"timezone": body.get("timezone", "America/Los_Angeles"), "currency": body.get("currency", "USD")},
            "plan": body.get("plan", "enterprise"),
            "status": "active",
            "feature_flags": {"ai_studio": True, "emulator_lab": True, "messaging": True, "pirs": True},
            "created_at": now,
        })
        # Update admin with tenant
        await db.users.update_one({"email": admin_email}, {"$set": {"tenant_id": tenant_id}})

    # Create distributor if provided
    distributor_id = None
    if body.get("distributor_name"):
        distributor_id = str(uuid.uuid4())
        await db.route_distributors.insert_one({
            "id": distributor_id,
            "tenant_id": tenant_id,
            "name": body["distributor_name"],
            "bank_routing": body.get("bank_routing", ""),
            "bank_account": body.get("bank_account", ""),
            "state_license": body.get("state_license", ""),
            "contact_email": admin_email,
            "status": "active",
            "tax_rate_bps": body.get("tax_rate_bps", 500),
            "license_expires": body.get("license_expires"),
            "created_at": now,
        })

    # Create first site if provided
    site_id = None
    if body.get("first_site_name"):
        site_id = str(uuid.uuid4())
        await db.sites.insert_one({
            "id": site_id,
            "tenant_id": tenant_id,
            "name": body["first_site_name"],
            "location": body.get("first_site_address", ""),
            "timezone": body.get("timezone", "America/Los_Angeles"),
            "device_count": 0,
            "status": "active",
        })

    # Create default PIRS config
    from routes.pirs import DEFAULT_CONFIG
    await db.pirs_config.update_one({"type": "global"}, {"$set": {**DEFAULT_CONFIG, "type": "global", "updated_at": now}}, upsert=True)

    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.devices.create_index("id", unique=True)
    await db.events.create_index([("occurred_at", -1)])

    # Audit
    await db.audit_records.insert_one({
        "id": str(uuid.uuid4()), "tenant_id": tenant_id,
        "actor": admin_email, "action": "system.initialized",
        "target_type": "system", "target_id": "first_run",
        "before": None,
        "after": {"seed_mode": SEED_MODE, "admin_email": admin_email, "has_tenant": tenant_id is not None, "has_distributor": distributor_id is not None},
        "evidence_ref": None, "timestamp": now,
    })

    logger.info(f"System initialized: admin={admin_email}, tenant={body.get('company_name')}, mode={SEED_MODE}")

    return {
        "message": "System initialized successfully!",
        "admin_email": admin_email,
        "admin_id": admin_id,
        "tenant_id": tenant_id,
        "distributor_id": distributor_id,
        "site_id": site_id,
        "seed_mode": SEED_MODE,
        "next_steps": [
            "Log in with your admin credentials",
            "Add your sites in Settings > Sites",
            "Connect your EGMs (see Documentation > Setting Up Your Route)",
            "Configure PIRS Rewards budget in PIRS > Settings",
        ],
    }


@router.post("/load-demo-data")
async def load_demo_data(request: Request):
    """Manually trigger demo data load. Only works if admin exists (post-setup)."""
    from auth import get_current_user, require_role
    user = await require_role(request, ["admin"])

    # Check if demo data already exists
    if await db.devices.count_documents({}) > 10:
        raise HTTPException(status_code=400, detail="Demo data already loaded. Reset database first if you want to reload.")

    logger.info("Loading demo data by admin request...")

    from seed_data import seed_all
    await seed_all()
    from seed_financial import seed_financial_and_players
    await seed_financial_and_players()
    from seed_marketplace import seed_marketplace_and_jackpots
    await seed_marketplace_and_jackpots()
    from seed_route import seed_route_module
    await seed_route_module()
    from routes.hardware import seed_library
    await seed_library()
    from routes.route_v2 import seed_route_v2
    await seed_route_v2()
    from routes.portal import seed_portal
    await seed_portal()
    from routes.pirs import seed_pirs
    await seed_pirs()

    return {
        "message": "Demo data loaded successfully",
        "loaded": {
            "devices": await db.devices.count_documents({}),
            "events": await db.events.count_documents({}),
            "players": await db.pirs_players.count_documents({}),
            "retailers": await db.route_retailers.count_documents({}),
        },
    }


@router.post("/reset-demo-data")
async def reset_demo_data(request: Request):
    """Clear ALL data and start fresh. Requires admin. USE WITH EXTREME CAUTION."""
    from auth import require_role
    user = await require_role(request, ["admin"])
    body = await request.json()

    # Require explicit confirmation
    if body.get("confirm") != "DELETE_ALL_DATA":
        raise HTTPException(status_code=400, detail="Must send {\"confirm\": \"DELETE_ALL_DATA\"} to proceed. This action cannot be undone.")

    logger.warning(f"DATABASE RESET initiated by {user.get('email')}")

    # List of all collections to clear (except users — keep the admin)
    collections = [
        "devices", "events", "commands", "alerts", "meter_snapshots", "audit_records",
        "connectors", "manifests", "connector_mappings", "deployments",
        "tenants", "sites", "agent_registrations",
        "financial_events", "player_sessions", "message_campaigns",
        "marketplace_connectors", "marketplace_installs", "marketplace_reviews", "marketplace_revenue",
        "progressive_jackpots", "jackpot_history",
        "route_distributors", "route_retailers", "route_operators", "route_nor_periods",
        "route_exceptions", "route_integrity_checks", "route_buffer_states", "route_eft_files",
        "route_device_shares", "route_statutory_periods",
        "emulator_runs", "certification_runs", "signed_certificates",
        "ai_analytics_results", "ai_findings", "ai_studio_sessions", "ai_studio_chats",
        "lab_transcripts", "lab_scripts", "lab_script_runs", "lab_tar_reports", "lab_watchables",
        "lab_recordings", "lab_device_templates", "lab_production_sessions",
        "response_configurations", "fleet_runners",
        "proxy_instances", "analyzer_results", "security_audits", "session_audit", "scep_enrollments",
        "hw_test_results", "hw_library",
        "pirs_players", "pirs_rules", "pirs_config", "poc_awards", "poc_wallet", "venue_player_profiles", "maintenance_queue",
        "device_state_projection", "device_messages", "notifications", "announcements", "announcement_dismissals",
        "swf_analyses", "content_registry", "vip_alerts",
        "password_reset_tokens", "login_attempts",
    ]

    cleared = 0
    for coll in collections:
        result = await db[coll].delete_many({})
        cleared += result.deleted_count

    # Keep admin user but remove all others
    admin_email = user.get("email")
    await db.users.delete_many({"email": {"$ne": admin_email}})

    logger.warning(f"DATABASE RESET complete: {cleared} documents removed across {len(collections)} collections")

    return {
        "message": "All data cleared. System is ready for fresh setup.",
        "documents_removed": cleared,
        "collections_cleared": len(collections),
        "admin_preserved": admin_email,
        "next_steps": [
            "Add your real distributors, operators, and retailers",
            "Connect your EGMs",
            "Or click 'Load Demo Data' to reload sample data",
        ],
    }
