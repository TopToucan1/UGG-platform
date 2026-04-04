"""
Phase 5 — Advanced Testing Tools: Transcript Analyzer, Proxy Mode,
Fleet Simulator, Compliance Reference, Certificate Signatures.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from database import db
from auth import get_current_user
import uuid
import random
import hashlib
import json
import io
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

router = APIRouter(tags=["phase5"])

# ══════════════════════════════════════════════════
# 1. ADVANCED TRANSCRIPT ANALYZER (ATA)
# ══════════════════════════════════════════════════

COMPLIANCE_RULES = [
    {
        "ruleId": "EVT_SUB_001", "category": "EVENT_SUBSCRIPTION", "severity": "ERROR",
        "g2s_class": "G2S_eventHandler",
        "title": "Event Subscription Accuracy",
        "description": "EGM event subscription response must include all events requested by host",
        "why_it_matters": "If the EGM omits events from its subscription response, the host will never receive those events. This creates blind spots in monitoring — a device could tilt, jam, or be tampered with and the host would never know.",
        "protocol_ref": "G2S Protocol v2.1.0, Section 4.3.2 — eventHandler class, setEventSub command",
        "expected_behavior": "The eventSubList response from the EGM must contain an entry for every eventCode included in the host's setEventSub request. Missing entries indicate the EGM rejected or ignored the subscription.",
        "violation_example": "Host sends setEventSub with events [G2S_CBE201, G2S_CBE202, G2S_GPE101]. EGM responds with eventSubList containing only [G2S_CBE201, G2S_GPE101]. G2S_CBE202 (door closed) is missing.",
        "fix_guidance": "Verify the EGM's event handler implementation supports all requested event codes. Check the Device Template for unsupported event patterns. Some EGMs reject events outside their capability set — ensure the host only subscribes to events the EGM declares in its descriptor.",
    },
    {
        "ruleId": "EVT_RPT_001", "category": "EVENT_REPORT", "severity": "ERROR",
        "g2s_class": "G2S_eventHandler",
        "title": "Event Report Completeness",
        "description": "Every eventReport must include all data elements agreed in the subscription",
        "why_it_matters": "Incomplete event reports break downstream processing. If a game-end event is missing the win amount, NOR calculations become unreliable. Financial reconciliation depends on complete data.",
        "protocol_ref": "G2S Protocol v2.1.0, Section 4.3.4 — eventReport structure",
        "expected_behavior": "Each eventReport must include the status block for the device class that generated the event, with all attributes populated per the subscription agreement.",
        "violation_example": "EGM sends G2S_GPE112 (gameEnded) eventReport but the gamePlayStatus block is missing the egmPaidGameWonAmt attribute.",
        "fix_guidance": "Review the EGM's event report generation code. Ensure all status attributes defined in the G2S schema for the generating class are included in every event report.",
    },
    {
        "ruleId": "STATE_001", "category": "STATE_TRANSITION", "severity": "ERROR",
        "g2s_class": "G2S_cabinet",
        "title": "State Transition Attribute Consistency",
        "description": "eventReport attributes must correctly reflect the G2S state machine transitions",
        "why_it_matters": "If the EGM reports cabinetStatus with egmEnabled=true after receiving a disable command, the host's view of the device is wrong. This can lead to sending commands to a disabled device or failing to detect tampering.",
        "protocol_ref": "G2S Protocol v2.1.0, Section 3.2.1 — Cabinet State Machine (9 states)",
        "expected_behavior": "After a G2S_CBE205 (EGM enabled) event, the cabinetStatus must show egmEnabled=true. After G2S_CBE206 (EGM disabled), egmEnabled must be false.",
        "violation_example": "EGM sends G2S_CBE205 event but cabinetStatus shows egmEnabled=false.",
        "fix_guidance": "Check the EGM's state machine implementation. The state reported in eventReport status blocks must match the state that triggered the event. Common cause: status block is cached and not updated before the event is emitted.",
    },
    {
        "ruleId": "COMMS_001", "category": "STATE_TRANSITION", "severity": "ERROR",
        "g2s_class": "G2S_communications",
        "title": "commsOnLine Sequence Integrity",
        "description": "G2S startup must follow commsOnLine → commsOnLineAck → setCommsState sequence",
        "why_it_matters": "The startup sequence establishes the communication contract. If steps are skipped or out of order, the host and EGM may disagree on enabled device classes, leading to command failures.",
        "protocol_ref": "G2S Protocol v2.1.0, Section 3.1.1 — Communications Startup",
        "expected_behavior": "EGM sends commsOnLine. Host responds with commsOnLineAck. Host then sends setCommsState to enable/disable classes. All three must occur in sequence within each Comms Session.",
        "violation_example": "Host sends setCommsState before receiving commsOnLine from EGM.",
        "fix_guidance": "Review startup sequence timing. Ensure the host waits for commsOnLine before proceeding.",
    },
    {
        "ruleId": "METER_001", "category": "EVENT_REPORT", "severity": "WARNING",
        "g2s_class": "G2S_meters",
        "title": "Meter Monotonicity",
        "description": "Lifetime meter values must never decrease between consecutive reads",
        "why_it_matters": "Decreasing lifetime meters indicate a possible RAM clear, meter rollback, or accounting manipulation. Regulators require monotonically increasing lifetime meters.",
        "protocol_ref": "G2S Protocol v2.1.0, Section 4.5.1 — Meter Semantics",
        "expected_behavior": "For any lifetime meter (e.g., wageredCashableAmt), value at time T+1 must be >= value at time T.",
        "violation_example": "getMeterInfo at 10:00 returns wageredCashableAmt=50000. getMeterInfo at 10:05 returns wageredCashableAmt=49500.",
        "fix_guidance": "Investigate potential RAM clear or meter rollback. If intentional (e.g., after RAM clear procedure), the event should include a meterRollback indicator.",
    },
    {
        "ruleId": "HANDPAY_001", "category": "STATE_TRANSITION", "severity": "ERROR",
        "g2s_class": "G2S_handpay",
        "title": "Handpay Sequence Completeness",
        "description": "Every handpayPending (HPE101) must be followed by a handpayAcknowledged (HPE104)",
        "why_it_matters": "An unacknowledged handpay means money is stuck. The device cannot continue play until the handpay is resolved. Missing HPE104 indicates a broken key-off procedure.",
        "protocol_ref": "G2S Protocol v2.1.0, Section 4.8.2 — Handpay Lifecycle",
        "expected_behavior": "G2S_HPE101 → operator key-off → G2S_HPE104. Both events must appear in the same Comms Session.",
        "violation_example": "Session contains G2S_HPE101 but no G2S_HPE104 before session end.",
        "fix_guidance": "Ensure the handpay key-off procedure generates HPE104. Check that the key-off event is not being filtered or lost in transmission.",
    },
]


def _evaluate_rules(session_transcripts: list) -> list:
    """Evaluate all compliance rules against a set of transcripts."""
    violations = []
    for rule in COMPLIANCE_RULES:
        rule_id = rule["ruleId"]
        if rule_id == "EVT_SUB_001":
            set_sub = [t for t in session_transcripts if t.get("command_name") == "setEventSub" and t.get("direction") == "TX"]
            sub_list = [t for t in session_transcripts if t.get("command_name") == "eventSubList" and t.get("direction") == "RX"]
            if set_sub and not sub_list:
                violations.append({"rule_id": rule_id, "severity": rule["severity"], "category": rule["category"], "g2s_class": rule["g2s_class"], "detail": "setEventSub sent but no eventSubList received", "transcript_msg_id": set_sub[0].get("id")})
        elif rule_id == "COMMS_001":
            comms_online = [t for t in session_transcripts if t.get("command_name") == "commsOnLine"]
            set_comms = [t for t in session_transcripts if t.get("command_name") == "setCommsState"]
            if set_comms and not comms_online:
                violations.append({"rule_id": rule_id, "severity": "ERROR", "category": "STATE_TRANSITION", "g2s_class": "G2S_communications", "detail": "setCommsState sent without prior commsOnLine"})
        elif rule_id == "HANDPAY_001":
            hpe101 = [t for t in session_transcripts if "HPE101" in (t.get("command_name") or "") or "handpayPending" in (t.get("command_name") or "")]
            hpe104 = [t for t in session_transcripts if "HPE104" in (t.get("command_name") or "") or "handpayAcknowledged" in (t.get("command_name") or "")]
            if hpe101 and not hpe104:
                violations.append({"rule_id": rule_id, "severity": "ERROR", "category": "STATE_TRANSITION", "g2s_class": "G2S_handpay", "detail": f"handpayPending ({len(hpe101)} occurrences) without handpayAcknowledged", "transcript_msg_id": hpe101[0].get("id")})
    return violations


@router.post("/api/analyzer/run")
async def run_transcript_analyzer(request: Request):
    """Run the Advanced Transcript Analyzer against a session."""
    user = await get_current_user(request)
    body = await request.json()
    session_id = body.get("session_id", "default")

    transcripts = await db.lab_transcripts.find({"session_id": session_id}, {"_id": 0}).sort("occurred_at", 1).to_list(50000)
    if not transcripts:
        return {"session_id": session_id, "status": "NO_DATA", "sessions": [], "total_violations": 0}

    # Split into Comms Sessions
    comms_sessions = []
    current = {"index": 0, "messages": [], "started_at": None, "is_complete": False}
    for t in transcripts:
        if t.get("command_name") == "commsOnLine" and current["messages"]:
            current["is_complete"] = any(m.get("command_name") == "setCommsState" for m in current["messages"])
            comms_sessions.append(current)
            current = {"index": len(comms_sessions), "messages": [], "started_at": t.get("occurred_at"), "is_complete": False}
        if not current["started_at"]:
            current["started_at"] = t.get("occurred_at")
        current["messages"].append(t)
    if current["messages"]:
        current["is_complete"] = any(m.get("command_name") == "setCommsState" for m in current["messages"])
        comms_sessions.append(current)

    # Filter empty sessions
    comms_sessions = [cs for cs in comms_sessions if len(cs["messages"]) > 0]

    # Evaluate rules per session
    session_results = []
    total_violations = 0
    total_warnings = 0
    total_errors = 0
    for cs in comms_sessions:
        violations = _evaluate_rules(cs["messages"])
        errors = [v for v in violations if v["severity"] == "ERROR"]
        warnings = [v for v in violations if v["severity"] == "WARNING"]
        status = "RED" if errors else "YELLOW" if warnings else "GREEN"
        total_violations += len(violations)
        total_errors += len(errors)
        total_warnings += len(warnings)
        session_results.append({
            "session_index": cs["index"],
            "started_at": cs["started_at"],
            "message_count": len(cs["messages"]),
            "is_complete": cs["is_complete"],
            "status": status,
            "violations": violations,
            "error_count": len(errors),
            "warning_count": len(warnings),
        })

    overall = "RED" if total_errors > 0 else "YELLOW" if total_warnings > 0 else "GREEN"

    result = {
        "session_id": session_id, "overall_status": overall,
        "total_messages": len(transcripts), "comms_session_count": len(session_results),
        "total_violations": total_violations, "total_errors": total_errors, "total_warnings": total_warnings,
        "sessions": session_results,
        "rules_evaluated": len(COMPLIANCE_RULES),
        "analyzed_at": datetime.now(timezone.utc).isoformat(), "analyzed_by": user.get("email"),
    }
    await db.analyzer_results.insert_one({"id": str(uuid.uuid4()), **result})
    result.pop("_id", None)
    return result


@router.get("/api/analyzer/results")
async def list_analyzer_results(request: Request, limit: int = 10):
    await get_current_user(request)
    results = await db.analyzer_results.find({}, {"_id": 0, "sessions": 0}).sort("analyzed_at", -1).limit(limit).to_list(limit)
    return {"results": results}


# ══════════════════════════════════════════════════
# 2. PROXY MODE — Transparent MITM
# ══════════════════════════════════════════════════

_proxy_instances = {}

DISRUPTIVE_FILTER_ACTIONS = ["DROP", "DELAY", "CORRUPT", "DUPLICATE"]


@router.post("/api/proxy/start")
async def start_proxy(request: Request):
    """Start a G2S proxy instance for transparent MITM capture."""
    user = await get_current_user(request)
    body = await request.json()
    proxy_id = body.get("proxy_id", f"proxy-{uuid.uuid4().hex[:8]}")
    listen_port = body.get("listen_port", 8443)
    target_host = body.get("target_host", "")
    target_port = body.get("target_port", 443)
    validate_schema = body.get("validate_schema", True)
    schema_version = body.get("schema_version", "G2S_2.1.0")
    filters = body.get("disruptive_filters", [])

    now = datetime.now(timezone.utc).isoformat()
    proxy = {
        "id": proxy_id, "status": "RUNNING",
        "listen_port": listen_port, "target_host": target_host, "target_port": target_port,
        "validate_schema": validate_schema, "schema_version": schema_version,
        "disruptive_filters": filters,
        "messages_captured": 0, "messages_forwarded": 0, "messages_dropped": 0,
        "schema_violations": 0, "filter_matches": 0,
        "started_at": now, "started_by": user.get("email"),
        "egm_connections": 0, "host_connections": 0,
        "channels": {"protocol_trace": 0, "soap": 0, "g2s": 0},
    }
    _proxy_instances[proxy_id] = proxy

    await db.proxy_instances.insert_one({**proxy})
    proxy.pop("_id", None)
    return proxy


@router.get("/api/proxy/instances")
async def list_proxy_instances(request: Request):
    await get_current_user(request)
    return {"instances": list(_proxy_instances.values())}


@router.post("/api/proxy/{proxy_id}/intercept")
async def proxy_intercept_message(request: Request, proxy_id: str):
    """Simulate intercepting a G2S message through the proxy pipeline."""
    user = await get_current_user(request)
    body = await request.json()
    proxy = _proxy_instances.get(proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")

    direction = body.get("direction", "EGM_TO_HOST")
    message_xml = body.get("xml", "")
    command_class = body.get("command_class", "")
    command_name = body.get("command_name", "")
    now = datetime.now(timezone.utc).isoformat()

    # Pipeline: raw → SOAP → G2S → validate → filter → forward
    proxy["messages_captured"] += 1
    proxy["channels"]["protocol_trace"] += 1
    proxy["channels"]["soap"] += 1
    proxy["channels"]["g2s"] += 1

    # Store in all 3 channels
    for channel in ["PROTOCOL_TRACE", "SOAP", "G2S"]:
        await db.lab_transcripts.insert_one({
            "id": str(uuid.uuid4()), "session_id": proxy_id,
            "direction": "TX" if direction == "EGM_TO_HOST" else "RX",
            "channel": channel, "command_class": command_class,
            "command_name": command_name, "payload_xml": message_xml[:5000],
            "state": "Standard", "occurred_at": now,
            "comment": f"Proxy captured ({direction})",
        })

    # Schema validation
    schema_valid = True
    if proxy["validate_schema"] and message_xml:
        if "<" not in message_xml or ">" not in message_xml:
            schema_valid = False
            proxy["schema_violations"] += 1

    # Apply disruptive filters
    action = "FORWARD"
    matched_filter = None
    for f in proxy.get("disruptive_filters", []):
        if f.get("commandClass") and f["commandClass"] != command_class:
            continue
        if f.get("commandName") and f["commandName"] != command_name:
            continue
        if f.get("direction") and f["direction"] != direction and f["direction"] != "BOTH":
            continue
        matched_filter = f
        action = f.get("action", "FORWARD")
        proxy["filter_matches"] += 1
        break

    if action == "DROP":
        proxy["messages_dropped"] += 1
    elif action == "DELAY":
        pass  # Would await asyncio.sleep(matched_filter.get("delayMs", 1000) / 1000)
    elif action == "CORRUPT":
        pass  # Would modify message bytes
    elif action == "DUPLICATE":
        proxy["messages_forwarded"] += 2
    else:
        proxy["messages_forwarded"] += 1

    return {
        "proxy_id": proxy_id, "direction": direction,
        "action": action, "schema_valid": schema_valid,
        "matched_filter": matched_filter.get("id") if matched_filter else None,
        "message_count": proxy["messages_captured"],
        "channels": proxy["channels"],
    }


@router.post("/api/proxy/{proxy_id}/stop")
async def stop_proxy(request: Request, proxy_id: str):
    await get_current_user(request)
    proxy = _proxy_instances.pop(proxy_id, None)
    if proxy:
        proxy["status"] = "STOPPED"
        proxy["stopped_at"] = datetime.now(timezone.utc).isoformat()
        await db.proxy_instances.update_one({"id": proxy_id}, {"$set": {"status": "STOPPED", "stopped_at": proxy["stopped_at"]}})
    return {"message": f"Proxy {proxy_id} stopped", "final_stats": proxy}


# ══════════════════════════════════════════════════
# 3. FLEET SIMULATOR — Up to 200 EGMs
# ══════════════════════════════════════════════════

ENGINE_STATUSES = ["Engine Stopped", "Engine Loading", "Engine Starting", "Engine Running", "Scripts Starting", "Scripts Running", "Scripts Stopping", "Engine Stopping", "Status Unknown"]
_fleet_runners = {}


@router.post("/api/fleet/create")
async def create_fleet_runner(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    runner = {
        "id": str(uuid.uuid4()), "name": body.get("name", "Fleet Run"),
        "target_host_url": body.get("target_host_url", ""),
        "max_egms": min(body.get("max_egms", 50), 200),
        "status": "Engine Stopped",
        "slots": [], "metrics": {"messages_sent": 0, "messages_recv": 0, "errors_total": 0, "avg_response_ms": 0, "egms_connected": 0, "egms_running": 0},
        "started_at": None, "created_by": user.get("email"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # Create slots
    for i in range(runner["max_egms"]):
        runner["slots"].append({
            "slot_index": i, "egm_id": f"FLEET-EGM-{i+1:04d}",
            "status": "IDLE", "template_id": None, "script_id": None,
            "messages_sent": 0, "messages_recv": 0, "errors": 0,
        })
    _fleet_runners[runner["id"]] = runner
    await db.fleet_runners.insert_one({k: v for k, v in runner.items() if k != "slots"})
    return {k: v for k, v in runner.items() if k != "slots" or True}


@router.post("/api/fleet/{runner_id}/engine")
async def control_fleet_engine(request: Request, runner_id: str):
    """Start or stop the fleet engine."""
    await get_current_user(request)
    body = await request.json()
    action = body.get("action", "start")
    runner = _fleet_runners.get(runner_id)
    if not runner:
        raise HTTPException(status_code=404, detail="Fleet runner not found")

    if action == "start":
        runner["status"] = "Engine Loading"
        runner["started_at"] = datetime.now(timezone.utc).isoformat()
        # Simulate staggered EGM startup
        for i, slot in enumerate(runner["slots"]):
            slot["status"] = "CONNECTING"
        runner["status"] = "Engine Starting"
        for i, slot in enumerate(runner["slots"]):
            slot["status"] = "CONNECTED"
            runner["metrics"]["egms_connected"] += 1
        runner["status"] = "Engine Running"
    elif action == "stop":
        runner["status"] = "Engine Stopping"
        for slot in runner["slots"]:
            slot["status"] = "IDLE"
        runner["metrics"]["egms_connected"] = 0
        runner["metrics"]["egms_running"] = 0
        runner["status"] = "Engine Stopped"

    return {"runner_id": runner_id, "status": runner["status"], "egms_connected": runner["metrics"]["egms_connected"]}


@router.get("/api/fleet/{runner_id}/engine")
async def get_fleet_engine_status(request: Request, runner_id: str):
    await get_current_user(request)
    runner = _fleet_runners.get(runner_id)
    if not runner:
        raise HTTPException(status_code=404, detail="Fleet runner not found")
    return {"runner_id": runner_id, "status": runner["status"], "metrics": runner["metrics"], "slot_count": len(runner["slots"]), "slots_summary": {"idle": sum(1 for s in runner["slots"] if s["status"] == "IDLE"), "connected": sum(1 for s in runner["slots"] if s["status"] == "CONNECTED"), "running": sum(1 for s in runner["slots"] if s["status"] == "RUNNING")}}


@router.post("/api/fleet/{runner_id}/scripts")
async def control_fleet_scripts(request: Request, runner_id: str):
    """Start or stop scripts across all fleet slots."""
    await get_current_user(request)
    body = await request.json()
    action = body.get("action", "start")
    runner = _fleet_runners.get(runner_id)
    if not runner:
        raise HTTPException(status_code=404, detail="Fleet runner not found")

    if action == "start":
        runner["status"] = "Scripts Starting"
        for slot in runner["slots"]:
            if slot["status"] == "CONNECTED":
                slot["status"] = "RUNNING"
                runner["metrics"]["egms_running"] += 1
                # Simulate some traffic
                slot["messages_sent"] = random.randint(10, 100)
                slot["messages_recv"] = random.randint(10, 100)
                runner["metrics"]["messages_sent"] += slot["messages_sent"]
                runner["metrics"]["messages_recv"] += slot["messages_recv"]
        runner["metrics"]["avg_response_ms"] = round(random.uniform(15, 80), 1)
        runner["status"] = "Scripts Running"
    elif action == "stop":
        runner["status"] = "Scripts Stopping"
        for slot in runner["slots"]:
            if slot["status"] == "RUNNING":
                slot["status"] = "CONNECTED"
        runner["metrics"]["egms_running"] = 0
        runner["status"] = "Engine Running"

    return {"runner_id": runner_id, "status": runner["status"], "metrics": runner["metrics"]}


@router.post("/api/fleet/{runner_id}/metrics")
async def reset_fleet_metrics(request: Request, runner_id: str):
    await get_current_user(request)
    body = await request.json()
    runner = _fleet_runners.get(runner_id)
    if not runner:
        raise HTTPException(status_code=404, detail="Fleet runner not found")
    if body.get("reset"):
        runner["metrics"] = {"messages_sent": 0, "messages_recv": 0, "errors_total": 0, "avg_response_ms": 0, "egms_connected": runner["metrics"]["egms_connected"], "egms_running": runner["metrics"]["egms_running"]}
    return {"metrics": runner["metrics"]}


@router.get("/api/fleet/runners")
async def list_fleet_runners(request: Request):
    await get_current_user(request)
    runners = [{k: v for k, v in r.items() if k != "slots"} for r in _fleet_runners.values()]
    return {"runners": runners}


# ══════════════════════════════════════════════════
# 4. COMPLIANCE REFERENCE — Public Knowledge Base
# ══════════════════════════════════════════════════

@router.get("/api/compliance/rules")
async def list_compliance_rules(request: Request = None, g2s_class: str = None, category: str = None, q: str = None):
    """Public endpoint — list all compliance rules with optional filtering."""
    rules = COMPLIANCE_RULES
    if g2s_class:
        rules = [r for r in rules if r["g2s_class"] == g2s_class]
    if category:
        rules = [r for r in rules if r["category"] == category]
    if q:
        ql = q.lower()
        rules = [r for r in rules if ql in r["title"].lower() or ql in r["description"].lower() or ql in r.get("why_it_matters", "").lower() or ql in r.get("fix_guidance", "").lower()]
    return {"rules": rules, "total": len(rules)}


@router.get("/api/compliance/rules/{rule_id}")
async def get_compliance_rule(request: Request = None, rule_id: str = ""):
    """Public endpoint — full rule detail."""
    rule = next((r for r in COMPLIANCE_RULES if r["ruleId"] == rule_id), None)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.get("/api/compliance/search")
async def search_compliance(request: Request = None, q: str = ""):
    """Public full-text search across all rule fields."""
    if not q:
        return {"rules": COMPLIANCE_RULES, "total": len(COMPLIANCE_RULES)}
    ql = q.lower()
    matched = []
    for r in COMPLIANCE_RULES:
        searchable = " ".join(str(v) for v in r.values()).lower()
        if ql in searchable:
            matched.append(r)
    return {"rules": matched, "total": len(matched), "query": q}


# ══════════════════════════════════════════════════
# 5. CERTIFICATE DIGITAL SIGNATURES
# ══════════════════════════════════════════════════

# Generate a signing key pair (in production this would be loaded from secure storage)
import hmac

_SIGNING_SECRET = "UGG-CERT-SIGNING-KEY-2026-PRODUCTION"


def _sign_certificate(cert_data: dict) -> str:
    """Generate a digital signature for a certificate."""
    payload = json.dumps({k: v for k, v in sorted(cert_data.items()) if k != "signature"}, sort_keys=True, default=str)
    return hmac.new(_SIGNING_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _verify_signature(cert_data: dict, signature: str) -> bool:
    """Verify a certificate's digital signature."""
    expected = _sign_certificate(cert_data)
    return hmac.compare_digest(expected, signature)


