"""
UGG Gateway Core — Phase 2 Event Processing Pipeline.
Connects protocol adapters to central services: event store, digital twin,
exception engine, meter aggregation, WebSocket broadcast, audit trail.
"""
import asyncio
import uuid
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Callable
from database import db
from ws_manager import manager

logger = logging.getLogger(__name__)


class EventPipeline:
    """
    Central event processing pipeline. Every CanonicalEvent from every adapter
    flows through this pipeline before reaching any service.

    Pipeline stages:
    1. VALIDATE   — Schema validation (required fields)
    2. ENRICH     — Add statutory fields, resolve device/site metadata
    3. STORE      — Persist to events collection
    4. TWIN       — Update device_state_projection (digital twin)
    5. EXCEPTION  — Evaluate exception rules
    6. METER      — Update meter_snapshots if meter event
    7. BROADCAST  — Push to WebSocket clients
    8. AUDIT      — Write audit trail entry
    """

    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.stage_times: dict[str, float] = {}
        self._running = False
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
        self._worker_task: Optional[asyncio.Task] = None
        self._custom_processors: list[Callable] = []

    async def start(self):
        """Start the pipeline worker."""
        self._running = True
        self._worker_task = asyncio.create_task(self._process_loop())
        logger.info("Gateway Core EventPipeline started")

    async def stop(self):
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
        logger.info(f"Gateway Core EventPipeline stopped. Processed: {self.processed_count}, Errors: {self.error_count}")

    def add_processor(self, processor: Callable):
        """Add a custom processing stage to the pipeline."""
        self._custom_processors.append(processor)

    async def ingest(self, event: dict):
        """Ingest a CanonicalEvent into the pipeline."""
        if self._queue.full():
            logger.warning("EventPipeline queue full — dropping event")
            return
        await self._queue.put(event)

    def ingest_sync(self, event: dict):
        """Synchronous ingestion for adapter callbacks."""
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("EventPipeline queue full (sync) — dropping event")

    async def _process_loop(self):
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._process_event(event)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_count += 1
                logger.error(f"Pipeline error: {e}")

    async def _process_event(self, event: dict):
        """Run event through all pipeline stages."""
        try:
            # Stage 1: VALIDATE
            event = await self._stage_validate(event)
            if not event:
                return

            # Stage 2: ENRICH
            event = await self._stage_enrich(event)

            # Stage 3: STORE
            await self._stage_store(event)

            # Stage 4: DIGITAL TWIN
            await self._stage_update_twin(event)

            # Stage 5: EXCEPTION ENGINE
            await self._stage_check_exceptions(event)

            # Stage 6: METER AGGREGATION
            if event.get("event_type") == "meter_snapshot":
                await self._stage_meter_aggregate(event)

            # Stage 7: BROADCAST
            await self._stage_broadcast(event)

            # Stage 8: AUDIT
            await self._stage_audit(event)

            # Custom processors
            for processor in self._custom_processors:
                try:
                    await processor(event)
                except Exception as e:
                    logger.error(f"Custom processor error: {e}")

            self.processed_count += 1

        except Exception as e:
            self.error_count += 1
            logger.error(f"Pipeline processing error: {e}")

    async def _stage_validate(self, event: dict) -> Optional[dict]:
        """Stage 1: Validate required fields."""
        required = ["device_id", "event_type", "protocol"]
        for field in required:
            if not event.get(field):
                logger.warning(f"Pipeline: missing required field '{field}' — dropping event")
                return None
        if not event.get("id"):
            event["id"] = str(uuid.uuid4())
        if not event.get("occurred_at"):
            event["occurred_at"] = datetime.now(timezone.utc).isoformat()
        if not event.get("received_at"):
            event["received_at"] = datetime.now(timezone.utc).isoformat()
        # Integrity hash
        payload_str = json.dumps(event.get("payload", {}), sort_keys=True, default=str)
        event["integrity_hash"] = hashlib.sha256(payload_str.encode()).hexdigest()[:32]
        return event

    async def _stage_enrich(self, event: dict) -> dict:
        """Stage 2: Enrich with device/site metadata and statutory fields."""
        device_id = event.get("device_id")
        if not device_id:
            return event

        # Look up device
        device = await db.devices.find_one({"id": device_id}, {"_id": 0})
        if device:
            event.setdefault("tenant_id", device.get("tenant_id", ""))
            event.setdefault("site_id", device.get("site_id", ""))
            event.setdefault("device_serial", device.get("serial_number", ""))
            event.setdefault("software_version", device.get("firmware_version", ""))
            event.setdefault("distributor_id", device.get("distributor_id"))

            # Resolve retailer for statutory fields
            retailer_id = device.get("retailer_id")
            if retailer_id:
                retailer = await db.route_retailers.find_one({"id": retailer_id}, {"_id": 0})
                if retailer:
                    event.setdefault("operator_id", retailer.get("id"))
                    event.setdefault("site_address", retailer.get("address", ""))
                    event.setdefault("site_city", retailer.get("city", ""))
                    event.setdefault("site_county", retailer.get("county", ""))

        return event

    async def _stage_store(self, event: dict):
        """Stage 3: Persist event to events collection."""
        doc = {k: v for k, v in event.items() if v is not None}
        doc.pop("_id", None)
        await db.events.insert_one(doc)

    async def _stage_update_twin(self, event: dict):
        """Stage 4: Update device digital twin projection."""
        device_id = event.get("device_id")
        if not device_id:
            return

        now = datetime.now(timezone.utc).isoformat()
        update = {
            "last_event_at": now,
            "updated_at": now,
        }

        event_type = event.get("event_type", "")
        payload = event.get("payload", {})

        if event_type == "meter_snapshot":
            meters = payload.get("meters", {})
            if "coinIn" in meters:
                update["coin_in_today"] = meters["coinIn"].get("value", 0) if isinstance(meters["coinIn"], dict) else meters["coinIn"]
            if "coinOut" in meters:
                update["coin_out_today"] = meters["coinOut"].get("value", 0) if isinstance(meters["coinOut"], dict) else meters["coinOut"]
            if "currentCredits" in meters:
                update["current_credits"] = meters["currentCredits"].get("value", 0) if isinstance(meters["currentCredits"], dict) else meters["currentCredits"]
            update["last_meter_at"] = now

        if event_type == "device_state":
            comms_state = payload.get("command", "")
            if "commsOnLine" in comms_state:
                update["comms_state"] = "ONLINE"
                update["operational_state"] = "ONLINE"
            elif "commsClosing" in comms_state:
                update["comms_state"] = "CLOSING"
            elif "commsDisabled" in comms_state:
                update["comms_state"] = "SYNC"

        if "integrity" in event_type:
            update["software_integrity"] = "PASS" if payload.get("result") == "PASS" else "FAIL"
            update["last_integrity_at"] = now

        await db.device_state_projection.update_one(
            {"device_id": device_id},
            {"$set": update},
            upsert=True,
        )

    async def _stage_check_exceptions(self, event: dict):
        """Stage 5: Evaluate exception rules."""
        device_id = event.get("device_id", "")
        event_type = event.get("event_type", "")
        payload = event.get("payload", {})

        # Integrity violation
        if "integrity" in event_type and payload.get("result") == "FAIL":
            await self._raise_exception(device_id, event, "INTEGRITY_VIOLATION", "CRITICAL", f"Software integrity check FAILED on {device_id}")

        # Device tilt
        if event_type == "device.tilt":
            await self._raise_exception(device_id, event, "DEVICE_DISABLED", "WARNING", f"Tilt condition on {device_id}")

        # Door open
        if event_type == "device.door.opened":
            await self._raise_exception(device_id, event, "DOOR_OPEN", "WARNING", f"Door opened on {device_id}")

        # Handpay
        if event_type == "device.jackpot.handpay":
            await self._raise_exception(device_id, event, "HANDPAY_PENDING", "WARNING", f"Handpay triggered on {device_id}")

    async def _raise_exception(self, device_id: str, event: dict, exc_type: str, severity: str, detail: str):
        """Create a monitoring exception."""
        # Check if active exception of same type exists
        existing = await db.route_exceptions.find_one({"device_id": device_id, "type": exc_type, "is_active": True})
        if existing:
            return  # Don't duplicate

        device = await db.devices.find_one({"id": device_id}, {"_id": 0})
        exc = {
            "id": str(uuid.uuid4()),
            "type": exc_type,
            "severity": severity,
            "device_id": device_id,
            "device_ref": device.get("external_ref", "") if device else "",
            "device_description": f"{device.get('manufacturer', '')} {device.get('model', '')}" if device else "",
            "site_id": event.get("site_id", ""),
            "site_name": "",
            "distributor_id": event.get("distributor_id", ""),
            "raised_at": datetime.now(timezone.utc).isoformat(),
            "resolved_at": None,
            "detail": detail,
            "is_active": True,
            "source_event_id": event.get("id"),
        }
        await db.route_exceptions.insert_one(exc)
        logger.info(f"Gateway Core: Exception raised [{severity}] {exc_type} on {device_id}")

    async def _stage_meter_aggregate(self, event: dict):
        """Stage 6: Store meter snapshots for time-series analysis."""
        device_id = event.get("device_id")
        meters = event.get("payload", {}).get("meters", {})
        if not meters:
            return

        now = datetime.now(timezone.utc).isoformat()
        for canonical_name, meter_data in meters.items():
            value = meter_data.get("value", meter_data) if isinstance(meter_data, dict) else meter_data
            sas_code = meter_data.get("sas_code", "") if isinstance(meter_data, dict) else ""
            is_vendor = meter_data.get("is_vendor_ext", False) if isinstance(meter_data, dict) else False
            await db.meter_snapshots.insert_one({
                "id": str(uuid.uuid4()),
                "device_id": device_id,
                "tenant_id": event.get("tenant_id", ""),
                "canonical_name": canonical_name,
                "meter_value": value,
                "sas_code": sas_code,
                "is_vendor_ext": is_vendor,
                "recorded_at": now,
            })

    async def _stage_broadcast(self, event: dict):
        """Stage 7: Push event to WebSocket clients."""
        broadcast_event = {k: v for k, v in event.items() if k != "_id" and v is not None}
        await manager.broadcast(broadcast_event, "events")

    async def _stage_audit(self, event: dict):
        """Stage 8: Write audit trail entry for significant events."""
        significant = ["integrity", "alarm", "device.tilt", "device.door", "device.jackpot", "device.remote"]
        if not any(s in event.get("event_type", "") for s in significant):
            return

        await db.audit_records.insert_one({
            "id": str(uuid.uuid4()),
            "tenant_id": event.get("tenant_id", ""),
            "actor": "gateway_core",
            "action": f"event.processed.{event.get('event_type', 'unknown')}",
            "target_type": "device",
            "target_id": event.get("device_id", ""),
            "before": None,
            "after": {"event_type": event.get("event_type"), "severity": event.get("severity")},
            "evidence_ref": event.get("id"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_stats(self) -> dict:
        return {
            "processed": self.processed_count,
            "errors": self.error_count,
            "queue_size": self._queue.qsize(),
            "queue_max": self._queue.maxsize,
            "running": self._running,
            "custom_processors": len(self._custom_processors),
        }


# Singleton pipeline instance
pipeline = EventPipeline()


class GatewayCore:
    """
    Gateway Core orchestrator. Manages the event pipeline, adapter registry,
    and provides the API surface for the gateway.
    """

    def __init__(self):
        self.pipeline = pipeline
        self.adapters: dict = {}
        self.started_at: Optional[str] = None

    async def start(self):
        await self.pipeline.start()
        self.started_at = datetime.now(timezone.utc).isoformat()
        logger.info("Gateway Core started")

    async def stop(self):
        # Disconnect all adapters
        for aid, adapter in list(self.adapters.items()):
            try:
                await adapter.disconnect()
            except Exception:
                pass
        self.adapters.clear()
        await self.pipeline.stop()
        logger.info("Gateway Core stopped")

    def register_adapter(self, adapter_id: str, adapter):
        """Register an adapter and wire its events into the pipeline."""
        self.adapters[adapter_id] = adapter

        def on_event(evt):
            event_dict = evt.to_dict() if hasattr(evt, 'to_dict') else evt
            self.pipeline.ingest_sync(event_dict)

        adapter.on_event(on_event)
        logger.info(f"Gateway Core: Adapter registered {adapter_id}")

    def unregister_adapter(self, adapter_id: str):
        if adapter_id in self.adapters:
            del self.adapters[adapter_id]

    def get_status(self) -> dict:
        return {
            "started_at": self.started_at,
            "pipeline": self.pipeline.get_stats(),
            "adapters": {aid: a.get_status() for aid, a in self.adapters.items()},
            "adapter_count": len(self.adapters),
        }


# Singleton gateway core
gateway_core = GatewayCore()
