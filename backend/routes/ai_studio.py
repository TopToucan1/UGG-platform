from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import os
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-studio", tags=["ai-studio"])


async def call_gemini(prompt: str, system_msg: str = None) -> str:
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="LLM key not configured")

    chat = LlmChat(
        api_key=api_key,
        session_id=f"ugg-studio-{uuid.uuid4().hex[:8]}",
        system_message=system_msg or "You are an expert gaming systems integration engineer helping with UGG (Universal Gaming Gateway) platform. You help map source system data to canonical UGG event formats."
    )
    chat.with_model("gemini", "gemini-3-flash-preview")
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    return response


@router.post("/discover")
async def discover_source(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    source_type = body.get("source_type", "rest_api")
    source_description = body.get("description", "")
    sample_data = body.get("sample_data", "")

    prompt = f"""Analyze this gaming system data source and provide discovery results:

Source Type: {source_type}
Description: {source_description}
Sample Data: {sample_data}

Provide a JSON response with:
1. "detected_fields": array of objects with "name", "type", "sample_value", "description"
2. "suggested_event_mappings": array of objects with "source_field", "canonical_event_type", "confidence" (0-1), "reasoning"
3. "suggested_command_mappings": array of objects with "canonical_command", "implementation_notes"
4. "warnings": array of strings for any concerns
5. "summary": brief analysis summary

Return ONLY valid JSON, no markdown code blocks."""

    try:
        result = await call_gemini(prompt)
        # Try to parse as JSON
        import json
        try:
            parsed = json.loads(result.strip().replace("```json", "").replace("```", "").strip())
        except json.JSONDecodeError:
            parsed = {"raw_response": result, "summary": "AI analysis completed - see raw response"}

        # Store the discovery session
        session = {
            "id": str(uuid.uuid4()),
            "source_type": source_type,
            "description": source_description,
            "sample_data": sample_data,
            "ai_result": parsed,
            "status": "completed",
            "created_by": user.get("email"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.ai_studio_sessions.insert_one(session)
        session.pop("_id", None)
        return session
    except Exception as e:
        logger.error(f"AI Studio discovery error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest-mapping")
async def suggest_mapping(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    source_fields = body.get("source_fields", [])
    target_schema = body.get("target_schema", "canonical_event")

    prompt = f"""Given these source fields from a gaming device system:
{source_fields}

Map them to the UGG canonical event schema. The canonical event fields are:
- event_type (e.g., device.game.start, device.game.end, device.door.opened, device.meter.changed, etc.)
- device_id, tenant_id, site_id
- occurred_at (timestamp)
- payload (JSON with event-specific data)
- severity (info, warning, critical)
- source_protocol
- integrity_hash

Provide JSON with:
1. "mappings": array of {{ "source_field", "canonical_field", "transform" (if needed), "confidence" (0-1) }}
2. "unmapped_fields": source fields that don't have a clear canonical mapping
3. "missing_required": canonical fields without a source mapping
4. "suggested_transforms": any data transformation code snippets needed

Return ONLY valid JSON."""

    try:
        result = await call_gemini(prompt)
        import json
        try:
            parsed = json.loads(result.strip().replace("```json", "").replace("```", "").strip())
        except json.JSONDecodeError:
            parsed = {"raw_response": result}
        return {"mappings": parsed, "status": "completed"}
    except Exception as e:
        logger.error(f"AI mapping suggestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-connector")
async def generate_connector(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    connector_name = body.get("name", "New Connector")
    source_type = body.get("source_type", "rest_poll")
    mappings = body.get("mappings", {})
    description = body.get("description", "")

    prompt = f"""Generate a UGG connector manifest for:
Name: {connector_name}
Source Type: {source_type}
Description: {description}
Field Mappings: {mappings}

Generate a complete connector manifest in JSON format with:
1. "manifest": the full manifest document with field_mappings, command_bindings, polling_config, error_handling
2. "connector_code": a Python code skeleton for the connector implementation
3. "test_scenarios": suggested emulator test scenarios for this connector
4. "deployment_notes": deployment and configuration notes

Return ONLY valid JSON."""

    try:
        result = await call_gemini(prompt)
        import json
        try:
            parsed = json.loads(result.strip().replace("```json", "").replace("```", "").strip())
        except json.JSONDecodeError:
            parsed = {"raw_response": result}
        return {"generated": parsed, "status": "completed", "requires_approval": True}
    except Exception as e:
        logger.error(f"AI connector generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(request: Request, limit: int = 20):
    await get_current_user(request)
    sessions = await db.ai_studio_sessions.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"sessions": sessions}


@router.post("/chat")
async def studio_chat(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    message = body.get("message", "")
    context = body.get("context", "")

    system_msg = """You are the UGG AI Studio assistant. You help gaming system integrators:
- Understand gaming protocols (SAS, G2S)
- Map source data to canonical UGG events
- Debug connector issues
- Write connector code
- Design emulator test scenarios
Be concise and technical. Reference UGG canonical event types when relevant."""

    prompt = f"{context}\n\nUser: {message}" if context else message

    try:
        result = await call_gemini(prompt, system_msg)
        # Store chat
        chat_record = {
            "id": str(uuid.uuid4()),
            "user_message": message,
            "ai_response": result,
            "context": context,
            "created_by": user.get("email"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.ai_studio_chats.insert_one(chat_record)
        chat_record.pop("_id", None)
        return chat_record
    except Exception as e:
        logger.error(f"AI Studio chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