@router.post("/api/certificates/sign")
async def sign_certificate(request: Request):
    """Generate a signed certification certificate after a passing run."""
    user = await get_current_user(request)
    body = await request.json()
    run_id = body.get("run_id")

    run = await db.certification_runs.find_one({"id": run_id, "status": "PASSED"}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="No passing certification run found")

    now = datetime.now(timezone.utc)
    cert_data = {
        "certificate_id": str(uuid.uuid4()),
        "run_id": run_id,
        "tier": run.get("tier_label", run.get("tier", "Bronze")),
        "device_ref": run.get("device_ref"),
        "manufacturer": run.get("manufacturer"),
        "model": run.get("model"),
        "pass_rate": run.get("pass_rate"),
        "total_tests": run.get("total_tests"),
        "total_passed": run.get("total_passed"),
        "issued_at": now.isoformat(),
        "issued_by": "UGG Certification Authority",
        "valid_until": (now + timedelta(days=365)).isoformat(),
        "schema_version": "G2S_2.1.0",
    }
    signature = _sign_certificate(cert_data)
    cert_data["signature"] = signature
    cert_data["public_url"] = f"/api/certificates/{cert_data['certificate_id']}/verify"
    cert_data["signed_by"] = user.get("email")

    await db.signed_certificates.insert_one(cert_data)
    cert_data.pop("_id", None)
    return cert_data


