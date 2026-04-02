from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from database import db
from auth import get_current_user
import csv
import io
import json
from datetime import datetime, timezone

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/financial/csv")
async def export_financial_csv(request: Request, event_type: str = None, limit: int = 5000):
    await get_current_user(request)
    query = {}
    if event_type:
        query["event_type"] = event_type
    events = await db.financial_events.find(query, {"_id": 0}).sort("occurred_at", -1).limit(limit).to_list(limit)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Time", "Type", "Amount", "Currency", "Device", "Player", "Game", "Denomination", "Site"])
    for e in events:
        writer.writerow([e.get("occurred_at", ""), e.get("event_type", ""), e.get("amount", ""), e.get("currency", ""), e.get("device_ref", ""), e.get("player_name", ""), e.get("game_title", ""), e.get("denomination", ""), e.get("site_name", "")])

    output.seek(0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=financial_export_{ts}.csv"})


@router.get("/players/csv")
async def export_players_csv(request: Request, status: str = None, limit: int = 5000):
    await get_current_user(request)
    query = {}
    if status:
        query["status"] = status
    sessions = await db.player_sessions.find(query, {"_id": 0}).sort("card_in_at", -1).limit(limit).to_list(limit)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Player ID", "Player Name", "Tier", "Device", "Site", "Card In", "Card Out", "Duration (min)", "Status", "Games", "Total Wagered", "Total Won", "Net Result", "Loyalty Points"])
    for s in sessions:
        writer.writerow([s.get("player_id", ""), s.get("player_name", ""), s.get("player_tier", ""), s.get("device_ref", ""), s.get("site_name", ""), s.get("card_in_at", ""), s.get("card_out_at", ""), s.get("duration_minutes", ""), s.get("status", ""), s.get("games_played", ""), s.get("total_wagered", ""), s.get("total_won", ""), s.get("net_result", ""), s.get("loyalty_points_earned", "")])

    output.seek(0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=player_sessions_{ts}.csv"})


@router.get("/devices/csv")
async def export_devices_csv(request: Request, limit: int = 5000):
    await get_current_user(request)
    devices = await db.devices.find({}, {"_id": 0}).sort("external_ref", 1).limit(limit).to_list(limit)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Device Ref", "Manufacturer", "Model", "Serial", "Protocol", "Version", "Status", "Firmware", "Last Seen", "Game", "Denomination"])
    for d in devices:
        writer.writerow([d.get("external_ref", ""), d.get("manufacturer", ""), d.get("model", ""), d.get("serial_number", ""), d.get("protocol_family", ""), d.get("protocol_version", ""), d.get("status", ""), d.get("firmware_version", ""), d.get("last_seen_at", ""), d.get("metadata", {}).get("game_title", ""), d.get("metadata", {}).get("denomination", "")])

    output.seek(0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=devices_{ts}.csv"})


@router.get("/events/csv")
async def export_events_csv(request: Request, event_type: str = None, severity: str = None, limit: int = 5000):
    await get_current_user(request)
    query = {}
    if event_type:
        query["event_type"] = event_type
    if severity:
        query["severity"] = severity
    events = await db.events.find(query, {"_id": 0}).sort("occurred_at", -1).limit(limit).to_list(limit)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Event ID", "Time", "Type", "Severity", "Device ID", "Protocol", "Payload"])
    for e in events:
        writer.writerow([e.get("id", ""), e.get("occurred_at", ""), e.get("event_type", ""), e.get("severity", ""), e.get("device_id", ""), e.get("source_protocol", ""), json.dumps(e.get("payload", {}))])

    output.seek(0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=events_{ts}.csv"})


@router.get("/audit/csv")
async def export_audit_csv(request: Request, limit: int = 5000):
    await get_current_user(request)
    records = await db.audit_records.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Actor", "Action", "Target Type", "Target ID", "Evidence"])
    for r in records:
        writer.writerow([r.get("timestamp", ""), r.get("actor", ""), r.get("action", ""), r.get("target_type", ""), r.get("target_id", ""), r.get("evidence_ref", "")])

    output.seek(0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=audit_{ts}.csv"})


@router.get("/jackpots/csv")
async def export_jackpots_csv(request: Request):
    await get_current_user(request)
    jackpots = await db.progressive_jackpots.find({}, {"_id": 0}).sort("current_amount", -1).to_list(100)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Type", "Site", "Status", "Base Amount", "Current Amount", "Ceiling", "Contribution %", "Linked Devices", "Total Hits", "Total Paid"])
    for j in jackpots:
        writer.writerow([j.get("name", ""), j.get("type", ""), j.get("site_name", ""), j.get("status", ""), j.get("base_amount", ""), j.get("current_amount", ""), j.get("ceiling_amount", ""), j.get("contribution_rate", ""), j.get("linked_device_count", ""), j.get("total_hits", ""), j.get("total_paid", "")])

    output.seek(0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=jackpots_{ts}.csv"})
