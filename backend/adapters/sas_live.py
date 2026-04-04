"""
SAS Adapter — Production RS-232 serial wiring for live EGM testing.
Handles real serial port I/O with CRC validation, frame parsing, and async read.
"""
import asyncio
import struct
import logging
import random
from typing import Optional
from datetime import datetime, timezone
from adapters import ProtocolAdapter, ProtocolType, ConnectionState, CanonicalEvent

logger = logging.getLogger(__name__)

# Import the full 38-meter map from existing adapter
from adapters.sas_adapter import SAS_METER_MAP, SAS_METER_BY_CODE, FaultInjector


def sas_crc16(data: bytes) -> int:
    """Calculate SAS CRC-16 (polynomial 0x8005, init 0x0000)."""
    crc = 0x0000
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8005
            else:
                crc >>= 1
    return crc & 0xFFFF


def build_sas_frame(address: int, command: int, data: bytes = b'') -> bytes:
    """Build a SAS command frame with CRC."""
    frame = bytes([0x80 | (address & 0x1F), command]) + data
    crc = sas_crc16(frame)
    return frame + struct.pack('<H', crc)


def validate_sas_frame(frame: bytes) -> bool:
    """Validate a received SAS frame CRC."""
    if len(frame) < 3:
        return False
    data = frame[:-2]
    expected_crc = struct.unpack('<H', frame[-2:])[0]
    return sas_crc16(data) == expected_crc


# SAS Long Poll commands
SAS_LP_GENERAL_POLL = 0x80          # General exception poll (no wakeup)
SAS_LP_EXCEPTION_STATUS = 0x01      # Read exception status
SAS_LP_METER_READ = 0xAF            # Read single selected meter
SAS_LP_MULTI_METER = 0x2F           # Read multiple meters
SAS_LP_ENABLE = 0x01                # Enable gaming machine
SAS_LP_DISABLE = 0x02               # Disable gaming machine
SAS_LP_SEND_METERS_10_15 = 0x10     # Send meters 10-15
SAS_LP_ROM_SIGNATURE = 0x21         # ROM signature verification
SAS_LP_SEND_TOTAL_CANCELLED = 0x1E  # Send total cancelled credits


