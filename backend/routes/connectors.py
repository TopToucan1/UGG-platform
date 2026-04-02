from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


@router.get("")
async def list_connectors(request: Request):
    await get_current_user(request)
    connectors = await db.connectors.find({}, {"_id": 0}).to_list(100)
    return {"connectors": connectors}


@router.get("/{connector_id}")
async def get_connector(request: Request, connector_id: str):
    await get_current_user(request)
    conn = await db.connectors.find_one({"id": connector_id}, {"_id": 0})
    if not conn:
        raise HTTPException(status_code=404, detail="Connector not found")
    manifests = await db.manifests.find({"connector_id": connector_id}, {"_id": 0}).to_list(100)
    conn["manifests"] = manifests
    device_count = await db.devices.count_documents({"connector_id": connector_id})
    conn["device_count"] = device_count
    return conn


@router.get("/{connector_id}/manifests")
async def get_connector_manifests(request: Request, connector_id: str):
    await get_current_user(request)
    manifests = await db.manifests.find({"connector_id": connector_id}, {"_id": 0}).to_list(100)
    return {"manifests": manifests}


@router.post("")
async def create_connector(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    conn = {
        "id": str(uuid.uuid4()),
        "name": body.get("name", "New Connector"),
        "type": body.get("type", "rest_poll"),
        "language": body.get("language", "python"),
        "version": "0.1.0",
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("email"),
    }
    await db.connectors.insert_one(conn)
    conn.pop("_id", None)
    return conn


@router.post("/{connector_id}/manifests")
async def create_manifest(request: Request, connector_id: str):
    user = await get_current_user(request)
    body = await request.json()
    manifest = {
        "id": str(uuid.uuid4()),
        "connector_id": connector_id,
        "name": body.get("name", "New Manifest"),
        "version": body.get("version", "0.1.0"),
        "status": "draft",
        "field_mappings": body.get("field_mappings", 0),
        "command_bindings": body.get("command_bindings", 0),
        "mapping_config": body.get("mapping_config", {}),
        "approved_by": None,
        "approved_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("email"),
    }
    await db.manifests.insert_one(manifest)
    manifest.pop("_id", None)
    return manifest


@router.post("/{connector_id}/manifests/{manifest_id}/approve")
async def approve_manifest(request: Request, connector_id: str, manifest_id: str):
    user = await get_current_user(request)
    result = await db.manifests.update_one(
        {"id": manifest_id, "connector_id": connector_id},
        {"$set": {"status": "approved", "approved_by": user.get("email"), "approved_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Manifest not found")
    return {"message": "Manifest approved"}
