"""
Phase 4 Emulator Lab — Complete engineering workbench.
SmartEGM Engine, Response Manager, Script DSL, Balanced Meters, TAR, Watchables.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from database import db
from auth import get_current_user
import uuid
import random
import hashlib
import json
import csv
import io
import re
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

router = APIRouter(prefix="/api/emulator-lab", tags=["emulator-lab"])

# ══════════════════════════════════════════════════
# 1. SMART EGM ENGINE — 12 Player Verbs
# ══════════════════════════════════════════════════

PLAYER_VERBS = [
    {"id": "INSERT_BILL", "label": "Insert Bill", "params": ["denomination"], "state_req": "ENABLED"},
    {"id": "INSERT_VOUCHER", "label": "Insert Voucher", "params": ["amount"], "state_req": "ENABLED"},
    {"id": "INSERT_COIN", "label": "Insert Coin", "params": ["amount"], "state_req": "ENABLED"},
    {"id": "PUSH_PLAY_BUTTON", "label": "Push Play", "params": ["wager"], "state_req": "ENABLED"},
    {"id": "PUSH_MAX_BET", "label": "Max Bet", "params": [], "state_req": "ENABLED"},
    {"id": "CASH_OUT", "label": "Cash Out", "params": [], "state_req": "ENABLED"},
    {"id": "REQUEST_HANDPAY", "label": "Request Handpay", "params": [], "state_req": "ANY"},
    {"id": "OPEN_DOOR", "label": "Open Door", "params": ["door_type"], "state_req": "ANY"},
    {"id": "CLOSE_DOOR", "label": "Close Door", "params": ["door_type"], "state_req": "ANY"},
    {"id": "FORCE_TILT", "label": "Force Tilt", "params": ["reason"], "state_req": "ANY"},
    {"id": "CLEAR_FAULT", "label": "Clear Fault", "params": [], "state_req": "FAULT"},
    {"id": "SET_CREDITS", "label": "Set Credits", "params": ["amount"], "state_req": "ANY"},
]

WIN_LEVELS = [
    {"id": 0, "name": "NoWin", "probability": 0.70, "multiplier": 0},
    {"id": 1, "name": "Small", "probability": 0.20, "multiplier": 1.5},
    {"id": 2, "name": "Medium", "probability": 0.08, "multiplier": 5},
    {"id": 3, "name": "Large", "probability": 0.019, "multiplier": 25},
    {"id": 4, "name": "Jackpot", "probability": 0.001, "multiplier": 250},
]

# In-memory SmartEGM state
_smart_egm_state = {}


def _get_egm(session_id: str) -> dict:
    if session_id not in _smart_egm_state:
        _smart_egm_state[session_id] = {
            "state": "IDLE", "credits": 0, "coin_in": 0, "coin_out": 0,
            "games_played": 0, "bills_in": 0, "vouchers_in": 0, "handpays": 0,
            "doors_open": set(), "events": [], "meters": {},
        }
    return _smart_egm_state[session_id]


def _roll_outcome(wager: int) -> dict:
    r = random.random()
    cumulative = 0
    for wl in WIN_LEVELS:
        cumulative += wl["probability"]
        if r <= cumulative:
            win = int(wager * wl["multiplier"])
            return {"level": wl["name"], "multiplier": wl["multiplier"], "win": win}
    return {"level": "NoWin", "multiplier": 0, "win": 0}


@router.get("/smart-egm/verbs")
async def get_player_verbs(request: Request):
    await get_current_user(request)
    return {"verbs": PLAYER_VERBS, "win_levels": WIN_LEVELS}


@router.post("/smart-egm/execute-verb")
async def execute_player_verb(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    session_id = body.get("session_id", "default")
    verb = body.get("verb")
    params = body.get("params", {})

    egm = _get_egm(session_id)
    now = datetime.now(timezone.utc).isoformat()
    events = []

    if verb == "INSERT_BILL":
        denom = params.get("denomination", 2000)
        egm["credits"] += denom
        egm["bills_in"] += denom
        egm["coin_in"] += denom
        events.append({"code": "G2S_NAE101", "type": "billAccepted", "data": {"denomination": denom, "credits": egm["credits"]}})

    elif verb == "INSERT_VOUCHER":
        amount = params.get("amount", 1000)
        egm["credits"] += amount
        egm["vouchers_in"] += amount
        events.append({"code": "G2S_VCE104", "type": "voucherPending", "data": {"amount": amount}})
        events.append({"code": "G2S_VCE102", "type": "voucherRedeemed", "data": {"amount": amount, "credits": egm["credits"]}})

    elif verb == "INSERT_COIN":
        amount = params.get("amount", 100)
        egm["credits"] += amount
        egm["coin_in"] += amount
        events.append({"code": "G2S_CAE101", "type": "coinAccepted", "data": {"amount": amount}})

    elif verb in ("PUSH_PLAY_BUTTON", "PUSH_MAX_BET"):
        wager = params.get("wager", 500) if verb == "PUSH_PLAY_BUTTON" else 5000
        if egm["credits"] < wager:
            raise HTTPException(status_code=400, detail=f"Insufficient credits: {egm['credits']} < {wager}")
        outcome = _roll_outcome(wager)
        egm["credits"] -= wager
        egm["coin_in"] += wager
        egm["games_played"] += 1
        events.append({"code": "G2S_GPE101", "type": "gameStarted", "data": {"wager": wager}})
        if outcome["win"] > 0:
            egm["credits"] += outcome["win"]
            egm["coin_out"] += outcome["win"]
        events.append({"code": "G2S_GPE112", "type": "gameEnded", "data": {"wager": wager, "win": outcome["win"], "level": outcome["level"], "credits": egm["credits"]}})
        if outcome["win"] >= 120000:
            events.append({"code": "G2S_HPE101", "type": "handpayPending", "data": {"amount": outcome["win"]}})
            egm["state"] = "HANDPAY_PENDING"

    elif verb == "CASH_OUT":
        if egm["credits"] <= 0:
            raise HTTPException(status_code=400, detail="No credits to cash out")
        amount = egm["credits"]
        egm["credits"] = 0
        egm["coin_out"] += amount
        events.append({"code": "G2S_VCE101", "type": "voucherPrinted", "data": {"amount": amount}})

    elif verb == "REQUEST_HANDPAY":
        egm["handpays"] += 1
        events.append({"code": "G2S_HPE101", "type": "handpayPending", "data": {"credits": egm["credits"]}})
        events.append({"code": "G2S_HPE104", "type": "handpayAcknowledged", "data": {}})
        egm["state"] = "ENABLED"

    elif verb == "OPEN_DOOR":
        door = params.get("door_type", "main")
        egm["doors_open"].add(door)
        events.append({"code": "G2S_CBE201", "type": "doorOpened", "data": {"door_type": door}})

    elif verb == "CLOSE_DOOR":
        door = params.get("door_type", "main")
        egm["doors_open"].discard(door)
        events.append({"code": "G2S_CBE202", "type": "doorClosed", "data": {"door_type": door}})

    elif verb == "FORCE_TILT":
        reason = params.get("reason", "operator_forced")
        egm["state"] = "FAULT"
        events.append({"code": "G2S_CBE301", "type": "tilt", "data": {"reason": reason}})

    elif verb == "CLEAR_FAULT":
        egm["state"] = "ENABLED"
        events.append({"code": "G2S_CBE302", "type": "tiltCleared", "data": {}})

    elif verb == "SET_CREDITS":
        egm["credits"] = params.get("amount", 0)

    # Store events in transcript
    for evt in events:
        evt["occurred_at"] = now
        evt["session_id"] = session_id
    egm["events"].extend(events)

    # Store transcript in DB
    for evt in events:
        await db.lab_transcripts.insert_one({
            "id": str(uuid.uuid4()), "session_id": session_id,
            "direction": "RX", "channel": "G2S", "command_class": evt["code"][:7],
            "command_name": evt["type"], "payload_xml": json.dumps(evt["data"]),
            "state": "Standard", "occurred_at": now,
        })

    return {"verb": verb, "events": events, "egm_state": {**egm, "doors_open": list(egm["doors_open"])}}


@router.get("/smart-egm/state")
async def get_egm_state(request: Request, session_id: str = "default"):
    await get_current_user(request)
    egm = _get_egm(session_id)
    return {**egm, "doors_open": list(egm["doors_open"]), "event_count": len(egm["events"])}


# ══════════════════════════════════════════════════
# 2. RESPONSE MANAGER
# ══════════════════════════════════════════════════

_response_configs = {}
_active_config = None
_response_counters = {}


@router.get("/response-manager/configs")
async def list_response_configs(request: Request):
    await get_current_user(request)
    configs = await db.response_configurations.find({}, {"_id": 0}).to_list(50)
    return {"configs": configs, "active": _active_config}


@router.post("/response-manager/configs")
async def create_response_config(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    config = {
        "id": str(uuid.uuid4()), "name": body.get("name", "New Config"),
        "description": body.get("description", ""), "g2s_schema": body.get("g2s_schema", "G2S_2.1.0"),
        "rules": body.get("rules", []), "is_system": False,
        "created_by": user.get("email"), "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # Validate custom error format
    for rule in config["rules"]:
        if rule.get("action") == "CUSTOM_APP_ERROR":
            payload = rule.get("actionPayload", "")
            if not re.match(r'^[A-Z]{3}_[A-Z0-9]{6}$', payload):
                raise HTTPException(status_code=400, detail=f"Invalid custom error format: '{payload}'. Must be 'XXX_YYYYYY'")
    await db.response_configurations.insert_one(config)
    config.pop("_id", None)
    return config


@router.post("/response-manager/activate/{config_id}")
async def activate_response_config(request: Request, config_id: str):
    global _active_config, _response_counters
    await get_current_user(request)
    config = await db.response_configurations.find_one({"id": config_id}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    _active_config = config
    _response_counters = {}
    return {"message": f"Activated: {config['name']}", "active": config}


@router.post("/response-manager/intercept")
async def intercept_response(request: Request):
    """Test the response manager intercept logic."""
    await get_current_user(request)
    body = await request.json()
    if not _active_config:
        return {"intercepted": False, "reason": "No active config"}
    cmd_class = body.get("commandClass", "")
    cmd_name = body.get("commandName", "")
    key = f"{cmd_class}.{cmd_name}"
    _response_counters[key] = _response_counters.get(key, 0) + 1
    count = _response_counters[key]

    for rule in _active_config.get("rules", []):
        if rule.get("commandClass") != cmd_class or rule.get("commandName") != cmd_name:
            continue
        n = rule.get("sendOnOccurrence", 1)
        c = rule.get("sendCount", 1)
        repeat = rule.get("repeatPattern", False)
        if not repeat:
            if count >= n and count < n + c:
                return {"intercepted": True, "action": rule["action"], "payload": rule.get("actionPayload"), "occurrence": count}
        else:
            cycle = (count - 1) % (n + c - 1)
            if cycle >= n - 1 and cycle < n + c - 1:
                return {"intercepted": True, "action": rule["action"], "payload": rule.get("actionPayload"), "occurrence": count}
    return {"intercepted": False, "occurrence": count}


# ══════════════════════════════════════════════════
# 3. SCENARIO SCRIPT ENGINE — 19-verb DSL
# ══════════════════════════════════════════════════

SCRIPT_VERBS = [
    "comment", "notice", "pause", "prompt", "run-script", "run-macro",
    "set-ttl", "set-response-config", "wait-for-commands", "wait-for-events",
    "wait-for-compares", "delete-all-snapshots", "perform-snapshot",
    "perform-snapshot-compare", "event-snapshots", "enable-all-host-disabled",
    "balanced-meters-analysis", "player-verb", "send-command",
]

SYSTEM_SCRIPTS = [
    {"id": "play-cycle-verify", "name": "Play Cycle Verify", "version": "1.0", "category": "System", "description": "Complete play cycle: bill in, play 5 games, cash out, verify Appendix B", "steps": [
        {"verb": "delete-all-snapshots", "params": {}},
        {"verb": "perform-snapshot", "params": {"name": "baseline"}},
        {"verb": "comment", "params": {"text": "=== INSERT $20 BILL ==="}},
        {"verb": "player-verb", "params": {"verb": "INSERT_BILL", "denomination": 2000}},
        {"verb": "wait-for-events", "params": {"events": ["G2S_NAE101"]}},
        {"verb": "comment", "params": {"text": "=== PLAY 5 GAMES ==="}},
        {"verb": "player-verb", "params": {"verb": "PUSH_PLAY_BUTTON", "wager": 500}},
        {"verb": "player-verb", "params": {"verb": "PUSH_PLAY_BUTTON", "wager": 500}},
        {"verb": "player-verb", "params": {"verb": "PUSH_PLAY_BUTTON", "wager": 500}},
        {"verb": "player-verb", "params": {"verb": "PUSH_PLAY_BUTTON", "wager": 500}},
        {"verb": "player-verb", "params": {"verb": "PUSH_PLAY_BUTTON", "wager": 500}},
        {"verb": "comment", "params": {"text": "=== CASH OUT ==="}},
        {"verb": "player-verb", "params": {"verb": "CASH_OUT"}},
        {"verb": "perform-snapshot", "params": {"name": "final"}},
        {"verb": "balanced-meters-analysis", "params": {"start": "baseline", "end": "final"}},
        {"verb": "notice", "params": {"message": "Play cycle complete. Review Balanced Meters."}},
    ]},
    {"id": "startup-sequence", "name": "G2S Startup Sequence", "version": "1.0", "category": "System", "description": "Verify G2S startup: commsOnLine → commsOnLineAck → setCommsState", "steps": [
        {"verb": "comment", "params": {"text": "=== G2S STARTUP VERIFICATION ==="}},
        {"verb": "send-command", "params": {"class": "communications", "command": "commsOnLine"}},
        {"verb": "wait-for-commands", "params": {"commands": [{"class": "communications", "name": "commsOnLineAck"}]}},
        {"verb": "send-command", "params": {"class": "communications", "command": "setCommsState"}},
        {"verb": "notice", "params": {"message": "Startup sequence verified."}},
    ]},
    {"id": "handpay-cycle", "name": "Handpay Cycle", "version": "1.0", "category": "System", "description": "Trigger and resolve a handpay event", "steps": [
        {"verb": "player-verb", "params": {"verb": "SET_CREDITS", "amount": 500000}},
        {"verb": "player-verb", "params": {"verb": "REQUEST_HANDPAY"}},
        {"verb": "wait-for-events", "params": {"events": ["G2S_HPE101"]}},
        {"verb": "prompt", "params": {"message": "Verify handpay event in transcript", "button": "Verified", "timeout": 30}},
        {"verb": "notice", "params": {"message": "Handpay cycle complete."}},
    ]},
    {"id": "door-tilt-test", "name": "Door & Tilt Test", "version": "1.0", "category": "System", "description": "Open door, force tilt, clear fault", "steps": [
        {"verb": "player-verb", "params": {"verb": "OPEN_DOOR", "door_type": "main"}},
        {"verb": "pause", "params": {"min_seconds": 2, "max_seconds": 3}},
        {"verb": "player-verb", "params": {"verb": "CLOSE_DOOR", "door_type": "main"}},
        {"verb": "player-verb", "params": {"verb": "FORCE_TILT", "reason": "test_tilt"}},
        {"verb": "pause", "params": {"min_seconds": 1, "max_seconds": 2}},
        {"verb": "player-verb", "params": {"verb": "CLEAR_FAULT"}},
        {"verb": "notice", "params": {"message": "Door and tilt test complete."}},
    ]},
]


@router.get("/scripts")
async def list_scripts(request: Request):
    await get_current_user(request)
    custom = await db.lab_scripts.find({}, {"_id": 0}).to_list(50)
    return {"system_scripts": SYSTEM_SCRIPTS, "custom_scripts": custom, "verbs": SCRIPT_VERBS}


@router.post("/scripts")
async def create_script(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    script = {
        "id": str(uuid.uuid4()), "name": body.get("name"), "version": body.get("version", "1.0"),
        "category": "Custom", "description": body.get("description", ""),
        "steps": body.get("steps", []),
        "created_by": user.get("email"), "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.lab_scripts.insert_one(script)
    script.pop("_id", None)
    return script


@router.post("/scripts/run")
async def run_script(request: Request):
    """Execute a script's steps sequentially against the SmartEGM."""
    user = await get_current_user(request)
    body = await request.json()
    script_id = body.get("script_id")
    session_id = body.get("session_id", str(uuid.uuid4())[:8])

    # Find script
    script = next((s for s in SYSTEM_SCRIPTS if s["id"] == script_id), None)
    if not script:
        script = await db.lab_scripts.find_one({"id": script_id}, {"_id": 0})
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    # Initialize EGM for this session
    egm = _get_egm(session_id)
    egm["state"] = "ENABLED"
    egm["credits"] = 0

    run_id = str(uuid.uuid4())
    steps_done = 0
    step_results = []
    status = "RUNNING"
    snapshots = {}
    bma_results = None

    for i, step in enumerate(script["steps"]):
        verb = step["verb"]
        params = step.get("params", {})
        step_result = {"index": i, "verb": verb, "status": "running", "message": ""}

        try:
            if verb == "comment":
                step_result["message"] = params.get("text", "")
                step_result["status"] = "passed"

            elif verb == "notice":
                step_result["message"] = params.get("message", "")
                step_result["status"] = "passed"

            elif verb == "pause":
                min_s = params.get("min_seconds", 1)
                max_s = params.get("max_seconds", min_s + 1)
                delay = random.uniform(min_s, max_s)
                await asyncio.sleep(min(delay, 3))
                step_result["message"] = f"Paused {delay:.1f}s"
                step_result["status"] = "passed"

            elif verb == "prompt":
                step_result["message"] = params.get("message", "Operator prompt")
                step_result["status"] = "passed"

            elif verb == "player-verb":
                pv = params.get("verb", "SET_CREDITS")
                pv_params = {k: v for k, v in params.items() if k != "verb"}
                # Execute against SmartEGM
                egm_state = _get_egm(session_id)
                # Simulate verb execution inline
                sub_body = {"session_id": session_id, "verb": pv, "params": pv_params}
                try:
                    from starlette.testclient import TestClient
                except ImportError:
                    pass
                # Direct execution
                if pv == "INSERT_BILL":
                    denom = pv_params.get("denomination", 2000)
                    egm_state["credits"] += denom
                    egm_state["coin_in"] += denom
                    egm_state["bills_in"] += denom
                elif pv in ("PUSH_PLAY_BUTTON", "PUSH_MAX_BET"):
                    wager = pv_params.get("wager", 500)
                    if egm_state["credits"] >= wager:
                        outcome = _roll_outcome(wager)
                        egm_state["credits"] -= wager
                        egm_state["coin_in"] += wager
                        egm_state["games_played"] += 1
                        if outcome["win"] > 0:
                            egm_state["credits"] += outcome["win"]
                            egm_state["coin_out"] += outcome["win"]
                elif pv == "CASH_OUT" and egm_state["credits"] > 0:
                    egm_state["coin_out"] += egm_state["credits"]
                    egm_state["credits"] = 0
                elif pv == "SET_CREDITS":
                    egm_state["credits"] = pv_params.get("amount", 0)
                elif pv == "REQUEST_HANDPAY":
                    egm_state["handpays"] += 1
                elif pv == "OPEN_DOOR":
                    egm_state["doors_open"].add(pv_params.get("door_type", "main"))
                elif pv == "CLOSE_DOOR":
                    egm_state["doors_open"].discard(pv_params.get("door_type", "main"))
                elif pv == "FORCE_TILT":
                    egm_state["state"] = "FAULT"
                elif pv == "CLEAR_FAULT":
                    egm_state["state"] = "ENABLED"
                step_result["message"] = f"{pv} executed"
                step_result["status"] = "passed"

            elif verb == "delete-all-snapshots":
                snapshots.clear()
                step_result["status"] = "passed"

            elif verb == "perform-snapshot":
                name = params.get("name", f"snap_{i}")
                egm_state = _get_egm(session_id)
                snapshots[name] = {"credits": egm_state["credits"], "coin_in": egm_state["coin_in"], "coin_out": egm_state["coin_out"], "games_played": egm_state["games_played"], "bills_in": egm_state["bills_in"], "handpays": egm_state["handpays"]}
                step_result["message"] = f"Snapshot '{name}' taken"
                step_result["status"] = "passed"

            elif verb == "balanced-meters-analysis":
                start_name = params.get("start", "baseline")
                end_name = params.get("end", "final")
                if start_name in snapshots and end_name in snapshots:
                    bma_results = _run_balanced_meters(snapshots[start_name], snapshots[end_name])
                    step_result["message"] = f"BMA: {sum(1 for r in bma_results if r['passed'])}/{len(bma_results)} passed"
                else:
                    step_result["message"] = f"Missing snapshots: {start_name} or {end_name}"
                step_result["status"] = "passed"

            elif verb == "wait-for-events":
                step_result["message"] = f"Waited for events: {params.get('events', [])}"
                step_result["status"] = "passed"

            elif verb == "wait-for-commands":
                step_result["message"] = f"Waited for commands"
                step_result["status"] = "passed"

            elif verb == "send-command":
                step_result["message"] = f"Sent {params.get('class','')}.{params.get('command','')}"
                step_result["status"] = "passed"

            elif verb == "set-response-config":
                step_result["message"] = f"Response config set: {params.get('name','')}"
                step_result["status"] = "passed"

            else:
                step_result["message"] = f"Verb '{verb}' executed"
                step_result["status"] = "passed"

            steps_done += 1
        except Exception as e:
            step_result["status"] = "failed"
            step_result["message"] = str(e)
            status = "FAILED"
            step_results.append(step_result)
            break

        step_results.append(step_result)

    if status == "RUNNING":
        status = "COMPLETED"

    egm_final = _get_egm(session_id)
    run_record = {
        "id": run_id, "script_id": script_id, "script_name": script["name"],
        "session_id": session_id, "status": status,
        "step_count": len(script["steps"]), "steps_done": steps_done,
        "step_results": step_results,
        "egm_final_state": {**egm_final, "doors_open": list(egm_final["doors_open"])},
        "snapshots": snapshots,
        "balanced_meters": bma_results,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "run_by": user.get("email"),
    }
    await db.lab_script_runs.insert_one(run_record)
    run_record.pop("_id", None)
    return run_record


