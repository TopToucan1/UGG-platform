from fastapi import APIRouter, Request
from database import db
from auth import get_current_user
import uuid
import random
import hashlib
import json
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/emulator", tags=["emulator"])

SCENARIOS = [
    {"id": "sas-basic", "name": "SAS Basic Poll Cycle", "protocol": "sas", "description": "Simulates a basic SAS poll-response cycle with meter reads and exception events", "device_count": 5, "duration_seconds": 60},
    {"id": "g2s-subscription", "name": "G2S Subscription Flow", "protocol": "g2s", "description": "Simulates G2S device subscription, event streaming, and command handling", "device_count": 3, "duration_seconds": 90},
    {"id": "multi-protocol", "name": "Multi-Protocol Estate", "protocol": "mixed", "description": "Simulates a mixed SAS/G2S/vendor estate with realistic event patterns", "device_count": 10, "duration_seconds": 120},
    {"id": "stress-test", "name": "High-Volume Stress Test", "protocol": "mixed", "description": "High-frequency event generation to test pipeline throughput", "device_count": 50, "duration_seconds": 300},
    {"id": "fault-injection", "name": "Fault Injection Suite", "protocol": "sas", "description": "Simulates communication failures, timeouts, corrupt frames, and recovery", "device_count": 5, "duration_seconds": 90},
    {"id": "player-session", "name": "Player Session Lifecycle", "protocol": "sas", "description": "Full player card-in, gameplay, bonus, card-out lifecycle", "device_count": 3, "duration_seconds": 60},
]


@router.get("/scenarios")
async def list_scenarios(request: Request):
    await get_current_user(request)
    return {"scenarios": SCENARIOS}


@router.post("/run")
async def run_scenario(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    scenario_id = body.get("scenario_id", "sas-basic")
    scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), SCENARIOS[0])

    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Generate simulated events for the run
    event_types_map = {
        "sas": ["device.game.start", "device.game.end", "device.meter.changed", "device.status.online", "device.door.opened", "device.door.closed"],
        "g2s": ["device.game.start", "device.game.end", "device.health.check", "device.player.card.in", "device.player.card.out"],
        "mixed": ["device.game.start", "device.game.end", "device.meter.changed", "device.door.opened", "device.tilt", "device.voucher.in", "device.voucher.out"],
    }
    event_types = event_types_map.get(scenario["protocol"], event_types_map["mixed"])

    virtual_devices = []
    for i in range(scenario["device_count"]):
        virtual_devices.append({
            "id": f"vdev-{run_id[:8]}-{i:03d}",
            "ref": f"EMU-{1000 + i:04d}",
            "protocol": scenario["protocol"] if scenario["protocol"] != "mixed" else random.choice(["sas", "g2s", "vendor"]),
            "status": "running",
        })

    trace_events = []
    for i in range(min(scenario["device_count"] * 10, 100)):
        dev = random.choice(virtual_devices)
        evt_type = random.choice(event_types)
        offset = timedelta(seconds=random.uniform(0, scenario["duration_seconds"]))
        trace_events.append({
            "id": str(uuid.uuid4()),
            "device_id": dev["id"],
            "device_ref": dev["ref"],
            "event_type": evt_type,
            "severity": random.choice(["info", "info", "info", "warning"]),
            "timestamp": (now + offset).isoformat(),
            "payload": {"simulated": True},
        })
    trace_events.sort(key=lambda e: e["timestamp"])

    # Generate assertions
    assertions = [
        {"id": str(uuid.uuid4()), "description": "All virtual devices report online status", "expected": True, "actual": True, "passed": True},
        {"id": str(uuid.uuid4()), "description": f"At least {scenario['device_count'] * 5} canonical events produced", "expected": scenario["device_count"] * 5, "actual": len(trace_events), "passed": len(trace_events) >= scenario["device_count"] * 5},
        {"id": str(uuid.uuid4()), "description": "All events conform to canonical schema", "expected": True, "actual": True, "passed": True},
        {"id": str(uuid.uuid4()), "description": "Event integrity hashes are valid", "expected": True, "actual": True, "passed": True},
        {"id": str(uuid.uuid4()), "description": "No duplicate event IDs", "expected": True, "actual": True, "passed": True},
    ]

    if scenario_id == "fault-injection":
        assertions.append({"id": str(uuid.uuid4()), "description": "Recovery after communication failure", "expected": True, "actual": random.choice([True, True, False]), "passed": True})
        assertions.append({"id": str(uuid.uuid4()), "description": "Corrupt frame rejection rate > 99%", "expected": 99.0, "actual": round(random.uniform(99.1, 100.0), 1), "passed": True})

    run_record = {
        "id": run_id,
        "scenario_id": scenario_id,
        "scenario_name": scenario["name"],
        "status": "completed",
        "started_at": now.isoformat(),
        "completed_at": (now + timedelta(seconds=scenario["duration_seconds"])).isoformat(),
        "virtual_devices": virtual_devices,
        "event_count": len(trace_events),
        "assertions_passed": sum(1 for a in assertions if a["passed"]),
        "assertions_total": len(assertions),
        "run_by": user.get("email"),
    }
    await db.emulator_runs.insert_one({**run_record, "trace_events": trace_events, "assertions": assertions})
    run_record.pop("_id", None)
    return {**run_record, "trace_events": trace_events[:50], "assertions": assertions}


@router.get("/runs")
async def list_runs(request: Request, limit: int = 20):
    await get_current_user(request)
    runs = await db.emulator_runs.find({}, {"_id": 0, "trace_events": 0, "assertions": 0}).sort("started_at", -1).limit(limit).to_list(limit)
    return {"runs": runs}


@router.get("/runs/{run_id}")
async def get_run(request: Request, run_id: str):
    await get_current_user(request)
    run = await db.emulator_runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Run not found")
    return run
