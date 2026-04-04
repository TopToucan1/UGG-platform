"""
UGG Protocol Adapter Base — The contract every adapter must honor.
Adapters translate device protocols into CanonicalEvents.
They do NOT store data, make business decisions, or know about other devices.
"""
from enum import Enum
from typing import Optional, Callable, Any
from datetime import datetime, timezone
import uuid
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    CLOSED = "CLOSED"
    OPENING = "OPENING"
    SYNC = "SYNC"
    ONLINE = "ONLINE"
    CLOSING = "CLOSING"
    LOST = "LOST"


class ProtocolType(str, Enum):
    SAS = "SAS"
    G2S = "G2S"
    S2S = "S2S"
    PROPRIETARY = "PROPRIETARY"


class CanonicalEvent:
    def __init__(self, device_id: str, event_type: str, protocol: str, payload: dict,
                 tenant_id: str = "", site_id: str = "", **kwargs):
        self.id = str(uuid.uuid4())
        self.tenant_id = tenant_id
        self.site_id = site_id
        self.device_id = device_id
        self.event_type = event_type
        self.protocol = protocol
        self.occurred_at = datetime.now(timezone.utc).isoformat()
        self.received_at = datetime.now(timezone.utc).isoformat()
        self.payload = payload
        # Statutory route fields
        self.distributor_id = kwargs.get("distributor_id")
        self.site_county = kwargs.get("site_county")
        self.software_version = kwargs.get("software_version")
        self.device_serial = kwargs.get("device_serial")

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}


class ProtocolAdapter:
    """Base class for all protocol adapters."""

    def __init__(self, protocol: ProtocolType, device_id: str):
        self.protocol = protocol
        self.device_id = device_id
        self.state = ConnectionState.CLOSED
        self._event_handlers: list[Callable] = []
        self._error_handlers: list[Callable] = []
        self._state_handlers: list[Callable] = []
        self._trace_handlers: list[Callable] = []

    async def connect(self, config: dict) -> None:
        raise NotImplementedError

    async def disconnect(self) -> None:
        raise NotImplementedError

    def get_connection_state(self) -> ConnectionState:
        return self.state

    async def poll_meters(self) -> list[dict]:
        raise NotImplementedError

    async def get_device_info(self) -> dict:
        raise NotImplementedError

    async def send_command(self, cmd: dict) -> dict:
        raise NotImplementedError

    def on_event(self, handler: Callable):
        self._event_handlers.append(handler)

    def on_error(self, handler: Callable):
        self._error_handlers.append(handler)

    def on_state_change(self, handler: Callable):
        self._state_handlers.append(handler)

    def on_trace(self, handler: Callable):
        self._trace_handlers.append(handler)

    def _emit_event(self, event: CanonicalEvent):
        for h in self._event_handlers:
            try:
                h(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def _emit_error(self, error: Exception):
        for h in self._error_handlers:
            try:
                h(error)
            except Exception:
                pass

    def _emit_trace(self, trace: dict):
        for h in self._trace_handlers:
            try:
                h(trace)
            except Exception:
                pass

    def _set_state(self, new_state: ConnectionState):
        old = self.state
        self.state = new_state
        for h in self._state_handlers:
            try:
                h(old, new_state)
            except Exception:
                pass
        logger.info(f"[{self.protocol}:{self.device_id}] {old} -> {new_state}")
