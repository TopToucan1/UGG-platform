from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("")
async def list_campaigns(request: Request, limit: int = 50):
    await get_current_user(request)
    campaigns = await db.message_campaigns.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"campaigns": campaigns}


@router.post("")
async def create_campaign(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    campaign = {
        "id": str(uuid.uuid4()),
        "tenant_id": body.get("tenant_id"),
        "name": body.get("name", "New Campaign"),
        "content": body.get("content", ""),
        "target_sites": body.get("target_sites", []),
        "target_device_count": body.get("target_device_count", 0),
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("email"),
        "delivered_count": 0,
        "failed_count": 0,
    }
    await db.message_campaigns.insert_one(campaign)
    campaign.pop("_id", None)
    return campaign


@router.post("/{campaign_id}/send")
async def send_campaign(request: Request, campaign_id: str):
    user = await get_current_user(request)
    campaign = await db.message_campaigns.find_one({"id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Simulate sending
    import random
    total = campaign.get("target_device_count", 10)
    delivered = total - random.randint(0, max(1, total // 10))
    failed = total - delivered

    await db.message_campaigns.update_one(
        {"id": campaign_id},
        {"$set": {"status": "delivered", "delivered_count": delivered, "failed_count": failed, "sent_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"message": "Campaign sent", "delivered": delivered, "failed": failed}
