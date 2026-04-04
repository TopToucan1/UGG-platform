"""
Gateway Core API — manages the event processing pipeline,
adapter lifecycle, and pipeline statistics.
"""
from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
from gateway_core import gateway_core, pipeline
import uuid
import asyncio
from datetime import datetime, timezone

router = APIRouter(prefix="/api/gateway", tags=["gateway"])


@router.get("/status")
async def gateway_status(request: Request):
    await get_current_user(request)
    return gateway_core.get_status()


@router.get("/pipeline/stats")
async def pipeline_stats(request: Request):
    await get_current_user(request)
    return pipeline.get_stats()


@router.post("/pipeline/start")
async def start_pipeline(request: Request):
    await get_current_user(request)
    if not pipeline._running:
        await pipeline.start()
    return {"status": "running", **pipeline.get_stats()}


@router.post("/pipeline/stop")
async def stop_pipeline(request: Request):
    await get_current_user(request)
    await pipeline.stop()
    return {"status": "stopped", **pipeline.get_stats()}


@router.post("/connect")
async def connect_adapter_to_gateway(request: Request):
    """Connect an adapter and wire it through the Gateway Core pipeline."""
    user = await get_current_user(request)
    body = await request.json()
    protocol = body.get("protocol", "SAS")
    device_id = body.get("device_id", f"dev-{uuid.uuid4().hex[:8]}")
    config = body.get("config", {})
    live_mode = body.get("live", False)

    # Ensure pipeline is running
    if not pipeline._running:
        await pipeline.start()

    # Create adapter based on protocol and mode
    if protocol == "SAS":
        if live_mode:
            from adapters.sas_live import SasLiveAdapter
            adapter = SasLiveAdapter(device_id)
        else:
            from adapters.sas_adapter import SasAdapter
            adapter = SasAdapter(device_id)
    elif protocol == "G2S":
        if live_mode:
            from adapters.g2s_live import G2SLiveAdapter
            adapter = G2SLiveAdapter(device_id)
        else:
            from adapters.g2s_adapter import G2SAdapter
            adapter = G2SAdapter(device_id)
    elif protocol == "S2S":
        from adapters.s2s_adapter import S2SAdapter
        adapter = S2SAdapter(device_id)
    elif protocol == "VENDOR":
        from adapters.vendor_connector import connector_factory
        manifest_id = config.get("manifest_id", "")
        adapter = connector_factory.create(manifest_id, device_id, config)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown protocol: {protocol}")

    adapter_id = f"{protocol}:{device_id}"

    # Wire adapter trace to trace buffer
    from routes.adapters import _add_trace
    adapter.on_trace(lambda t: _add_trace({**t, "adapter_id": adapter_id, "device_id": device_id}))

    # Register with Gateway Core (events flow through pipeline)
    gateway_core.register_adapter(adapter_id, adapter)

    try:
        await adapter.connect(config)
        return {
            "adapter_id": adapter_id,
            "mode": "live" if live_mode else "virtual",
            "status": adapter.get_status(),
            "pipeline": pipeline.get_stats(),
        }
    except Exception as e:
        gateway_core.unregister_adapter(adapter_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{adapter_id}/disconnect")
async def disconnect_from_gateway(request: Request, adapter_id: str):
    await get_current_user(request)
    adapter = gateway_core.adapters.get(adapter_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Adapter not found in gateway")
    await adapter.disconnect()
    gateway_core.unregister_adapter(adapter_id)
    return {"message": f"Adapter {adapter_id} disconnected from gateway", "pipeline": pipeline.get_stats()}


@router.post("/{adapter_id}/command")
async def send_gateway_command(request: Request, adapter_id: str):
    await get_current_user(request)
    adapter = gateway_core.adapters.get(adapter_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Adapter not found in gateway")
    body = await request.json()
    result = await adapter.send_command(body)
    return result


@router.get("/digital-twin")
async def get_digital_twin(request: Request, device_id: str = None):
    """Get digital twin projections for devices."""
    await get_current_user(request)
    query = {}
    if device_id:
        query["device_id"] = device_id
    twins = await db.device_state_projection.find(query, {"_id": 0}).to_list(200)
    return {"twins": twins, "count": len(twins)}


@router.get("/digital-twin/{device_id}")
async def get_device_twin(request: Request, device_id: str):
    await get_current_user(request)
    twin = await db.device_state_projection.find_one({"device_id": device_id}, {"_id": 0})
    if not twin:
        raise HTTPException(status_code=404, detail="No digital twin for this device")
    return twin
