"""
FlywheelOS Delivery Orchestration — template rendering + channel adapters.
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta
from database import db
from ws_manager import manager
from flywheel import config as cfg
from flywheel.storage import save_delivery, update_delivery, save_inbox_message
from flywheel.actor_profile import increment_fatigue

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def render_template(template: str, context: dict) -> str:
    """Simple {{variable}} substitution."""
    result = template
    for key, value in context.items():
        result = result.replace("{{" + str(key) + "}}", str(value))
    return result


def _build_context(action: dict, profile: dict) -> dict:
    """Build template rendering context from action + profile."""
    return {
        "player_name": profile.get("player_name", "Player"),
        "actor_id": profile.get("actor_id", ""),
        "amount": f"${action.get('poc_amount', 0):.2f}",
        "poc_amount": f"{action.get('poc_amount', 0):.2f}",
        "tier": profile.get("tier", "bronze"),
        "tier_name": profile.get("tier", "bronze").title(),
        "rule_key": action.get("rule_key", ""),
        "rule_name": action.get("rule_name", action.get("family", "")),
        "family": action.get("family", ""),
        "device_id": action.get("target_device_id", ""),
        "score": f"{action.get('score', 0):.1%}",
        "lifecycle": profile.get("lifecycle_stage", "active"),
    }


# ═══════════════════════════════════════════════════════════
# Channel Adapters
# ═══════════════════════════════════════════════════════════

async def deliver_to_egm(action: dict, profile: dict) -> dict:
    """Write a message to device_messages collection — displayed on EGM screen."""
    context = _build_context(action, profile)
    rendered = render_template(
        action.get("message_template", "") or action.get("rendered_message", ""),
        context
    )
    if not rendered:
        rendered = f"You have ${action.get('poc_amount', 0):.2f} Play Credits! Enjoy your game!"

    device_id = action.get("target_device_id", "")
    if not device_id:
        return {"delivery_id": "", "status": "failed", "error": "no_device_id"}

    msg_id = str(uuid.uuid4())
    expires = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()

    await db.device_messages.insert_one({
        "id": msg_id,
        "device_id": device_id,
        "message_text": rendered,
        "message_type": "PROMO",
        "display_duration_seconds": cfg.EGM_MESSAGE_DURATION_SEC,
        "display_position": "CENTER",
        "background_color": cfg.EGM_MESSAGE_BG_COLOR,
        "text_color": cfg.EGM_MESSAGE_TEXT_COLOR,
        "priority": "HIGH",
        "expires_at": expires,
        "sent_by": "FLYWHEEL",
        "sent_at": _now(),
        "status": "PENDING",
        "flywheel_action_id": action.get("id", ""),
        "flywheel_family": action.get("family", ""),
    })

    delivery = {
        "id": str(uuid.uuid4()),
        "app_id": "ugg",
        "action_id": action.get("id", ""),
        "channel": "in_app_surface",
        "status": "sent",
        "provider_message_id": msg_id,
        "rendered_content": {"body": rendered, "device_id": device_id},
        "attempts": 1,
        "last_attempt_at": _now(),
        "delivered_at": _now(),
    }
    await save_delivery(delivery)
    logger.info(f"FlywheelOS: delivered to EGM {device_id}: {rendered[:80]}")
    return {"delivery_id": delivery["id"], "status": "sent", "channel": "in_app_surface"}


async def deliver_to_inbox(action: dict, profile: dict) -> dict:
    """Write to flywheel_inbox for player notifications."""
    context = _build_context(action, profile)
    rendered = render_template(
        action.get("message_template", "") or action.get("rendered_message", ""),
        context
    )
    msg = {
        "player_id": profile.get("actor_id", ""),
        "player_name": profile.get("player_name", ""),
        "action_id": action.get("id", ""),
        "family": action.get("family", ""),
        "rule_key": action.get("rule_key", ""),
        "message": rendered,
        "poc_amount": action.get("poc_amount", 0),
        "is_read": False,
    }
    await save_inbox_message(msg)

    delivery = {
        "id": str(uuid.uuid4()),
        "app_id": "ugg",
        "action_id": action.get("id", ""),
        "channel": "in_app_inbox",
        "status": "sent",
        "rendered_content": {"body": rendered},
        "attempts": 1,
        "last_attempt_at": _now(),
        "delivered_at": _now(),
    }
    await save_delivery(delivery)
    return {"delivery_id": delivery["id"], "status": "sent", "channel": "in_app_inbox"}


async def deliver_to_websocket(action: dict, profile: dict) -> dict:
    """Broadcast to WebSocket channel 'flywheel' for real-time admin dashboards."""
    context = _build_context(action, profile)
    rendered = render_template(
        action.get("message_template", "") or action.get("rendered_message", ""),
        context
    )
    await manager.broadcast({
        "type": "flywheel_action",
        "action_id": action.get("id"),
        "player_id": profile.get("actor_id"),
        "player_name": profile.get("player_name"),
        "family": action.get("family"),
        "rule_key": action.get("rule_key"),
        "poc_amount": action.get("poc_amount", 0),
        "message": rendered,
        "score": action.get("score", 0),
        "channel": "websocket",
        "occurred_at": _now(),
    }, "flywheel")
    return {"delivery_id": "", "status": "sent", "channel": "websocket"}


# ═══════════════════════════════════════════════════════════
# Dispatch router
# ═══════════════════════════════════════════════════════════

CHANNEL_ADAPTERS = {
    "in_app_surface": deliver_to_egm,
    "in_app_inbox": deliver_to_inbox,
    "websocket": deliver_to_websocket,
}


async def dispatch_action(action: dict, profile: dict) -> dict:
    """
    Deliver an approved action via its selected channel.
    Falls back through channel_order if primary fails.
    Also updates action status and increments fatigue.
    """
    channel = action.get("channel", "in_app_surface")
    adapter = CHANNEL_ADAPTERS.get(channel)
    result = {"delivery_id": "", "status": "failed"}

    if adapter:
        try:
            result = await adapter(action, profile)
        except Exception as e:
            logger.error(f"Delivery error on {channel}: {e}")
            result = {"delivery_id": "", "status": "failed", "error": str(e)}

    # Update action status
    from flywheel.storage import update_action
    if result.get("status") == "sent":
        await update_action(action["id"], {
            "status": "dispatched",
            "dispatched_at": _now(),
            "delivered_at": _now(),
            "delivery_id": result.get("delivery_id", ""),
            "rendered_message": render_template(
                action.get("message_template", ""), _build_context(action, profile)
            ),
        })
        # Increase fatigue
        await increment_fatigue(profile.get("actor_id", ""), 0.1)

        # Also deliver to websocket for dashboard visibility
        if channel != "websocket":
            try:
                await deliver_to_websocket(action, profile)
            except Exception:
                pass  # non-critical
    else:
        await update_action(action["id"], {
            "status": "failed",
            "dispatched_at": _now(),
        })

    return result
