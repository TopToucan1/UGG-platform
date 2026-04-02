from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
from pydantic import BaseModel
from typing import Optional, List, Dict
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


# --- Mapping Models ---
class FieldMapping(BaseModel):
    id: str
    source_field: str
    canonical_field: str
    transform: Optional[str] = None
    confidence: Optional[float] = None

class SaveMappingsRequest(BaseModel):
    mappings: List[FieldMapping]


# --- Connector CRUD ---
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
    # Load saved mappings
    mappings = await db.connector_mappings.find({"connector_id": connector_id}, {"_id": 0}).to_list(200)
    conn["mappings"] = mappings
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


# --- Field Mappings ---
@router.get("/{connector_id}/mappings")
async def get_mappings(request: Request, connector_id: str):
    await get_current_user(request)
    mappings = await db.connector_mappings.find({"connector_id": connector_id}, {"_id": 0}).to_list(200)
    return {"mappings": mappings}


@router.post("/{connector_id}/mappings")
async def save_mappings(request: Request, connector_id: str):
    user = await get_current_user(request)
    body = await request.json()
    mappings_data = body.get("mappings", [])

    # Delete old mappings for this connector
    await db.connector_mappings.delete_many({"connector_id": connector_id})

    # Insert new mappings
    docs = []
    for m in mappings_data:
        docs.append({
            "id": m.get("id", str(uuid.uuid4())),
            "connector_id": connector_id,
            "source_field": m["source_field"],
            "canonical_field": m["canonical_field"],
            "transform": m.get("transform"),
            "confidence": m.get("confidence"),
            "created_by": user.get("email"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    if docs:
        await db.connector_mappings.insert_many(docs)

    return {"message": f"Saved {len(docs)} mappings", "count": len(docs)}


@router.delete("/{connector_id}/mappings/{mapping_id}")
async def delete_mapping(request: Request, connector_id: str, mapping_id: str):
    await get_current_user(request)
    result = await db.connector_mappings.delete_one({"id": mapping_id, "connector_id": connector_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return {"message": "Mapping deleted"}


# --- Manifests ---
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


# --- Deployments ---
@router.get("/{connector_id}/deployments")
async def list_deployments(request: Request, connector_id: str):
    await get_current_user(request)
    deployments = await db.deployments.find({"connector_id": connector_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"deployments": deployments}


@router.post("/{connector_id}/deploy")
async def create_deployment(request: Request, connector_id: str):
    user = await get_current_user(request)
    body = await request.json()

    connector = await db.connectors.find_one({"id": connector_id}, {"_id": 0})
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    manifest_id = body.get("manifest_id")
    if manifest_id:
        manifest = await db.manifests.find_one({"id": manifest_id, "status": "approved"}, {"_id": 0})
        if not manifest:
            raise HTTPException(status_code=400, detail="Manifest must be approved before deployment")

    target_scope = body.get("target_scope", "all")
    target_site_id = body.get("target_site_id")
    strategy = body.get("strategy", "canary")
    canary_percent = body.get("canary_percent", 5)

    deployment = {
        "id": str(uuid.uuid4()),
        "connector_id": connector_id,
        "connector_name": connector.get("name"),
        "manifest_id": manifest_id,
        "version": connector.get("version", "0.1.0"),
        "target_scope": target_scope,
        "target_site_id": target_site_id,
        "strategy": strategy,
        "canary_percent": canary_percent if strategy == "canary" else 100,
        "status": "pending_approval",
        "phase": "pending",
        "phases": _build_phases(strategy, canary_percent),
        "current_phase_index": 0,
        "created_by": user.get("email"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_by": None,
        "approved_at": None,
        "started_at": None,
        "completed_at": None,
        "rolled_back_at": None,
        "health_checks": [],
        "affected_devices": 0,
    }

    # Count affected devices
    dq = {"connector_id": connector_id}
    if target_site_id:
        dq["site_id"] = target_site_id
    deployment["affected_devices"] = await db.devices.count_documents(dq)

    await db.deployments.insert_one(deployment)
    deployment.pop("_id", None)

    await db.audit_records.insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": None,
        "actor": user.get("email"),
        "action": "deployment.created",
        "target_type": "connector",
        "target_id": connector_id,
        "before": None,
        "after": {"deployment_id": deployment["id"], "strategy": strategy},
        "evidence_ref": deployment["id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    return deployment


def _build_phases(strategy, canary_percent):
    if strategy == "full":
        return [{"name": "Full Rollout", "percent": 100, "status": "pending", "started_at": None, "completed_at": None}]
    elif strategy == "canary":
        phases = [
            {"name": "Canary", "percent": canary_percent, "duration_minutes": 15, "status": "pending", "started_at": None, "completed_at": None},
            {"name": "Progressive 25%", "percent": 25, "duration_minutes": 15, "status": "pending", "started_at": None, "completed_at": None},
            {"name": "Progressive 50%", "percent": 50, "duration_minutes": 15, "status": "pending", "started_at": None, "completed_at": None},
            {"name": "Full Rollout", "percent": 100, "status": "pending", "started_at": None, "completed_at": None},
        ]
        return phases
    return [{"name": "Full Rollout", "percent": 100, "status": "pending", "started_at": None, "completed_at": None}]


@router.post("/{connector_id}/deployments/{deployment_id}/approve")
async def approve_deployment(request: Request, connector_id: str, deployment_id: str):
    user = await get_current_user(request)
    now = datetime.now(timezone.utc).isoformat()
    result = await db.deployments.update_one(
        {"id": deployment_id, "status": "pending_approval"},
        {"$set": {
            "status": "approved",
            "approved_by": user.get("email"),
            "approved_at": now,
        }},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Deployment not found or already approved")
    return {"message": "Deployment approved"}


@router.post("/{connector_id}/deployments/{deployment_id}/start")
async def start_deployment(request: Request, connector_id: str, deployment_id: str):
    user = await get_current_user(request)
    dep = await db.deployments.find_one({"id": deployment_id})
    if not dep:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if dep["status"] not in ["approved", "in_progress"]:
        raise HTTPException(status_code=400, detail="Deployment must be approved first")

    now = datetime.now(timezone.utc).isoformat()
    phases = dep.get("phases", [])
    idx = dep.get("current_phase_index", 0)

    if idx < len(phases):
        phases[idx]["status"] = "active"
        phases[idx]["started_at"] = now

    # Simulate a health check
    import random
    health = {
        "timestamp": now,
        "phase": phases[idx]["name"] if idx < len(phases) else "unknown",
        "error_rate": round(random.uniform(0, 2.5), 2),
        "latency_ms": round(random.uniform(10, 80), 1),
        "events_processed": random.randint(50, 500),
        "status": "healthy",
    }
    if health["error_rate"] > 5:
        health["status"] = "degraded"

    await db.deployments.update_one(
        {"id": deployment_id},
        {"$set": {
            "status": "in_progress",
            "phase": phases[idx]["name"] if idx < len(phases) else "deploying",
            "phases": phases,
            "started_at": dep.get("started_at") or now,
            "current_phase_index": idx,
        }, "$push": {"health_checks": health}},
    )

    dep_updated = await db.deployments.find_one({"id": deployment_id}, {"_id": 0})
    return dep_updated


@router.post("/{connector_id}/deployments/{deployment_id}/promote")
async def promote_deployment(request: Request, connector_id: str, deployment_id: str):
    """Move to next phase of canary deployment."""
    user = await get_current_user(request)
    dep = await db.deployments.find_one({"id": deployment_id})
    if not dep or dep["status"] != "in_progress":
        raise HTTPException(status_code=400, detail="Invalid deployment state")

    now = datetime.now(timezone.utc).isoformat()
    phases = dep.get("phases", [])
    idx = dep.get("current_phase_index", 0)

    # Complete current phase
    if idx < len(phases):
        phases[idx]["status"] = "completed"
        phases[idx]["completed_at"] = now

    next_idx = idx + 1
    if next_idx >= len(phases):
        # All phases complete
        await db.deployments.update_one(
            {"id": deployment_id},
            {"$set": {"status": "completed", "phase": "completed", "phases": phases, "completed_at": now, "current_phase_index": next_idx}},
        )
        return {"message": "Deployment completed successfully", "status": "completed"}
    else:
        # Start next phase
        phases[next_idx]["status"] = "active"
        phases[next_idx]["started_at"] = now

        import random
        health = {
            "timestamp": now,
            "phase": phases[next_idx]["name"],
            "error_rate": round(random.uniform(0, 1.5), 2),
            "latency_ms": round(random.uniform(10, 60), 1),
            "events_processed": random.randint(100, 1000),
            "status": "healthy",
        }

        await db.deployments.update_one(
            {"id": deployment_id},
            {"$set": {"phases": phases, "phase": phases[next_idx]["name"], "current_phase_index": next_idx}, "$push": {"health_checks": health}},
        )
        dep_updated = await db.deployments.find_one({"id": deployment_id}, {"_id": 0})
        return dep_updated


@router.post("/{connector_id}/deployments/{deployment_id}/rollback")
async def rollback_deployment(request: Request, connector_id: str, deployment_id: str):
    user = await get_current_user(request)
    now = datetime.now(timezone.utc).isoformat()
    result = await db.deployments.update_one(
        {"id": deployment_id, "status": {"$in": ["in_progress", "approved"]}},
        {"$set": {"status": "rolled_back", "phase": "rolled_back", "rolled_back_at": now, "rolled_back_by": user.get("email")}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Cannot rollback")

    await db.audit_records.insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": None,
        "actor": user.get("email"),
        "action": "deployment.rolled_back",
        "target_type": "connector",
        "target_id": connector_id,
        "before": None,
        "after": {"deployment_id": deployment_id},
        "evidence_ref": deployment_id,
        "timestamp": now,
    })
    return {"message": "Deployment rolled back"}


# --- Dashboard Charts Data ---
@router.get("/{connector_id}/stats")
async def get_connector_stats(request: Request, connector_id: str):
    await get_current_user(request)
    device_count = await db.devices.count_documents({"connector_id": connector_id})
    event_count = await db.events.count_documents({"connector_id": connector_id})
    deployments = await db.deployments.count_documents({"connector_id": connector_id})
    return {"device_count": device_count, "event_count": event_count, "deployment_count": deployments}
