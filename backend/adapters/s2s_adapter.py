"""
S2S Adapter — System-to-System protocol for Central ↔ Edge communication.
UGG Agent is the Edge. Central Monitoring System is the Central.
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime, timezone
from adapters import ProtocolAdapter, ProtocolType, ConnectionState, CanonicalEvent

logger = logging.getLogger(__name__)

S2S_SCHEMA_VERSIONS = ["S2S_1.2.6", "S2S_1.3.1", "S2S_1.5.0"]


class S2SAdapter(ProtocolAdapter):
    """S2S adapter acts as both client (posting to Central) and server (receiving from Central)."""

    def __init__(self, device_id: str):
        super().__init__(ProtocolType.S2S, device_id)
        self.config: dict = {}
        self.edge_id: str = ""
        self.central_url: str = ""
        self.schema_version: str = "S2S_1.5.0"
        self.managed_devices: list[str] = []
        self.report_task: Optional[asyncio.Task] = None
        self.last_push_at: Optional[str] = None
        self.push_count = 0
        self.command_count = 0
        self.last_event_at: Optional[str] = None

    async def connect(self, config: dict) -> None:
        self.config = config
        self.edge_id = config.get("edgeId", f"edge-{self.device_id}")
        self.central_url = config.get("centralUrl", "")
        self.schema_version = config.get("s2sSchema", "S2S_1.5.0")
        self.managed_devices = config.get("devices", [])

        if self.schema_version not in S2S_SCHEMA_VERSIONS:
            raise ValueError(f"Unsupported S2S schema: {self.schema_version}")

        self._set_state(ConnectionState.OPENING)
        logger.info(f"[S2S:{self.edge_id}] Connecting to Central at {self.central_url} (schema: {self.schema_version})")

        # Handshake with Central
        await self._negotiate_handshake()
        self._set_state(ConnectionState.ONLINE)

        # Start periodic push
        interval = config.get("reportInterval", 60000) / 1000.0
        self.report_task = asyncio.create_task(self._push_loop(interval))

    async def disconnect(self) -> None:
        self._set_state(ConnectionState.CLOSING)
        if self.report_task:
            self.report_task.cancel()
        self._set_state(ConnectionState.CLOSED)

    async def _negotiate_handshake(self):
        """Negotiate S2S connection with Central."""
        self._emit_trace({"channel": "soap", "direction": "out", "protocol": "S2S", "command": "s2sNegotiate", "xml": f'<s2s:negotiate s2s:edgeId="{self.edge_id}" s2s:schema="{self.schema_version}" s2s:deviceCount="{len(self.managed_devices)}"/>'})
        self._emit_event(CanonicalEvent(device_id=self.device_id, event_type="device_state", protocol="S2S", payload={"action": "negotiate", "edge_id": self.edge_id, "schema": self.schema_version}))
        await asyncio.sleep(0.1)
        self._emit_trace({"channel": "soap", "direction": "in", "protocol": "S2S", "command": "s2sNegotiateAck", "xml": f'<s2s:negotiateAck s2s:status="accepted"/>'})
        logger.info(f"[S2S:{self.edge_id}] Handshake complete — managing {len(self.managed_devices)} devices")

    async def _push_loop(self, interval: float):
        """Periodically push aggregated metrics to Central."""
        while self.state == ConnectionState.ONLINE:
            try:
                await asyncio.sleep(interval)
                await self.push_to_central()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[S2S:{self.edge_id}] Push error: {e}")

    async def push_to_central(self):
        """Aggregate device metrics and push to Central."""
        now = datetime.now(timezone.utc).isoformat()
        self.push_count += 1
        self.last_push_at = now
        self.last_event_at = now

        payload = {
            "edge_id": self.edge_id,
            "push_sequence": self.push_count,
            "device_count": len(self.managed_devices),
            "timestamp": now,
        }
        self._emit_trace({"channel": "soap", "direction": "out", "protocol": "S2S", "command": "s2sPushMetrics", "xml": f'<s2s:pushMetrics s2s:edgeId="{self.edge_id}" s2s:seq="{self.push_count}"/>'})
        self._emit_event(CanonicalEvent(device_id=self.device_id, event_type="device_state", protocol="S2S", payload=payload))
        return payload

    async def on_central_command(self, command: dict):
        """Receive a command from Central, translate to G2S, route to correct adapter."""
        self.command_count += 1
        cmd_type = command.get("type", "unknown")
        target_device = command.get("targetDeviceId")
        self._emit_trace({"channel": "g2s", "direction": "in", "protocol": "S2S", "command": f"centralCommand:{cmd_type}", "target": target_device})
        self._emit_event(CanonicalEvent(device_id=target_device or self.device_id, event_type="device_state", protocol="S2S", payload={"central_command": cmd_type, "target": target_device}))
        logger.info(f"[S2S:{self.edge_id}] Central command: {cmd_type} -> device {target_device}")
        return {"status": "routed", "command": cmd_type, "target": target_device}

    async def poll_meters(self) -> list[dict]:
        return []

    async def get_device_info(self) -> dict:
        return {"device_id": self.device_id, "protocol": "S2S", "edge_id": self.edge_id, "state": self.state, "schema": self.schema_version, "managed_devices": len(self.managed_devices), "push_count": self.push_count, "command_count": self.command_count}

    async def send_command(self, cmd: dict) -> dict:
        return await self.on_central_command(cmd)

    def get_status(self) -> dict:
        return {
            "protocol": "S2S", "device_id": self.device_id, "state": self.state.value,
            "edge_id": self.edge_id, "schema_version": self.schema_version,
            "managed_devices": len(self.managed_devices), "push_count": self.push_count,
            "command_count": self.command_count, "last_push_at": self.last_push_at,
            "last_event_at": self.last_event_at,
        }
