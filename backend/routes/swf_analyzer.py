from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from database import db
from auth import get_current_user
import uuid
import struct
import zlib
from datetime import datetime, timezone

router = APIRouter(prefix="/api/swf-analyzer", tags=["swf-analyzer"])

# Canonical event mapping suggestions for discovered identifiers
IDENTIFIER_MAPPINGS = {
    "score": {"canonical": "device.game.end", "field": "payload.win", "confidence": 0.8},
    "bonus": {"canonical": "device.bonus.triggered", "field": "payload.bonus_amount", "confidence": 0.85},
    "jackpot": {"canonical": "device.jackpot.handpay", "field": "payload.jackpot_amount", "confidence": 0.9},
    "card_in": {"canonical": "device.player.card.in", "field": "payload.player_id", "confidence": 0.95},
    "card_out": {"canonical": "device.player.card.out", "field": "payload.player_id", "confidence": 0.95},
    "balance": {"canonical": "device.meter.changed", "field": "payload.credit_balance", "confidence": 0.7},
    "coin": {"canonical": "device.meter.changed", "field": "payload.coin_in", "confidence": 0.75},
    "credit": {"canonical": "device.meter.changed", "field": "payload.credits", "confidence": 0.7},
    "spin": {"canonical": "device.game.start", "field": "payload.game_cycle", "confidence": 0.85},
    "reel": {"canonical": "device.game.start", "field": "payload.reel_config", "confidence": 0.7},
    "symbol": {"canonical": "device.game.end", "field": "payload.result_symbols", "confidence": 0.75},
    "pay": {"canonical": "device.game.end", "field": "payload.payout", "confidence": 0.8},
    "line": {"canonical": "device.game.start", "field": "payload.paylines", "confidence": 0.6},
    "bet": {"canonical": "device.game.start", "field": "payload.bet_amount", "confidence": 0.85},
    "win": {"canonical": "device.game.end", "field": "payload.win_amount", "confidence": 0.9},
    "play": {"canonical": "device.game.start", "field": "event_type", "confidence": 0.6},
    "game": {"canonical": "device.game.start", "field": "event_type", "confidence": 0.5},
    "button": {"canonical": "device.game.start", "field": "payload.user_action", "confidence": 0.4},
    "voucher": {"canonical": "device.voucher.out", "field": "payload.voucher_amount", "confidence": 0.85},
    "tilt": {"canonical": "device.tilt", "field": "payload.tilt_code", "confidence": 0.9},
    "door": {"canonical": "device.door.opened", "field": "payload.door_type", "confidence": 0.85},
    "meter": {"canonical": "device.meter.changed", "field": "payload.meter_value", "confidence": 0.9},
    "disable": {"canonical": "device.remote.disabled", "field": "event_type", "confidence": 0.8},
    "enable": {"canonical": "device.status.online", "field": "event_type", "confidence": 0.7},
    "offer": {"canonical": "device.bonus.triggered", "field": "payload.offer_type", "confidence": 0.6},
    "level": {"canonical": "device.player.card.in", "field": "payload.tier_level", "confidence": 0.5},
    "service": {"canonical": "device.health.check", "field": "payload.service_type", "confidence": 0.5},
}

GAME_CATEGORIES = {
    "slot": ["reel", "spin", "symbol", "line", "payline", "scatter", "wild"],
    "bonus": ["bonus", "free", "pick", "wheel", "multiplier"],
    "player_tracking": ["card", "player", "balance", "level", "offer", "pin", "loyalty"],
    "financial": ["coin", "credit", "bet", "win", "pay", "jackpot", "voucher", "meter", "score"],
    "system": ["button", "menu", "service", "command", "door", "tilt", "disable", "enable"],
}


