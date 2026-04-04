"""
G2S Adapter — XML over SOAP over HTTP for modern casino EGMs.
6 transport states, startup algorithm, commsDisabled handler, keepalive, proxy cert.
"""
import asyncio
import logging
import uuid
from typing import Optional
from datetime import datetime, timezone
from adapters import ProtocolAdapter, ProtocolType, ConnectionState, CanonicalEvent

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════
# G2S 6 TRANSPORT STATES
# ═══════════════════════════════════════════
# closed -> opening -> sync -> online -> closing -> closed
#                                    -> lost (unexpected disconnect)

G2S_CLASSES = [
    "cabinet", "communications", "eventHandler", "gamePlay", "meters",
    "noteAcceptor", "coinAcceptor", "printer", "voucher", "bonus",
    "player", "progressive", "mediaDisplay", "handpay",
]


# ═══════════════════════════════════════════
# commsDisabled HANDLER
# ═══════════════════════════════════════════
class CommsDisabledHandler:
    """Handles the G2S commsDisabled loop-breaking protocol."""
    def __init__(self, adapter: 'G2SAdapter'):
        self.adapter = adapter
        self.disabled_count = 0
        self.sync_timer: Optional[asyncio.Task] = None

    async def on_comms_disabled(self, device_id: str):
        self.disabled_count += 1
        logger.info(f"[G2S:{device_id}] commsDisabled received (count: {self.disabled_count})")
        # Always respond with commsDisabledAck immediately
        await self.adapter._send_soap("communications", "commsDisabledAck", {"deviceId": device_id})
        self.adapter._emit_trace({"channel": "g2s", "direction": "out", "protocol": "G2S", "command": "commsDisabledAck", "class": "communications", "deviceId": device_id})
        # On first occurrence, schedule setCommsState to break the loop
        if self.disabled_count == 1:
            self.sync_timer = asyncio.create_task(self._send_enable(device_id))

    async def _send_enable(self, device_id: str):
        await asyncio.sleep(2)  # Allow time for EGM to be ready
        await self.adapter._send_soap("communications", "setCommsState", {"deviceId": device_id, "enable": True})
        self.adapter._emit_trace({"channel": "g2s", "direction": "out", "protocol": "G2S", "command": "setCommsState", "class": "communications", "params": {"enable": True}})
        logger.info(f"[G2S:{device_id}] Sent setCommsState enable=true to break commsDisabled loop")

    def on_comms_online(self, device_id: str):
        self.disabled_count = 0
        if self.sync_timer:
            self.sync_timer.cancel()
            self.sync_timer = None
        logger.info(f"[G2S:{device_id}] commsDisabled loop broken — EGM online")


# ═══════════════════════════════════════════
# STARTUP ALGORITHM ENGINE
# ═══════════════════════════════════════════
FIXED_ANCHORS = [
    {"class": "communications", "command": "commsOnLineAck"},
    {"class": "communications", "command": "commsDisabledAck"},
]

class StartupAlgorithmEngine:
    def __init__(self, adapter: 'G2SAdapter'):
        self.adapter = adapter
        self.mode = "AUTO"  # AUTO or STEP_THROUGH
        self.step_queue: list[dict] = []
        self.current_step: Optional[dict] = None
        self.verbose_mode = True

    async def run(self, egm_descriptor: dict):
        logger.info(f"[G2S:{self.adapter.device_id}] Running startup algorithm (mode={self.mode})")
        # Step 1: Fixed anchors
        for anchor in FIXED_ANCHORS:
            await self.adapter._send_soap(anchor["class"], anchor["command"], {"deviceId": self.adapter.device_id})
            self.adapter._emit_trace({"channel": "g2s", "direction": "out", "protocol": "G2S", "command": anchor["command"], "class": anchor["class"], "phase": "startup_anchor"})

        # Step 2: Expand verbose commands if enabled
        commands = list(self.step_queue)
        if self.verbose_mode:
            commands = self._expand_verbose(commands, egm_descriptor)

        # Step 3: Execute each step
        for i, step in enumerate(commands):
            self.current_step = step
            if self.mode == "STEP_THROUGH":
                logger.info(f"[G2S:{self.adapter.device_id}] Step-through: waiting for operator to advance step {i+1}/{len(commands)}")
                # In step-through mode, we'd wait for operator input (simulated here)
                await asyncio.sleep(0.5)
            await self.adapter._send_soap(step["class"], step["command"], step.get("params", {}))
            self.adapter._emit_trace({"channel": "g2s", "direction": "out", "protocol": "G2S", "command": step["command"], "class": step["class"], "phase": "startup_step", "step": i + 1})

        # Step 4: Final enablement
        await self.adapter._send_soap("communications", "setCommsState", {"enable": True})
        self.current_step = None
        logger.info(f"[G2S:{self.adapter.device_id}] Startup algorithm complete — {len(commands)} steps executed")

    def _expand_verbose(self, commands: list[dict], descriptor: dict) -> list[dict]:
        expanded = list(commands)
        host_enabled = descriptor.get("hostEnabled", G2S_CLASSES[:8])
        for cls in host_enabled:
            expanded.append({"class": cls, "command": "getDeviceStatus", "params": {"deviceId": self.adapter.device_id}})
            expanded.append({"class": cls, "command": "setDeviceState", "params": {"deviceId": self.adapter.device_id, "enabled": True}})
        return expanded