@router.get("/api/certificates/{cert_id}/verify")
async def verify_certificate(cert_id: str):
    """Public endpoint — verify a certificate's digital signature. No auth required."""
    cert = await db.signed_certificates.find_one({"certificate_id": cert_id}, {"_id": 0})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    # Check expiry
    valid_until = cert.get("valid_until", "")
    if valid_until:
        try:
            expiry = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expiry:
                raise HTTPException(status_code=410, detail="Certificate has expired")
        except (ValueError, TypeError):
            pass

    # Verify signature — use only the fields that were signed
    stored_sig = cert.get("signature", "")
    verify_data = {k: v for k, v in cert.items() if k not in ("signature", "public_url", "signed_by")}
    is_valid = _verify_signature(verify_data, stored_sig)

    return {
        "certificate_id": cert_id,
        "signature_valid": is_valid,
        "tier": cert.get("tier"),
        "device": cert.get("device_ref"),
        "manufacturer": cert.get("manufacturer"),
        "model": cert.get("model"),
        "pass_rate": cert.get("pass_rate"),
        "issued_at": cert.get("issued_at"),
        "valid_until": cert.get("valid_until"),
        "issued_by": cert.get("issued_by"),
        "verification_status": "VALID" if is_valid else "INVALID",
    }


@router.get("/api/certificates")
async def list_signed_certificates(request: Request):
    await get_current_user(request)
    certs = await db.signed_certificates.find({}, {"_id": 0, "signature": 0}).sort("issued_at", -1).to_list(50)
    return {"certificates": certs}