def parse_swf(data: bytes) -> dict:
    """Parse an SWF file and extract metadata + ActionScript strings."""
    if len(data) < 8:
        raise ValueError("File too small to be SWF")

    sig = data[:3].decode('ascii', errors='replace')
    if sig not in ('CWS', 'FWS', 'ZWS'):
        raise ValueError(f"Not a valid SWF file (signature: {sig})")

    version = data[3]
    file_length = struct.unpack_from('<I', data, 4)[0]
    compressed = sig == 'CWS'
    zws = sig == 'ZWS'

    if compressed:
        try:
            body = zlib.decompress(data[8:])
        except zlib.error as e:
            raise ValueError(f"Failed to decompress CWS: {e}")
    elif zws:
        raise ValueError("LZMA-compressed SWF not supported")
    else:
        body = data[8:]

    # Extract readable strings (4+ chars)
    strings = []
    current = b''
    for byte in body:
        if 32 <= byte < 127:
            current += bytes([byte])
        else:
            if len(current) >= 4:
                strings.append(current.decode('ascii', errors='replace'))
            current = b''
    if len(current) >= 4:
        strings.append(current.decode('ascii', errors='replace'))

    # Deduplicate and filter
    unique = list(dict.fromkeys(strings))
    meaningful = [s for s in unique if len(s) >= 4 and not s.startswith('#') and not all(c in '0123456789' for c in s)]

    # Classify identifiers
    identifiers = []
    for s in meaningful:
        sl = s.lower()
        for keyword, mapping in IDENTIFIER_MAPPINGS.items():
            if keyword in sl:
                identifiers.append({
                    "raw_string": s,
                    "keyword_match": keyword,
                    "suggested_canonical_event": mapping["canonical"],
                    "suggested_field": mapping["field"],
                    "confidence": mapping["confidence"],
                })
                break

    # Categorize content
    categories_found = {}
    for cat, keywords in GAME_CATEGORIES.items():
        matches = []
        for s in meaningful:
            sl = s.lower()
            for kw in keywords:
                if kw in sl:
                    matches.append(s)
                    break
        if matches:
            categories_found[cat] = matches[:10]

    # Detect fonts
    fonts = [s for s in meaningful if any(f in s for f in ['Helvetica', 'Arial', 'Times', 'Verdana', 'Georgia', 'Font', 'Bold', 'Italic', 'Light', 'Black'])]

    # Detect ActionScript patterns
    as_patterns = [s for s in meaningful if any(p in s for p in ['_root.', 'function', 'FSCommand', 'setInterval', 'clearInterval', 'onEnterFrame', 'gotoAndPlay', 'gotoAndStop', 'MovieClip', 'addEventListener'])]

    # Detect copyright/attribution
    copyrights = [s for s in meaningful if 'copyright' in s.lower() or '(c)' in s.lower()]

    return {
        "signature": sig,
        "version": version,
        "compressed": compressed,
        "compressed_size": len(data),
        "uncompressed_size": file_length,
        "total_strings": len(meaningful),
        "identifiers": identifiers,
        "categories": categories_found,
        "fonts": fonts[:10],
        "actionscript_patterns": as_patterns[:20],
        "copyrights": copyrights[:5],
        "all_strings_sample": meaningful[:100],
    }


@router.post("/analyze")
async def analyze_swf(request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    contents = await file.read()

    try:
        analysis = parse_swf(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Store analysis
    record = {
        "id": str(uuid.uuid4()),
        "filename": file.filename or "unknown.swf",
        "file_size": len(contents),
        "swf_version": analysis["version"],
        "compressed": analysis["compressed"],
        "uncompressed_size": analysis["uncompressed_size"],
        "total_strings": analysis["total_strings"],
        "identifiers_count": len(analysis["identifiers"]),
        "categories": list(analysis["categories"].keys()),
        "fonts": analysis["fonts"],
        "copyrights": analysis["copyrights"],
        "analyzed_by": user.get("email"),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.swf_analyses.insert_one(record)
    record.pop("_id", None)

    return {
        **record,
        "identifiers": analysis["identifiers"],
        "categories": analysis["categories"],
        "actionscript_patterns": analysis["actionscript_patterns"],
        "all_strings_sample": analysis["all_strings_sample"],
        "suggested_mappings": [
            {"source": ident["raw_string"], "canonical_event": ident["suggested_canonical_event"], "canonical_field": ident["suggested_field"], "confidence": ident["confidence"]}
            for ident in sorted(analysis["identifiers"], key=lambda x: -x["confidence"])
        ],
    }


@router.get("/analyses")
async def list_analyses(request: Request, limit: int = 50):
    await get_current_user(request)
    analyses = await db.swf_analyses.find({}, {"_id": 0}).sort("analyzed_at", -1).limit(limit).to_list(limit)
    return {"analyses": analyses, "total": await db.swf_analyses.count_documents({})}


@router.post("/hex-dump")
async def hex_dump(request: Request, file: UploadFile = File(...), offset: int = 0, length: int = 512):
    await get_current_user(request)
    contents = await file.read()
    chunk = contents[offset:offset + length]
    hex_lines = []
    for i in range(0, len(chunk), 16):
        row = chunk[i:i + 16]
        hex_part = ' '.join(f'{b:02x}' for b in row)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
        hex_lines.append({"offset": f"{offset + i:08x}", "hex": hex_part, "ascii": ascii_part})
    return {"hex_dump": hex_lines, "total_size": len(contents), "offset": offset, "length": len(chunk)}