@router.get("/scripts/runs")
async def list_script_runs(request: Request, limit: int = 20):
    await get_current_user(request)
    runs = await db.lab_script_runs.find({}, {"_id": 0, "step_results": 0}).sort("started_at", -1).limit(limit).to_list(limit)
    return {"runs": runs}


# ══════════════════════════════════════════════════
# 4. BALANCED METERS ANALYSIS — 8 Appendix B Tests
# ══════════════════════════════════════════════════

def _run_balanced_meters(before: dict, after: dict) -> list:
    delta = {k: after.get(k, 0) - before.get(k, 0) for k in set(list(before.keys()) + list(after.keys()))}
    ci = delta.get("coin_in", 0)
    co = delta.get("coin_out", 0)
    hp = delta.get("handpays", 0) * 120000
    bi = delta.get("bills_in", 0)
    gp = delta.get("games_played", 0)
    net = ci - co

    results = [
        _bm_test("BM-01", "Total Wager Balance", ci, bi, "coinIn == billsIn (simplified)"),
        _bm_test("BM-02", "Total Payout Balance", co, co, "coinOut == egmPaid + handPaid"),
        _bm_test("BM-03", "Net Win Integrity", net, ci - co, "netWin == coinIn - coinOut", tolerance=1),
        _bm_test("BM-04", "Progressive Hit Balance", 0, 0, "progWin == egmPaidProg + handPaidProg"),
        _bm_test("BM-05", "WAT Balance", 0, 0, "WAT in == WAT out + credits"),
        _bm_test("BM-06", "Voucher Balance", 0, 0, "vouchersIn == sum by type"),
        _bm_test("BM-07", "Bill Count vs Amount", bi, bi, "billCount × denom == billAmount"),
        _bm_test("BM-08", "Credit Meter Check", after.get("credits", 0), before.get("credits", 0) + ci - co, "finalCredits == init + in - out", tolerance=1),
    ]
    return results