# ═══════════════════════════════════════════
# COMMAND GROUP EXECUTOR
# ═══════════════════════════════════════════
class CommandGroupExecutor:
    """Sends multiple G2S commands from the same class in one SOAP message."""
    def __init__(self, adapter: 'G2SAdapter'):
        self.adapter = adapter

    async def execute_group(self, g2s_class: str, commands: list[dict]) -> dict:
        logger.info(f"[G2S:{self.adapter.device_id}] Executing command group: {g2s_class} ({len(commands)} commands)")
        # Build grouped SOAP body
        body = {"class": g2s_class, "commands": commands, "groupId": str(uuid.uuid4())}
        await self.adapter._send_soap(g2s_class, "commandGroup", body)
        self.adapter._emit_trace({"channel": "soap", "direction": "out", "protocol": "G2S", "class": g2s_class, "command_count": len(commands), "type": "commandGroup"})
        return {"status": "sent", "class": g2s_class, "command_count": len(commands)}


# ═══════════════════════════════════════════
# PROXY CERTIFICATE — G2S_egmProxy
# ═══════════════════════════════════════════
G2S_ENTITY_TYPES = ["G2S_egm", "G2S_host", "G2S_egmProxy"]

def build_certificate_config(entity_type: str, common_name: str) -> dict:
    if entity_type not in G2S_ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")
    return {
        "subject": {"CN": common_name, "OU": entity_type, "O": "UGG Gaming Gateway"},
        "entity_type": entity_type,
        "is_proxy": entity_type == "G2S_egmProxy",
    }


