"""
Protocol Adapter Management API — manages adapter instances, traces, and status.
"""
from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import uuid
import asyncio
from datetime import datetime, timezone
from adapters import ConnectionState

router = APIRouter(prefix="/api/adapters", tags=["adapters"])

# In-memory adapter registry (production would use a proper service manager)
_active_adapters: dict = {}
_trace_buffer: list[dict] = []
MAX_TRACE = 500


def _add_trace(trace: dict):
    trace["id"] = str(uuid.uuid4())
    trace["timestamp"] = datetime.now(timezone.utc).isoformat()
    _trace_buffer.append(trace)
    if len(_trace_buffer) > MAX_TRACE:
        _trace_buffer.pop(0)


@router.get("")
async def list_adapters(request: Request):
    await get_current_user(request)
    statuses = []
    for aid, adapter in _active_adapters.items():
        statuses.append({"adapter_id": aid, **adapter.get_status()})
    return {"adapters": statuses, "count": len(statuses)}


@router.post("/connect")
async def connect_adapter(request: Request):
    """Start an adapter instance."""
    user = await get_current_user(request)
    body = await request.json()
    protocol = body.get("protocol", "SAS")
    device_id = body.get("device_id", f"dev-{uuid.uuid4().hex[:8]}")
    config = body.get("config", {})

    if protocol == "SAS":
        from adapters.sas_adapter import SasAdapter
        adapter = SasAdapter(device_id)
    elif protocol == "G2S":
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

    # Wire up trace handler
    adapter.on_trace(lambda t: _add_trace({**t, "adapter_id": adapter_id, "device_id": device_id}))

    # Wire up event handler to store in DB
    async def store_event(evt):
        doc = evt.to_dict()
        doc.pop("_id", None)
        await db.events.insert_one(doc)

    def event_handler(evt):
        asyncio.create_task(store_event(evt))

    adapter.on_event(event_handler)

    try:
        await adapter.connect(config)
        _active_adapters[adapter_id] = adapter
        return {"adapter_id": adapter_id, "status": adapter.get_status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{adapter_id}/disconnect")
async def disconnect_adapter(request: Request, adapter_id: str):
    await get_current_user(request)
    adapter = _active_adapters.get(adapter_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Adapter not found")
    await adapter.disconnect()
    del _active_adapters[adapter_id]
    return {"message": f"Adapter {adapter_id} disconnected"}


@router.get("/{adapter_id}/status")
async def adapter_status(request: Request, adapter_id: str):
    await get_current_user(request)
    adapter = _active_adapters.get(adapter_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Adapter not found")
    return adapter.get_status()


@router.post("/{adapter_id}/command")
async def send_adapter_command(request: Request, adapter_id: str):
    await get_current_user(request)
    adapter = _active_adapters.get(adapter_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Adapter not found")
    body = await request.json()
    result = await adapter.send_command(body)
    return result


@router.get("/traces")
async def get_traces(request: Request, channel: str = None, protocol: str = None, limit: int = 100):
    await get_current_user(request)
    traces = list(_trace_buffer)
    if channel:
        traces = [t for t in traces if t.get("channel") == channel]
    if protocol:
        traces = [t for t in traces if t.get("protocol") == protocol]
    traces = traces[-limit:]
    traces.reverse()
    return {"traces": traces, "total": len(traces)}


@router.get("/traces/channels")
async def get_trace_channels(request: Request):
    await get_current_user(request)
    channels = list(set(t.get("channel", "unknown") for t in _trace_buffer))
    protocols = list(set(t.get("protocol", "unknown") for t in _trace_buffer))
    return {"channels": sorted(channels), "protocols": sorted(protocols), "total_traces": len(_trace_buffer)}


# Register default vendor connector manifests
def register_default_manifests():
    from adapters.vendor_connector import ConnectorManifest, connector_factory
    defaults = [
        ConnectorManifest("rest-loyalty", "REST Loyalty Connector", "1.0.0", "REST", [{"source_field": "player_id", "canonical_field": "player_id"}, {"source_field": "points", "canonical_field": "payload.loyalty_points"}], "Silver", {"required": ["url"]}),
        ConnectorManifest("db-legacy-cms", "Database Legacy CMS", "1.0.0", "DATABASE", [{"source_field": "machine_id", "canonical_field": "device_id"}, {"source_field": "meter_reading", "canonical_field": "payload.meter_value"}], "Bronze", {"required": ["connectionString"]}),
        ConnectorManifest("log-proprietary", "Log File Parser", "1.0.0", "LOG", [], "Bronze", {"required": ["logPath"]}),
        ConnectorManifest("msgbus-kafka", "Kafka Event Stream", "1.0.0", "MESSAGE_BUS", [], "Gold", {"required": ["brokerUrl", "topic"]}),
    ]
    for m in defaults:
        connector_factory.register(m)

register_default_manifests()