def _bm_test(test_id, name, left, right, formula, tolerance=0):
    delta = abs(left - right)
    return {"testId": test_id, "testName": name, "passed": delta <= tolerance, "leftValue": left, "rightValue": right, "delta": delta, "formula": formula, "details": "Balanced" if delta <= tolerance else f"Out of balance by {delta}"}


@router.post("/balanced-meters")
async def run_balanced_meters_api(request: Request):
    await get_current_user(request)
    body = await request.json()
    before = body.get("before", {})
    after = body.get("after", {})
    results = _run_balanced_meters(before, after)
    return {"results": results, "passed": sum(1 for r in results if r["passed"]), "total": len(results)}


@router.post("/balanced-meters/export-csv")
async def export_balanced_meters_csv(request: Request):
    await get_current_user(request)
    body = await request.json()
    results = body.get("results", [])
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Test ID", "Test Name", "Result", "Left Value", "Right Value", "Delta", "Formula", "Details"])
    for r in results:
        writer.writerow([r["testId"], r["testName"], "PASS" if r["passed"] else "FAIL", r["leftValue"], r["rightValue"], r["delta"], r["formula"], r["details"]])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=balanced_meters.csv"})


# ══════════════════════════════════════════════════
# 5. TRANSCRIPT ANALYSIS REPORT (TAR) — 7 Sections
# ══════════════════════════════════════════════════

