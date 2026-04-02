from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(request: Request, status: str = None, severity: str = None, limit: int = 50, skip: int = 0):
    await get_current_user(request)
    query = {}
    if status:
        query["status"] = status
    if severity:
        query["severity"] = severity
    alerts = await db.alerts.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.alerts.count_documents(query)
    return {"alerts": alerts, "total": total}


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(request: Request, alert_id: str):
    user = await get_current_user(request)
    result = await db.alerts.update_one(
        {"id": alert_id, "status": "active"},
        {"$set": {"status": "acknowledged", "acknowledged_at": datetime.now(timezone.utc).isoformat(), "acknowledged_by": user.get("email")}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found or already acknowledged")

    await db.audit_records.insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": None,
        "actor": user.get("email"),
        "action": "alert.acknowledged",
        "target_type": "alert",
        "target_id": alert_id,
        "before": {"status": "active"},
        "after": {"status": "acknowledged"},
        "evidence_ref": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return {"message": "Alert acknowledged"}


@router.post("/{alert_id}/resolve")
async def resolve_alert(request: Request, alert_id: str):
    user = await get_current_user(request)
    result = await db.alerts.update_one(
        {"id": alert_id, "status": {"$in": ["active", "acknowledged"]}},
        {"$set": {"status": "resolved", "resolved_at": datetime.now(timezone.utc).isoformat(), "resolved_by": user.get("email")}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found or already resolved")
    return {"message": "Alert resolved"}
