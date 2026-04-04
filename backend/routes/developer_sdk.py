"""
EGM Developer SDK — Downloadable integration packages, code samples,
JSON schemas, API reference, and integration test kits.
"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from database import db
from auth import get_current_user
import uuid
import json
import io
import zipfile
from datetime import datetime, timezone

router = APIRouter(prefix="/api/developer-sdk", tags=["developer-sdk"])

# ══════════════════════════════════════════════════
# EVENT SCHEMAS — JSON Schema definitions
# ══════════════════════════════════════════════════

UNIVERSAL_EVENT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "UGG Universal Game Event",
    "description": "The payload every EGM sends to UGG after each game outcome",
    "type": "object",
    "required": ["event_type", "game_type", "egm_id", "player_id"],
    "properties": {
        "event_type": {"type": "string", "enum": ["REEL_SPIN", "SCATTER_HIT", "BONUS_TRIGGERED", "BONUS_COMPLETED", "BONUS_RETRIGGER", "WILD_COMBINATION", "MEGA_WIN", "JACKPOT_WIN", "CONSECUTIVE_WINS", "CONSECUTIVE_LOSSES", "SYMBOL_COMBINATION", "MAX_BET_SPIN", "FEATURE_PICK", "STICKY_WILD", "MYSTERY_REVEAL", "GAMBLE_FEATURE", "MULTIPLIER_HIT", "HAND_RESULT", "KENO_RESULT", "SESSION_START", "SESSION_END", "SESSION_HEARTBEAT", "GAME_CHANGE", "DENOMINATION_CHANGE"]},
        "game_type": {"type": "string", "enum": ["SLOTS", "VIDEO_POKER", "KENO"]},
        "egm_id": {"type": "string", "description": "Unique device ID registered in UGG"},
        "player_id": {"type": "string", "description": "Player loyalty card ID (null if no card)"},
        "session_id": {"type": "string", "description": "Current play session UUID"},
        "game_theme": {"type": "string", "description": "Name of the game being played"},
        "denomination": {"type": "number", "description": "Base denomination in dollars (e.g., 0.25)"},
        "bet_amount": {"type": "number", "description": "Total bet for this game in dollars"},
        "win_amount": {"type": "number", "description": "Total win for this game in dollars (0 if loss)"},
        "win_multiplier": {"type": "number", "description": "Win as multiple of bet (e.g., 50 for 50x)"},
        "game_data": {"type": "object", "description": "Game-specific payload — varies by event_type and game_type"},
        "session_context": {
            "type": "object",
            "properties": {
                "session_duration_mins": {"type": "integer"},
                "session_coin_in": {"type": "number", "description": "Running total coin-in in cents"},
                "bonus_rounds_this_session": {"type": "integer"},
                "big_wins_this_session": {"type": "integer"},
                "wins_this_session": {"type": "integer"},
                "consecutive_wins": {"type": "integer"},
                "journey_steps_completed": {"type": "integer"},
                "journey_current_step": {"type": "integer"},
            },
        },
    },
}

SLOTS_GAME_DATA = {
    "SCATTER_HIT": {"scatter_count": "integer (3-5)", "scatter_positions": "array of reel positions"},
    "BONUS_TRIGGERED": {"bonus_type": "string (free_spins/pick/wheel)", "free_spins_awarded": "integer", "trigger_count_session": "integer"},
    "BONUS_COMPLETED": {"spins_used": "integer", "bonus_total_win": "number", "retrigger_occurred": "boolean"},
    "BONUS_RETRIGGER": {"retrigger_number": "integer", "new_spins_added": "integer"},
    "WILD_COMBINATION": {"payline_id": "integer", "wild_count": "integer", "win_amount": "number"},
    "MEGA_WIN": {"win_multiplier": "integer", "is_epic": "boolean (>100x)", "is_legendary": "boolean (>500x)"},
    "JACKPOT_WIN": {"jackpot_tier": "string (mini/minor/major/grand)", "amount": "number"},
    "CONSECUTIVE_WINS": {"streak_count": "integer", "cumulative_win": "number"},
    "FEATURE_PICK": {"pick_position": "integer", "reveal_type": "string", "reveal_value": "number", "is_top_prize": "boolean"},
    "STICKY_WILD": {"reel_position": "array [reel, row]", "spins_remaining": "integer"},
    "MYSTERY_REVEAL": {"revealed_symbol": "string", "positions": "array", "total_win": "number"},
    "MULTIPLIER_HIT": {"multiplier_value": "integer", "base_win": "number", "boosted_win": "number"},
}

VP_GAME_DATA = {
    "HAND_RESULT": {
        "hand_dealt": "array of 5 card codes (e.g., ['Ah','Kh','Qh','Jh','Th'])",
        "cards_held": "array of 5 booleans",
        "hand_drawn": "array of 5 final card codes",
        "hand_rank": "string enum (HIGH_CARD, JACKS_OR_BETTER, TWO_PAIR, THREE_OF_A_KIND, STRAIGHT, FLUSH, FULL_HOUSE, FOUR_OF_A_KIND, FOUR_ACES, STRAIGHT_FLUSH, NATURAL_ROYAL, ROYAL_FLUSH)",
        "hand_rank_code": "integer (100-900)",
        "is_natural": "boolean (no wilds used)",
        "wilds_used": "integer",
        "suit": "string (HEARTS/DIAMONDS/CLUBS/SPADES) for flushes",
        "game_variant": "string (JACKS_OR_BETTER, DEUCES_WILD, BONUS_POKER, etc.)",
        "coins_played": "integer (1-5)",
        "is_max_coins": "boolean",
        "cards_held_count": "integer (0-5)",
        "is_winner": "boolean",
    },
}

KENO_GAME_DATA = {
    "KENO_RESULT": {
        "spots_picked": "integer (1-20)",
        "numbers_picked": "array of integers (1-80)",
        "numbers_drawn": "array of 20 integers",
        "matches": "integer",
        "pay_table_hit": "string (e.g., '7_OF_8')",
        "is_solid_catch": "boolean (all picks matched)",
        "consecutive_wins": "integer",
        "first_ball_match": "boolean",
        "last_ball_match": "boolean",
        "progressive_hit": "boolean",
        "bonus_multiplier": "integer",
        "is_winner": "boolean",
    },
}


# ══════════════════════════════════════════════════
# CODE SAMPLES
# ══════════════════════════════════════════════════

CODE_SAMPLES = {
    "python": {
        "filename": "ugg_integration.py",
        "language": "Python",
        "content": '''"""UGG EGM Integration — Python SDK"""
import requests
import json
from datetime import datetime, timezone

UGG_URL = "https://your-ugg-server.com"
EGM_ID = "MY-EGM-001"

class UGGClient:
    def __init__(self, base_url, egm_id):
        self.base_url = base_url
        self.egm_id = egm_id
        self.session_id = None

    def send_event(self, event_type, game_type, player_id, game_data, session_context=None, bet=0, win=0):
        """Send a game event to UGG."""
        payload = {
            "event_type": event_type,
            "game_type": game_type,
            "egm_id": self.egm_id,
            "player_id": player_id,
            "session_id": self.session_id,
            "bet_amount": bet,
            "win_amount": win,
            "win_multiplier": round(win / bet, 1) if bet > 0 else 0,
            "game_data": game_data,
            "session_context": session_context or {},
        }
        # Send to gamification engine
        r = requests.post(f"{self.base_url}/api/gamification/event", json=payload)
        return r.json()

    def send_canonical_event(self, event_type, protocol="PROPRIETARY", payload=None):
        """Send a canonical event to UGG core."""
        data = {
            "device_id": self.egm_id,
            "event_type": event_type,
            "protocol": protocol,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "severity": "info",
            "payload": payload or {},
        }
        requests.post(f"{self.base_url}/api/events", json=data)

    def poll_messages(self):
        """Poll UGG for messages to display on the EGM screen."""
        r = requests.get(f"{self.base_url}/api/device-messages/poll/{self.egm_id}")
        data = r.json()
        return data.get("messages", [])

    def acknowledge_message(self, message_id):
        """Tell UGG the message was displayed."""
        requests.post(f"{self.base_url}/api/device-messages/displayed/{message_id}")

    def dismiss_message(self, message_id):
        """Tell UGG the player dismissed the message."""
        requests.post(f"{self.base_url}/api/device-messages/acknowledged/{message_id}")


# === USAGE EXAMPLES ===

client = UGGClient(UGG_URL, EGM_ID)

# Slots: Player hits 3 scatters
result = client.send_event(
    event_type="SCATTER_HIT",
    game_type="SLOTS",
    player_id="PL-12345",
    game_data={"scatter_count": 3, "scatter_positions": [1, 3, 5]},
    session_context={"session_duration_mins": 25, "session_coin_in": 5000, "wins_this_session": 8},
    bet=1.25, win=0
)
print(f"Achievements: {result.get('achievements', [])}")
print(f"Journey: {result.get('journey')}")
print(f"POC: ${result.get('poc_total', 0)}")

# Video Poker: Player hits Full House
result = client.send_event(
    event_type="HAND_RESULT",
    game_type="VIDEO_POKER",
    player_id="PL-12345",
    game_data={
        "hand_dealt": ["Ah", "As", "Kh", "Ks", "2d"],
        "cards_held": [True, True, True, True, False],
        "hand_drawn": ["Ah", "As", "Kh", "Ks", "Ad"],
        "hand_rank": "FULL_HOUSE",
        "hand_rank_code": 450,
        "is_natural": True,
        "coins_played": 5,
        "is_max_coins": True,
        "cards_held_count": 4,
        "is_winner": True,
    },
    bet=1.25, win=11.25
)

# Keno: Player catches 7 of 8
result = client.send_event(
    event_type="KENO_RESULT",
    game_type="KENO",
    player_id="PL-12345",
    game_data={
        "spots_picked": 8,
        "numbers_picked": [3, 7, 14, 22, 33, 41, 55, 68],
        "numbers_drawn": [7, 14, 22, 33, 41, 55, 68, 72, 80, 4],
        "matches": 7,
        "is_solid_catch": False,
        "first_ball_match": True,
        "consecutive_wins": 2,
        "is_winner": True,
    },
    bet=2.00, win=1500.00
)

# Poll and display messages every 30 seconds
messages = client.poll_messages()
for msg in messages:
    print(f"[{msg['type']}] {msg['text']}")
    # Display on EGM screen...
    client.acknowledge_message(msg["id"])
''',
    },
    "javascript": {
        "filename": "ugg_integration.js",
        "language": "JavaScript / Node.js",
        "content": '''// UGG EGM Integration — JavaScript SDK
const UGG_URL = "https://your-ugg-server.com";
const EGM_ID = "MY-EGM-001";

async function sendGameEvent(eventType, gameType, playerId, gameData, sessionCtx = {}, bet = 0, win = 0) {
  const resp = await fetch(`${UGG_URL}/api/gamification/event`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event_type: eventType, game_type: gameType, egm_id: EGM_ID,
      player_id: playerId, bet_amount: bet, win_amount: win,
      win_multiplier: bet > 0 ? Math.round(win / bet * 10) / 10 : 0,
      game_data: gameData, session_context: sessionCtx,
    }),
  });
  return resp.json();
}

async function pollMessages() {
  const resp = await fetch(`${UGG_URL}/api/device-messages/poll/${EGM_ID}`);
  const data = await resp.json();
  return data.messages || [];
}

async function displayMessage(msgId) {
  await fetch(`${UGG_URL}/api/device-messages/displayed/${msgId}`, { method: "POST" });
}

async function dismissMessage(msgId) {
  await fetch(`${UGG_URL}/api/device-messages/acknowledged/${msgId}`, { method: "POST" });
}

// === SLOTS EXAMPLE ===
const result = await sendGameEvent("SCATTER_HIT", "SLOTS", "PL-12345",
  { scatter_count: 3, scatter_positions: [1, 3, 5] },
  { session_duration_mins: 25, session_coin_in: 5000, wins_this_session: 8 },
  1.25, 0
);
console.log("Achievements:", result.achievements);
console.log("Journey:", result.journey);
console.log("POC:", result.poc_total);

// === MESSAGE LOOP (every 30 seconds) ===
setInterval(async () => {
  const messages = await pollMessages();
  for (const msg of messages) {
    showOnScreen(msg.text, msg.type, msg.duration_seconds, msg.position);
    await displayMessage(msg.id);
    setTimeout(() => dismissMessage(msg.id), msg.duration_seconds * 1000);
  }
}, 30000);
''',
    },
    "csharp": {
        "filename": "UGGIntegration.cs",
        "language": "C# / Unity",
        "content": '''// UGG EGM Integration — C# SDK (Unity Compatible)
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

public class UGGClient {
    private readonly HttpClient _http = new HttpClient();
    private readonly string _baseUrl;
    private readonly string _egmId;

    public UGGClient(string baseUrl, string egmId) {
        _baseUrl = baseUrl;
        _egmId = egmId;
    }

    public async Task<GameEventResult> SendGameEvent(string eventType, string gameType,
        string playerId, object gameData, object sessionContext = null, decimal bet = 0, decimal win = 0) {
        var payload = new {
            event_type = eventType, game_type = gameType, egm_id = _egmId,
            player_id = playerId, bet_amount = bet, win_amount = win,
            win_multiplier = bet > 0 ? Math.Round(win / bet, 1) : 0,
            game_data = gameData, session_context = sessionContext ?? new {},
        };
        var json = JsonConvert.SerializeObject(payload);
        var resp = await _http.PostAsync($"{_baseUrl}/api/gamification/event",
            new StringContent(json, Encoding.UTF8, "application/json"));
        var body = await resp.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject<GameEventResult>(body);
    }

    public async Task<Message[]> PollMessages() {
        var resp = await _http.GetStringAsync($"{_baseUrl}/api/device-messages/poll/{_egmId}");
        var data = JsonConvert.DeserializeObject<PollResponse>(resp);
        return data?.messages ?? Array.Empty<Message>();
    }
}

// Usage:
// var client = new UGGClient("https://your-ugg-server.com", "MY-EGM-001");
// var result = await client.SendGameEvent("SCATTER_HIT", "SLOTS", "PL-12345",
//     new { scatter_count = 3, scatter_positions = new[] {1,3,5} },
//     new { session_duration_mins = 25, wins_this_session = 8 }, 1.25m, 0m);
''',
    },
}

DEVICE_TEMPLATE_EXAMPLE = '''<?xml version="1.0" encoding="UTF-8"?>
<deviceTemplate version="1.0" manufacturer="YourBrand" model="GameKing-500" softwareVersion="2.1.0">
  <metadata>
    <serialNumber>SN-00001</serialNumber>
    <softwareSignature>sha256:abcdef1234567890</softwareSignature>
    <g2sSchemaVersion>G2S_2.1.0</g2sSchemaVersion>
  </metadata>
  <denominations active="true">
    <denom value="100"/>  <!-- $1.00 -->
    <denom value="500"/>  <!-- $5.00 -->
    <denom value="2500"/> <!-- $25.00 -->
  </denominations>
  <devices>
    <device class="G2S_cabinet" id="1" hostEnabled="true" egmEnabled="true"/>
    <device class="G2S_gamePlay" id="1" hostEnabled="true" egmEnabled="true"/>
    <device class="G2S_meters" id="1" hostEnabled="true" egmEnabled="true"/>
    <device class="G2S_noteAcceptor" id="1" hostEnabled="true" egmEnabled="true"/>
    <device class="G2S_voucher" id="1" hostEnabled="true" egmEnabled="true"/>
    <device class="G2S_handpay" id="1" hostEnabled="true" egmEnabled="true"/>
    <device class="G2S_eventHandler" id="1" hostEnabled="true" egmEnabled="true"/>
  </devices>
  <gameOutcomes>
    <wagerCategory id="1" name="BaseGame" minBet="100" maxBet="12500"/>
    <winLevel id="0" name="NoWin" probability="0.70" multiplier="0"/>
    <winLevel id="1" name="SmallWin" probability="0.20" multiplier="1.5"/>
    <winLevel id="2" name="MediumWin" probability="0.08" multiplier="5"/>
    <winLevel id="3" name="BigWin" probability="0.019" multiplier="25"/>
    <winLevel id="4" name="Jackpot" probability="0.001" multiplier="250"/>
  </gameOutcomes>
  <unsupportedEvents>
    <pattern>G2S_progressive*</pattern>
  </unsupportedEvents>
</deviceTemplate>'''


# ══════════════════════════════════════════════════
# API ENDPOINTS
# ══════════════════════════════════════════════════

@router.get("/schemas")
async def get_event_schemas():
    """Public — Get all JSON Schema definitions for UGG game events."""
    return {
        "universal_event": UNIVERSAL_EVENT_SCHEMA,
        "slots_game_data": SLOTS_GAME_DATA,
        "video_poker_game_data": VP_GAME_DATA,
        "keno_game_data": KENO_GAME_DATA,
        "event_types": UNIVERSAL_EVENT_SCHEMA["properties"]["event_type"]["enum"],
        "game_types": UNIVERSAL_EVENT_SCHEMA["properties"]["game_type"]["enum"],
    }


@router.get("/code-samples")
async def get_code_samples():
    """Public — Get integration code samples in all supported languages."""
    return {"samples": {k: {"filename": v["filename"], "language": v["language"], "lines": v["content"].count("\n")} for k, v in CODE_SAMPLES.items()}, "languages": list(CODE_SAMPLES.keys())}


@router.get("/code-samples/{language}")
async def get_code_sample(language: str):
    """Public — Get a specific code sample."""
    sample = CODE_SAMPLES.get(language)
    if not sample:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"No sample for '{language}'. Available: {list(CODE_SAMPLES.keys())}")
    return sample


@router.get("/device-template-example")
async def get_device_template():
    """Public — Get the Device Template XML example."""
    return {"xml": DEVICE_TEMPLATE_EXAMPLE, "format": "XML", "description": "Device Template for the UGG Emulator Lab. Customize for your EGM model."}


@router.get("/api-reference")
async def get_api_reference():
    """Public — Complete API reference for EGM developers."""
    return {"endpoints": [
        {"method": "POST", "path": "/api/gamification/event", "description": "THE MAIN ENDPOINT — Send a game event. UGG evaluates achievements, advances journey, awards POC, and returns display messages.", "auth": "None (device authenticates via egm_id)", "request_body": "Universal Game Event Payload", "response": "achievements[], journey progress, messages[], poc_total"},
        {"method": "GET", "path": "/api/device-messages/poll/{device_id}", "description": "Poll for pending messages to display on EGM screen. Call every 30 seconds.", "auth": "None", "response": "messages[] with id, text, type, duration, position, colors"},
        {"method": "POST", "path": "/api/device-messages/displayed/{message_id}", "description": "Tell UGG a message is showing on screen.", "auth": "None"},
        {"method": "POST", "path": "/api/device-messages/acknowledged/{message_id}", "description": "Tell UGG the player dismissed the message.", "auth": "None"},
        {"method": "POST", "path": "/api/gamification/journey/generate", "description": "Generate a Session Journey for a player on card-in.", "auth": "Bearer token", "request_body": "{player_id, game_type}"},
        {"method": "POST", "path": "/api/gamification/journey/advance", "description": "Check if an event advances the player's journey.", "auth": "Bearer token"},
        {"method": "GET", "path": "/api/gamification/achievements", "description": "List all achievements in the library.", "auth": "Bearer token", "params": "game_type, category"},
        {"method": "GET", "path": "/api/gamification/journey-steps", "description": "List all journey step definitions.", "auth": "Bearer token"},
        {"method": "GET", "path": "/api/developer-sdk/schemas", "description": "Get JSON Schema definitions for all event payloads.", "auth": "None"},
    ]}


@router.get("/download-sdk")
async def download_sdk_zip(request: Request):
    """Download the complete Developer SDK as a ZIP file."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.md", """# UGG Developer SDK
## Quick Start
1. Choose your language (Python, JavaScript, or C#)
2. Copy the integration file to your project
3. Update UGG_URL and EGM_ID with your values
4. Start sending game events after every spin/hand/draw
5. Poll for messages every 30 seconds and display them

## Files Included
- schemas/universal_event.json — JSON Schema for all events
- schemas/slots_game_data.json — Slots-specific game_data fields
- schemas/video_poker_game_data.json — Video Poker game_data fields
- schemas/keno_game_data.json — Keno game_data fields
- samples/ugg_integration.py — Python SDK with full examples
- samples/ugg_integration.js — JavaScript/Node.js SDK
- samples/UGGIntegration.cs — C#/Unity SDK
- templates/device_template.xml — Device Template XML example
- docs/api_reference.md — Complete API reference
- docs/gamification_events.md — All event types with example payloads
""")
        # Schemas
        zf.writestr("schemas/universal_event.json", json.dumps(UNIVERSAL_EVENT_SCHEMA, indent=2))
        zf.writestr("schemas/slots_game_data.json", json.dumps(SLOTS_GAME_DATA, indent=2))
        zf.writestr("schemas/video_poker_game_data.json", json.dumps(VP_GAME_DATA, indent=2))
        zf.writestr("schemas/keno_game_data.json", json.dumps(KENO_GAME_DATA, indent=2))

        # Code samples
        for lang, sample in CODE_SAMPLES.items():
            zf.writestr(f"samples/{sample['filename']}", sample["content"])

        # Device template
        zf.writestr("templates/device_template.xml", DEVICE_TEMPLATE_EXAMPLE)

        # API Reference doc
        api_ref = """# UGG API Reference for EGM Developers

## Main Endpoint: POST /api/gamification/event
Send after EVERY game outcome (spin, hand, draw).

### Request Body:
```json
{
  "event_type": "SCATTER_HIT",
  "game_type": "SLOTS",
  "egm_id": "YOUR-EGM-ID",
  "player_id": "PLAYER-CARD-ID",
  "bet_amount": 1.25,
  "win_amount": 0,
  "game_data": { "scatter_count": 3 },
  "session_context": { "session_duration_mins": 25, "wins_this_session": 8 }
}
```

### Response:
```json
{
  "achievements": [{"code": "ACH_S_SCATTER_FIRST", "name": "Scatter Awakening", "poc": 3}],
  "journey": {"step_completed": 2, "poc": 5, "progress": "2/6"},
  "messages": [{"type": "MSG_ACHIEVEMENT", "text": "ACHIEVEMENT: Scatter Awakening! $3.00 POC!"}],
  "poc_total": 8
}
```

## Message Polling: GET /api/device-messages/poll/{device_id}
Call every 30 seconds. No authentication needed.

## Message Lifecycle:
1. Poll returns messages with status PENDING
2. POST /displayed/{id} when message appears on screen
3. POST /acknowledged/{id} when player dismisses or timer expires

## Event Types by Game:
### Slots: SCATTER_HIT, BONUS_TRIGGERED, BONUS_COMPLETED, BONUS_RETRIGGER, WILD_COMBINATION, MEGA_WIN, JACKPOT_WIN, CONSECUTIVE_WINS, FEATURE_PICK, STICKY_WILD, MYSTERY_REVEAL, MULTIPLIER_HIT
### Video Poker: HAND_RESULT (with hand_rank, cards_held, etc.)
### Keno: KENO_RESULT (with matches, spots_picked, etc.)
### All Games: SESSION_START, SESSION_END, SESSION_HEARTBEAT
"""
        zf.writestr("docs/api_reference.md", api_ref)

        # Gamification events doc
        events_doc = "# UGG Gamification Event Types\n\n"
        events_doc += "## Slots Events\n"
        for evt, fields in SLOTS_GAME_DATA.items():
            events_doc += f"\n### {evt}\n"
            for field, desc in fields.items():
                events_doc += f"- **{field}**: {desc}\n"
        events_doc += "\n## Video Poker Events\n"
        for evt, fields in VP_GAME_DATA.items():
            events_doc += f"\n### {evt}\n"
            for field, desc in fields.items():
                events_doc += f"- **{field}**: {desc}\n"
        events_doc += "\n## Keno Events\n"
        for evt, fields in KENO_GAME_DATA.items():
            events_doc += f"\n### {evt}\n"
            for field, desc in fields.items():
                events_doc += f"- **{field}**: {desc}\n"
        zf.writestr("docs/gamification_events.md", events_doc)

    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=ugg_developer_sdk_v1.0.zip"})