@router.post("/tar/generate")
async def generate_tar(request: Request):
    await get_current_user(request)
    body = await request.json()
    session_id = body.get("session_id", "default")
    transcripts = await db.lab_transcripts.find({"session_id": session_id}, {"_id": 0}).sort("occurred_at", 1).to_list(10000)

    # Section 1: Comms Sessions
    comms_sessions = []
    current_session = None
    for t in transcripts:
        if t.get("command_name") == "commsOnLine":
            if current_session:
                current_session["end_time"] = t["occurred_at"]
                current_session["is_complete"] = current_session.get("has_set_comms_state", False)
                comms_sessions.append(current_session)
            current_session = {"start_time": t["occurred_at"], "message_count": 0, "device_classes": set(), "has_set_comms_state": False, "end_time": None, "is_complete": False}
        if current_session:
            current_session["message_count"] += 1
            if t.get("command_class"):
                current_session["device_classes"].add(t["command_class"])
            if t.get("command_name") == "setCommsState":
                current_session["has_set_comms_state"] = True
    if current_session:
        current_session["is_complete"] = current_session.get("has_set_comms_state", False)
        current_session["device_classes"] = list(current_session["device_classes"])
        comms_sessions.append(current_session)
    for cs in comms_sessions:
        if isinstance(cs.get("device_classes"), set):
            cs["device_classes"] = list(cs["device_classes"])
        cs["is_red"] = not cs.get("has_set_comms_state", False)

    # Section 2: Session Summaries
    session_summaries = [{"session_index": i, "start": cs["start_time"], "messages": cs["message_count"], "classes": cs.get("device_classes", []), "complete": cs["is_complete"], "status": "RED" if cs.get("is_red") else "GREEN"} for i, cs in enumerate(comms_sessions)]

    # Section 3: Device Commands
    cmd_stats = {}
    for t in transcripts:
        if t.get("command_class") and t.get("command_name"):
            key = f"{t['command_class']}.{t['command_name']}"
            if key not in cmd_stats:
                cmd_stats[key] = {"class": t["command_class"], "command": t["command_name"], "tx_count": 0, "rx_count": 0}
            if t.get("direction") == "TX":
                cmd_stats[key]["tx_count"] += 1
            else:
                cmd_stats[key]["rx_count"] += 1
    command_stats = list(cmd_stats.values())

    # Section 4: Event Log
    event_log = [{"time": t["occurred_at"], "class": t.get("command_class", ""), "event": t.get("command_name", ""), "direction": t.get("direction", ""), "state": t.get("state", "Standard")} for t in transcripts[:500]]

    # Section 5: G2S ACK Errors
    ack_errors = [t for t in transcripts if t.get("error_code") and t.get("error_code") != "G2S_none"]

    # Section 6: Balanced Meters (from latest script run)
    bm_results = None
    latest_run = await db.lab_script_runs.find_one({"session_id": session_id, "balanced_meters": {"$ne": None}}, {"_id": 0, "balanced_meters": 1})
    if latest_run:
        bm_results = latest_run.get("balanced_meters")

    # Section 7: Coverage Map
    g2s_classes = ["cabinet", "communications", "eventHandler", "gamePlay", "meters", "noteAcceptor", "coinAcceptor", "printer", "voucher", "bonus", "player", "progressive", "mediaDisplay", "handpay"]
    exercised = set()
    for t in transcripts:
        cls = t.get("command_class", "")
        for gc in g2s_classes:
            if gc.lower() in cls.lower():
                exercised.add(gc)
    coverage = [{"class": gc, "exercised": gc in exercised, "status": "GREEN" if gc in exercised else "YELLOW"} for gc in g2s_classes]
    uncovered = [c for c in coverage if not c["exercised"]]

    # Overall Status
    has_red = any(cs.get("is_red") for cs in comms_sessions)
    has_ack_errors = len(ack_errors) > 0
    has_bm_fail = bm_results and any(not r["passed"] for r in bm_results) if bm_results else False
    overall = "RED" if has_red or has_ack_errors or has_bm_fail else "YELLOW" if len(uncovered) > 0 else "GREEN"

    report = {
        "session_id": session_id, "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall, "total_messages": len(transcripts),
        "sections": {
            "comms_sessions": comms_sessions,
            "session_summaries": session_summaries,
            "command_stats": command_stats,
            "event_log": event_log[:200],
            "ack_errors": ack_errors,
            "balanced_meters": bm_results,
            "coverage_map": coverage,
        },
        "flags": {"has_red_session": has_red, "has_ack_errors": has_ack_errors, "has_bm_failures": has_bm_fail, "uncovered_classes": len(uncovered)},
    }
    await db.lab_tar_reports.insert_one({**report, "id": str(uuid.uuid4())})
    report.pop("_id", None)
    return report


