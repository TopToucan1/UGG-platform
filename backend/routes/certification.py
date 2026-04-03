from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import uuid
import random
import hashlib
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/certification", tags=["certification"])

# G2S 14-class test suite definition
G2S_CLASSES = [
    {"id": "cabinet", "name": "Cabinet", "description": "Cabinet device health, component status, door states", "test_count": 12},
    {"id": "communications", "name": "Communications", "description": "Connectivity management, heartbeat, keep-alive", "test_count": 8},
    {"id": "eventHandler", "name": "Event Handler", "description": "Event subscription, delivery, acknowledgement", "test_count": 10},
    {"id": "gamePlay", "name": "Game Play", "description": "Game cycles, bet amounts, win amounts, recall", "test_count": 15},
    {"id": "meters", "name": "Meters", "description": "Meter readback by type and denomination", "test_count": 14},
    {"id": "noteAcceptor", "name": "Note Acceptor", "description": "Bill validator events and cashbox status", "test_count": 8},
    {"id": "coinAcceptor", "name": "Coin Acceptor", "description": "Coin-in events and hopper status", "test_count": 6},
    {"id": "printer", "name": "Printer", "description": "Voucher printer events and error states", "test_count": 7},
    {"id": "voucher", "name": "Voucher", "description": "TITO in/out event handling", "test_count": 11},
    {"id": "bonus", "name": "Bonus", "description": "System-triggered bonus award commands", "test_count": 9},
    {"id": "player", "name": "Player", "description": "Player tracking session events", "test_count": 8},
    {"id": "progressive", "name": "Progressive", "description": "Progressive jackpot level management", "test_count": 10},
    {"id": "mediaDisplay", "name": "Media Display", "description": "On-device display commands and acks", "test_count": 6},
    {"id": "handpay", "name": "Handpay", "description": "Handpay events and key-off procedures", "test_count": 7},
]

TIERS = {
    "bronze": {"label": "Bronze", "classes": ["cabinet", "communications", "eventHandler", "meters"], "min_pass_rate": 80},
    "silver": {"label": "Silver", "classes": ["cabinet", "communications", "eventHandler", "meters", "gamePlay", "noteAcceptor", "voucher", "printer"], "min_pass_rate": 90},
    "gold": {"label": "Gold", "classes": ["cabinet", "communications", "eventHandler", "meters", "gamePlay", "noteAcceptor", "voucher", "printer", "bonus", "player", "progressive"], "min_pass_rate": 95},
    "platinum": {"label": "Platinum", "classes": [c["id"] for c in G2S_CLASSES], "min_pass_rate": 98},
}


@router.get("/classes")
async def get_test_classes(request: Request):
    await get_current_user(request)
    return {"classes": G2S_CLASSES, "total_tests": sum(c["test_count"] for c in G2S_CLASSES)}


@router.get("/tiers")
async def get_tiers(request: Request):
    await get_current_user(request)
    return {"tiers": {k: {**v, "class_count": len(v["classes"]), "total_tests": sum(c["test_count"] for c in G2S_CLASSES if c["id"] in v["classes"])} for k, v in TIERS.items()}}