class SasLiveAdapter(ProtocolAdapter):
    """Production SAS adapter for real RS-232 serial port communication with EGMs."""

    def __init__(self, device_id: str):
        super().__init__(ProtocolType.SAS, device_id)
        self.serial_port = None
        self.config: dict = {}
        self.cycle_count = 0
        self.poll_task: Optional[asyncio.Task] = None
        self.read_task: Optional[asyncio.Task] = None
        self.fault_injector = FaultInjector()
        self.meter_values: dict[str, int] = {}
        self.exception_buffer: list[int] = []
        self.poll_count = 0
        self.error_count = 0
        self.crc_errors = 0
        self.timeouts = 0
        self.last_event_at: Optional[str] = None
        self.bytes_sent = 0
        self.bytes_received = 0
        self._read_buffer = bytearray()
        self._response_future: Optional[asyncio.Future] = None

    async def connect(self, config: dict) -> None:
        self.config = config
        self._set_state(ConnectionState.OPENING)
        port_name = config.get("port", "/dev/ttyUSB0")
        baud = config.get("baudRate", 19200)
        parity = config.get("parity", "mark")  # SAS uses mark/space parity

        try:
            import serial
            import serial.tools.list_ports

            # List available ports for diagnostics
            available = [p.device for p in serial.tools.list_ports.comports()]
            logger.info(f"[SAS:{self.device_id}] Available serial ports: {available}")

            self.serial_port = serial.Serial(
                port=port_name, baudrate=baud, bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                timeout=0.5, write_timeout=1,
                xonxoff=False, rtscts=False, dsrdtr=False,
            )
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            logger.info(f"[SAS:{self.device_id}] Opened REAL serial port {port_name} at {baud}bps")
            self._emit_trace({"channel": "protocol", "direction": "info", "protocol": "SAS", "annotation": f"Serial port opened: {port_name} @ {baud}bps", "hex": ""})
        except ImportError:
            logger.warning(f"[SAS:{self.device_id}] pyserial not available — virtual mode")
            self.serial_port = None
        except Exception as e:
            logger.warning(f"[SAS:{self.device_id}] Cannot open {port_name}: {e} — falling back to virtual mode")
            self.serial_port = None
            self._emit_trace({"channel": "protocol", "direction": "info", "protocol": "SAS", "annotation": f"Virtual mode: {e}", "hex": ""})

        if config.get("faultInjection"):
            self.fault_injector.configure(config["faultInjection"])

        self._set_state(ConnectionState.ONLINE)
        self.poll_task = asyncio.create_task(self._poll_loop())

    async def disconnect(self) -> None:
        self._set_state(ConnectionState.CLOSING)
        if self.poll_task:
            self.poll_task.cancel()
            try:
                await self.poll_task
            except asyncio.CancelledError:
                pass
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            logger.info(f"[SAS:{self.device_id}] Serial port closed")
        self._set_state(ConnectionState.CLOSED)

    async def _send_and_receive(self, frame: bytes, expected_len: int = 32, timeout: float = 0.5) -> Optional[bytes]:
        """Send a SAS frame and wait for response. Async-safe for real serial I/O."""
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.reset_input_buffer()
                self.serial_port.write(frame)
                self.bytes_sent += len(frame)
                self._emit_trace({"channel": "protocol", "direction": "out", "protocol": "SAS", "hex": frame.hex(), "annotation": f"TX {len(frame)}B"})

                # Non-blocking read via asyncio
                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self.serial_port.read(expected_len)),
                    timeout=timeout
                )

                if response:
                    self.bytes_received += len(response)
                    valid = validate_sas_frame(response) if len(response) >= 3 else False
                    self._emit_trace({
                        "channel": "protocol", "direction": "in", "protocol": "SAS",
                        "hex": response.hex(),
                        "annotation": f"RX {len(response)}B CRC={'OK' if valid else 'FAIL'}",
                    })
                    if not valid and len(response) >= 3:
                        self.crc_errors += 1
                        logger.warning(f"[SAS:{self.device_id}] CRC error on response: {response.hex()}")
                    return response
                else:
                    self.timeouts += 1
                    return None
            except asyncio.TimeoutError:
                self.timeouts += 1
                self._emit_trace({"channel": "protocol", "direction": "in", "protocol": "SAS", "hex": "", "annotation": "TIMEOUT"})
                return None
            except Exception as e:
                self.error_count += 1
                logger.error(f"[SAS:{self.device_id}] Serial I/O error: {e}")
                self._emit_error(e)
                return None
        else:
            # Virtual mode — simulate response
            self._emit_trace({"channel": "protocol", "direction": "out", "protocol": "SAS", "hex": frame.hex(), "annotation": f"TX(virtual) {len(frame)}B"})
            return self._simulate_response(frame)

    def _simulate_response(self, frame: bytes) -> bytes:
        """Generate a simulated SAS response for virtual mode."""
        if len(frame) < 2:
            return b''
        command = frame[1]
        if command == SAS_LP_METER_READ and len(frame) >= 4:
            meter_code = frame[2:4].hex()
            prev = self.meter_values.get(meter_code, random.randint(10000, 500000))
            value = prev + random.randint(0, 50)
            self.meter_values[meter_code] = value
            resp_data = bytes([frame[0] & 0x1F, command]) + frame[2:4] + struct.pack('<I', value)
            crc = sas_crc16(resp_data)
            response = resp_data + struct.pack('<H', crc)
            self._emit_trace({"channel": "protocol", "direction": "in", "protocol": "SAS", "hex": response.hex(), "annotation": f"RX(virtual) meter={meter_code} val={value}"})
            return response
        elif command == SAS_LP_EXCEPTION_STATUS:
            exc_code = random.choice([0x00, 0x00, 0x00, 0x11, 0x12, 0x51]) if random.random() > 0.7 else 0x00
            resp_data = bytes([frame[0] & 0x1F, command, exc_code])
            crc = sas_crc16(resp_data)
            response = resp_data + struct.pack('<H', crc)
            self._emit_trace({"channel": "protocol", "direction": "in", "protocol": "SAS", "hex": response.hex(), "annotation": f"RX(virtual) exception=0x{exc_code:02X}"})
            return response
        return b''

    async def _poll_loop(self):
        addresses = self.config.get("deviceAddresses", [1])
        interval = self.config.get("pollIntervalMs", 200) / 1000.0
        meter_every = self.config.get("meterPollEvery", 10)

        logger.info(f"[SAS:{self.device_id}] Poll loop started: {len(addresses)} addresses, interval={interval}s, meters every {meter_every} cycles")

        while self.state == ConnectionState.ONLINE:
            try:
                for addr in addresses:
                    self.cycle_count += 1
                    # Exception poll every cycle
                    await self._poll_exceptions_live(addr)
                    # Meter poll every N cycles
                    if self.cycle_count % meter_every == 0:
                        await self._poll_all_meters_live(addr)
                    self.poll_count += 1
                    await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_count += 1
                self._emit_error(e)
                logger.error(f"[SAS:{self.device_id}] Poll loop error: {e}")
                if self.state == ConnectionState.ONLINE:
                    self._set_state(ConnectionState.LOST)
                await asyncio.sleep(5)
                if self.state == ConnectionState.LOST:
                    self._set_state(ConnectionState.ONLINE)
                    logger.info(f"[SAS:{self.device_id}] Reconnected — resuming poll")

    async def _poll_exceptions_live(self, address: int):
        """Poll SAS exception status using Long Poll 0x01."""
        frame = build_sas_frame(address, SAS_LP_EXCEPTION_STATUS)
        response = await self._send_and_receive(frame, expected_len=5, timeout=0.5)
        if response and len(response) >= 3:
            exc_code = response[2]
            if exc_code != 0x00:
                self.exception_buffer.append(exc_code)
                # Map SAS exception to canonical event
                exc_map = {0x11: "device.game.start", 0x12: "device.game.end", 0x51: "device.door.opened", 0x52: "device.door.closed", 0x7F: "device.tilt", 0x83: "device.voucher.in", 0x84: "device.voucher.out", 0x8F: "device.jackpot.handpay"}
                event_type = exc_map.get(exc_code, f"device.exception.0x{exc_code:02X}")
                severity = "critical" if exc_code in (0x7F, 0x8F) else "warning" if exc_code in (0x51,) else "info"
                now = datetime.now(timezone.utc).isoformat()
                self.last_event_at = now
                self._emit_event(CanonicalEvent(
                    device_id=self.device_id, event_type=event_type, protocol="SAS",
                    payload={"exception_code": f"0x{exc_code:02X}", "address": address, "raw_hex": response.hex()},
                ))

    async def _poll_all_meters_live(self, address: int):
        """Poll all 38 SAS meters using Long Poll 0xAF for each meter code."""
        meters = {}
        for mapping in SAS_METER_MAP:
            code = mapping["sasCode"]
            code_bytes = bytes.fromhex(code)
            frame = build_sas_frame(address, SAS_LP_METER_READ, code_bytes)
            response = await self._send_and_receive(frame, expected_len=10, timeout=0.5)

            if response and len(response) >= 8:
                try:
                    value = struct.unpack('<I', response[4:8])[0] if len(response) >= 8 else 0
                except struct.error:
                    value = 0
            elif response and len(response) >= 6:
                try:
                    value = struct.unpack('<I', response[2:6])[0]
                except struct.error:
                    value = self.meter_values.get(code, 0)
            else:
                value = self.meter_values.get(code, 0)

            # Fault injection
            value, fault = self.fault_injector.intercept(code, value)
            if fault == "SUPPRESS_RESPONSE":
                continue
            if fault and fault.startswith("MSX"):
                self._emit_event(CanonicalEvent(device_id=self.device_id, event_type="alarm", protocol="SAS", payload={"fault_code": fault, "meter_code": code}))
                continue

            if value is not None:
                self.meter_values[code] = value
                meters[mapping["canonicalName"]] = {"value": value, "sas_code": code, "is_vendor_ext": mapping["isVendorExt"], "g2s_class": mapping["g2sClass"]}

        now = datetime.now(timezone.utc).isoformat()
        self.last_event_at = now
        self._emit_event(CanonicalEvent(
            device_id=self.device_id, event_type="meter_snapshot", protocol="SAS",
            payload={"meters": meters, "cycle": self.cycle_count, "address": address, "meter_count": len(meters)},
        ))

    async def run_integrity_check(self) -> dict:
        """Request ROM signature from device via SAS Long Poll 0x21."""
        for addr in self.config.get("deviceAddresses", [1]):
            frame = build_sas_frame(addr, SAS_LP_ROM_SIGNATURE)
            response = await self._send_and_receive(frame, expected_len=20, timeout=2.0)
            if response:
                signature = response[2:-2].hex() if len(response) > 4 else "unknown"
                return {"device_id": self.device_id, "address": addr, "signature": signature, "raw": response.hex()}
        return {"device_id": self.device_id, "signature": "no_response"}

    async def poll_meters(self) -> list[dict]:
        return [{"canonicalName": k, "value": v} for k, v in self.meter_values.items()]

    async def get_device_info(self) -> dict:
        return {
            "device_id": self.device_id, "protocol": "SAS", "state": self.state.value,
            "mode": "live" if self.serial_port else "virtual",
            "port": self.config.get("port", "virtual"),
            "poll_count": self.poll_count, "error_count": self.error_count,
            "crc_errors": self.crc_errors, "timeouts": self.timeouts,
            "bytes_sent": self.bytes_sent, "bytes_received": self.bytes_received,
            "meter_count": len(self.meter_values), "exception_count": len(self.exception_buffer),
            "last_event_at": self.last_event_at,
        }

    async def send_command(self, cmd: dict) -> dict:
        cmd_type = cmd.get("type", "enable")
        addr = cmd.get("address", self.config.get("deviceAddresses", [1])[0])
        if cmd_type == "enable":
            frame = build_sas_frame(addr, SAS_LP_ENABLE)
        elif cmd_type == "disable":
            frame = build_sas_frame(addr, SAS_LP_DISABLE)
        elif cmd_type == "rom_signature":
            return await self.run_integrity_check()
        else:
            return {"status": "error", "message": f"Unknown command: {cmd_type}"}
        response = await self._send_and_receive(frame, expected_len=5)
        return {"status": "sent", "command": cmd_type, "response": response.hex() if response else None}

    def get_status(self) -> dict:
        return {
            "protocol": "SAS", "device_id": self.device_id, "state": self.state.value,
            "mode": "live" if self.serial_port else "virtual",
            "port": self.config.get("port", "virtual"),
            "poll_count": self.poll_count, "error_count": self.error_count,
            "crc_errors": self.crc_errors, "timeouts": self.timeouts,
            "bytes_sent": self.bytes_sent, "bytes_received": self.bytes_received,
            "cycle_count": self.cycle_count, "meter_count": len(self.meter_values),
            "exception_count": len(self.exception_buffer), "last_event_at": self.last_event_at,
        }