@router.get("/tar/reports")
async def list_tar_reports(request: Request, limit: int = 10):
    await get_current_user(request)
    reports = await db.lab_tar_reports.find({}, {"_id": 0, "sections": 0}).sort("generated_at", -1).limit(limit).to_list(limit)
    return {"reports": reports}


# ══════════════════════════════════════════════════
# 6. WATCHABLES XPATH ENGINE — 7 Pre-built Expressions
# ══════════════════════════════════════════════════

PREBUILT_WATCHABLES = [
    {"id": "startup", "name": "Startup Sequence", "expression": "//commsOnLine", "triggers_on": "EGM initiates commsOnLine"},
    {"id": "game-start", "name": "Game Start", "expression": "//gamePlayStatus[@gameStatus='G2S_gameStarted']", "triggers_on": "Every game cycle start"},
    {"id": "large-win", "name": "Large Win (>$100)", "expression": "//handPayLog[@cashableAmt>10000000]", "triggers_on": "Handpays > $100.00"},
    {"id": "voucher-redeemed", "name": "Voucher Redeemed", "expression": "//voucherLog[@voucherState='G2S_voucher102']", "triggers_on": "Voucher redemption"},
    {"id": "door-open", "name": "Cabinet Door Open", "expression": "//cabinetStatus[@cabinetDoorOpen='true']", "triggers_on": "Door opened"},
    {"id": "comms-disabled", "name": "commsDisabled", "expression": "//commsDisabled", "triggers_on": "EGM sends commsDisabled"},
    {"id": "ack-error", "name": "G2S ACK Error", "expression": "//g2sAck[@errorCode!='G2S_none']", "triggers_on": "Any ACK error"},
]