@router.post("/run")
async def run_certification(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    device_id = body.get("device_id")
    tier = body.get("tier", "bronze")
    run_failed_only = body.get("run_failed_only", False)

    if tier not in TIERS:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")

    tier_config = TIERS[tier]
    included_classes = tier_config["classes"]
    now = datetime.now(timezone.utc)

    # Look up device
    device = await db.devices.find_one({"id": device_id}, {"_id": 0}) if device_id else None

    # Generate test results (simulated)
    class_results = []
    total_pass = 0
    total_fail = 0
    total_skip = 0

    for cls in G2S_CLASSES:
        included = cls["id"] in included_classes
        tests = []
        cls_pass = 0
        cls_fail = 0

        for t in range(cls["test_count"]):
            if not included:
                tests.append({
                    "id": f"{cls['id']}_test_{t+1:03d}",
                    "name": f"{cls['name']} Test {t+1}",
                    "status": "skipped",
                    "duration_ms": 0,
                    "message": None,
                })
                total_skip += 1
                continue

            # Simulate realistic pass/fail rates (high pass rate)
            passed = random.random() < 0.94
            duration = random.randint(50, 2000)
            violation_msg = None
            if not passed:
                violation_msg = random.choice([
                    f"Expected g2sAck within 5000ms, received after {random.randint(5001, 15000)}ms",
                    f"Invalid {cls['id']}Status value: expected 'G2S_enabled', got 'G2S_unknown'",
                    f"Missing required attribute '{cls['id']}Id' in response",
                    f"Meter value mismatch: expected incrementing, got reset",
                    f"Subscription delivery failed: event not received within timeout",
                ])

            tests.append({
                "id": f"{cls['id']}_test_{t+1:03d}",
                "name": f"{cls['name']} Test {t+1}",
                "status": "passed" if passed else "failed",
                "duration_ms": duration,
                "message": violation_msg,
                "transcript_snippet": f"<g2s:{cls['id']}Status g2s:deviceId='G2S_{device_id or 'EGM001'}' />" if not passed else None,
            })
            if passed:
                cls_pass += 1
                total_pass += 1
            else:
                cls_fail += 1
                total_fail += 1

        class_results.append({
            "class_id": cls["id"],
            "class_name": cls["name"],
            "included": included,
            "test_count": cls["test_count"],
            "passed": cls_pass,
            "failed": cls_fail,
            "status": "skipped" if not included else ("passed" if cls_fail == 0 else "failed"),
        })

    total_tests = total_pass + total_fail
    pass_rate = round(total_pass / total_tests * 100, 1) if total_tests > 0 else 0
    overall_pass = pass_rate >= tier_config["min_pass_rate"]
    elapsed = sum(t["duration_ms"] for cr in class_results for t in [] ) # simplified

    run_record = {
        "id": str(uuid.uuid4()),
        "device_id": device_id,
        "device_ref": device.get("external_ref") if device else None,
        "manufacturer": device.get("manufacturer") if device else None,
        "model": device.get("model") if device else None,
        "tier": tier,
        "tier_label": tier_config["label"],
        "status": "PASSED" if overall_pass else "FAILED",
        "total_tests": total_tests,
        "total_passed": total_pass,
        "total_failed": total_fail,
        "total_skipped": total_skip,
        "pass_rate": pass_rate,
        "min_pass_rate": tier_config["min_pass_rate"],
        "class_results": class_results,
        "started_at": now.isoformat(),
        "completed_at": (now + timedelta(seconds=random.randint(30, 180))).isoformat(),
        "run_by": user.get("email"),
        "certificate_id": str(uuid.uuid4()) if overall_pass else None,
    }

    await db.certification_runs.insert_one(run_record)
    run_record.pop("_id", None)
    return run_record


@router.get("/runs")
async def list_runs(request: Request, limit: int = 20):
    await get_current_user(request)
    runs = await db.certification_runs.find({}, {"_id": 0, "class_results": 0}).sort("started_at", -1).limit(limit).to_list(limit)
    return {"runs": runs, "total": await db.certification_runs.count_documents({})}


@router.get("/runs/{run_id}")
async def get_run(request: Request, run_id: str):
    await get_current_user(request)
    run = await db.certification_runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/certificate/{run_id}")
async def get_certificate(request: Request, run_id: str):
    await get_current_user(request)
    run = await db.certification_runs.find_one({"id": run_id, "status": "PASSED"}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="No passing certificate for this run")
    return {
        "certificate_id": run.get("certificate_id"),
        "tier": run["tier_label"],
        "device": run.get("device_ref") or run.get("device_id"),
        "manufacturer": run.get("manufacturer"),
        "model": run.get("model"),
        "pass_rate": run["pass_rate"],
        "total_tests": run["total_tests"],
        "issued_at": run["completed_at"],
        "issued_by": "UGG Certification Authority",
        "valid_until": (datetime.fromisoformat(run["completed_at"].replace("Z", "+00:00")) + timedelta(days=365)).isoformat(),
    }