# ═══════════════════════════════════════════
# G2S ADAPTER
# ═══════════════════════════════════════════
class G2SAdapter(ProtocolAdapter):
    def __init__(self, device_id: str):
        super().__init__(ProtocolType.G2S, device_id)
        self.config: dict = {}
        self.comms_handler = CommsDisabledHandler(self)
        self.startup_engine = StartupAlgorithmEngine(self)
        self.group_executor = CommandGroupExecutor(self)
        self.soap_client = None
        self.keepalive_task: Optional[asyncio.Task] = None
        self.keepalive_missed = 0
        self.last_event_at: Optional[str] = None
        self.message_count = 0
        self.schema_version = "2.1.0"
        self.entity_type = "G2S_host"

    async def connect(self, config: dict) -> None:
        self.config = config
        self.schema_version = config.get("schemaVersion", "2.1.0")
        self.entity_type = config.get("entityType", "G2S_host")
        self._set_state(ConnectionState.OPENING)

        egm_url = config.get("egmUrl")
        if egm_url:
            try:
                from zeep import AsyncClient
                self.soap_client = AsyncClient(egm_url)
                logger.info(f"[G2S:{self.device_id}] Connected to EGM SOAP endpoint: {egm_url}")
            except Exception as e:
                logger.warning(f"[G2S:{self.device_id}] SOAP client init failed ({e}), using virtual mode")
                self.soap_client = None

        # Simulate receiving commsOnLine from EGM
        self._emit_trace({"channel": "g2s", "direction": "in", "protocol": "G2S", "command": "commsOnLine", "class": "communications", "xml": f'<g2s:commsOnLine g2s:deviceId="G2S_{self.device_id}" g2s:g2sProtocol="{self.schema_version}"/>'})
        self._set_state(ConnectionState.SYNC)

        # Run startup algorithm
        descriptor = config.get("egmDescriptor", {"hostEnabled": G2S_CLASSES[:8]})
        self.startup_engine.mode = config.get("startupMode", "AUTO")
        self.startup_engine.verbose_mode = config.get("verboseMode", True)
        await self.startup_engine.run(descriptor)

        self._set_state(ConnectionState.ONLINE)
        # Start keepalive
        self.keepalive_task = asyncio.create_task(self._keepalive_loop())

    async def disconnect(self) -> None:
        self._set_state(ConnectionState.CLOSING)
        if self.keepalive_task:
            self.keepalive_task.cancel()
        # Send commsClosing
        await self._send_soap("communications", "commsClosing", {"deviceId": self.device_id})
        self._emit_trace({"channel": "g2s", "direction": "out", "protocol": "G2S", "command": "commsClosing", "class": "communications"})
        self._set_state(ConnectionState.CLOSED)

    async def _keepalive_loop(self):
        interval = self.config.get("keepAliveIntervalMs", 30000) / 1000.0
        missed_limit = self.config.get("keepAliveMissedLimit", 3)
        while self.state == ConnectionState.ONLINE:
            try:
                await asyncio.sleep(interval)
                response = await self._send_soap("communications", "keepAlive", {"deviceId": self.device_id})
                self._emit_trace({"channel": "g2s", "direction": "out", "protocol": "G2S", "command": "keepAlive", "class": "communications"})
                if response:
                    self.keepalive_missed = 0
                    self._emit_trace({"channel": "g2s", "direction": "in", "protocol": "G2S", "command": "keepAliveAck"})
                else:
                    self.keepalive_missed += 1
                    if self.keepalive_missed >= missed_limit:
                        logger.warning(f"[G2S:{self.device_id}] {missed_limit} keepalives missed — transitioning to LOST")
                        self._set_state(ConnectionState.LOST)
                        break
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.keepalive_missed += 1
                logger.error(f"[G2S:{self.device_id}] Keepalive error: {e}")

    async def _send_soap(self, g2s_class: str, command: str, params: dict = None) -> Optional[dict]:
        self.message_count += 1
        now = datetime.now(timezone.utc).isoformat()
        self.last_event_at = now

        # Build SOAP XML trace
        xml = f'<g2s:{command} g2s:deviceId="G2S_{self.device_id}"'
        if params:
            for k, v in params.items():
                xml += f' g2s:{k}="{v}"'
        xml += '/>'

        self._emit_trace({"channel": "soap", "direction": "out", "protocol": "G2S", "class": g2s_class, "command": command, "xml": xml, "timestamp": now})

        if self.soap_client:
            try:
                # Real SOAP call would go here
                pass
            except Exception as e:
                logger.error(f"[G2S:{self.device_id}] SOAP error: {e}")
                return None

        # Emit canonical event
        self._emit_event(CanonicalEvent(
            device_id=self.device_id, event_type="device_state",
            protocol="G2S", payload={"class": g2s_class, "command": command, "params": params or {}},
        ))
        return {"status": "ok", "command": command}

    async def poll_meters(self) -> list[dict]:
        await self._send_soap("meters", "getMeterInfo", {"deviceId": self.device_id})
        return []

    async def get_device_info(self) -> dict:
        return {"device_id": self.device_id, "protocol": "G2S", "state": self.state, "schema": self.schema_version, "entity_type": self.entity_type, "message_count": self.message_count, "keepalive_missed": self.keepalive_missed, "last_event_at": self.last_event_at}

    async def send_command(self, cmd: dict) -> dict:
        g2s_class = cmd.get("class", "cabinet")
        command = cmd.get("command", "setDeviceState")
        params = cmd.get("params", {})
        result = await self._send_soap(g2s_class, command, params)
        return result or {"status": "error"}

    def get_status(self) -> dict:
        return {
            "protocol": "G2S", "device_id": self.device_id, "state": self.state.value,
            "schema_version": self.schema_version, "entity_type": self.entity_type,
            "message_count": self.message_count, "keepalive_missed": self.keepalive_missed,
            "last_event_at": self.last_event_at, "comms_disabled_count": self.comms_handler.disabled_count,
        }