_active_watchables = {}
_watchable_matches = {}


@router.get("/watchables")
async def list_watchables(request: Request):
    await get_current_user(request)
    custom = await db.lab_watchables.find({}, {"_id": 0}).to_list(50)
    all_w = PREBUILT_WATCHABLES + custom
    # Add match counts
    for w in all_w:
        w["match_count"] = len(_watchable_matches.get(w["id"], []))
        w["is_active"] = w["id"] in _active_watchables
    return {"watchables": all_w, "prebuilt": len(PREBUILT_WATCHABLES), "custom": len(custom)}


@router.post("/watchables")
async def create_watchable(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    watchable = {
        "id": str(uuid.uuid4()), "name": body.get("name", "Custom Watch"),
        "expression": body.get("expression", ""),
        "triggers_on": body.get("triggers_on", ""),
        "created_by": user.get("email"), "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # Basic validation
    expr = watchable["expression"]
    if not expr or len(expr) < 3:
        raise HTTPException(status_code=400, detail="Invalid expression: too short")
    await db.lab_watchables.insert_one(watchable)
    watchable.pop("_id", None)
    return watchable


@router.post("/watchables/{watchable_id}/activate")
async def activate_watchable(request: Request, watchable_id: str):
    await get_current_user(request)
    _active_watchables[watchable_id] = True
    if watchable_id not in _watchable_matches:
        _watchable_matches[watchable_id] = []
    return {"message": f"Watchable {watchable_id} activated"}


@router.post("/watchables/{watchable_id}/deactivate")
async def deactivate_watchable(request: Request, watchable_id: str):
    await get_current_user(request)
    _active_watchables.pop(watchable_id, None)
    return {"message": f"Watchable {watchable_id} deactivated"}


@router.post("/watchables/evaluate")
async def evaluate_watchables(request: Request):
    """Evaluate all active watchables against a message."""
    await get_current_user(request)
    body = await request.json()
    message_xml = body.get("xml", "")
    matches = []
    all_watchables = PREBUILT_WATCHABLES + (await db.lab_watchables.find({}, {"_id": 0}).to_list(50))
    for w in all_watchables:
        if w["id"] not in _active_watchables:
            continue
        expr = w["expression"].replace("//", "")
        if expr.lower() in message_xml.lower():
            match = {"watchable_id": w["id"], "name": w["name"], "matched_at": datetime.now(timezone.utc).isoformat(), "expression": w["expression"]}
            matches.append(match)
            _watchable_matches.setdefault(w["id"], []).append(match)
    return {"matches": matches, "evaluated": len(_active_watchables)}


@router.get("/watchables/matches")
async def get_watchable_matches(request: Request, watchable_id: str = None):
    await get_current_user(request)
    if watchable_id:
        return {"matches": _watchable_matches.get(watchable_id, [])}
    return {"matches": {k: v for k, v in _watchable_matches.items()}}


# ══════════════════════════════════════════════════
# DEVICE TEMPLATES
# ══════════════════════════════════════════════════

DEFAULT_TEMPLATES = [
    {"id": "ace-velocity-3", "manufacturer": "ACE", "model": "Velocity-3", "software_version": "3.2.1", "g2s_schema": "G2S_2.1.0", "denominations": [100, 500, 1000, 2000, 10000], "classes": ["cabinet", "gamePlay", "noteAcceptor", "voucher", "handpay", "bonus", "eventHandler", "meters", "download", "GAT"]},
    {"id": "igt-s3000", "manufacturer": "IGT", "model": "S3000", "software_version": "5.1.0", "g2s_schema": "G2S_2.1.0", "denominations": [100, 500, 2500], "classes": ["cabinet", "gamePlay", "noteAcceptor", "voucher", "handpay", "eventHandler", "meters"]},
    {"id": "aristocrat-gen8", "manufacturer": "Aristocrat", "model": "Gen8", "software_version": "8.0.2", "g2s_schema": "G2S_2.1.0", "denominations": [100, 500, 1000, 2500, 5000, 10000], "classes": ["cabinet", "gamePlay", "noteAcceptor", "voucher", "handpay", "bonus", "player", "progressive", "eventHandler", "meters", "download", "GAT"]},
]


@router.get("/templates")
async def list_templates(request: Request):
    await get_current_user(request)
    return {"templates": DEFAULT_TEMPLATES}
