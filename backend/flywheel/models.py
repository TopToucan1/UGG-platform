"""
FlywheelOS Data Models — Pydantic models for all domain entities.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FlywheelEvent(BaseModel):
    id: str = ""
    app_id: str = "ugg"
    tenant_id: str = ""
    actor_id: str = ""
    actor_type: str = "player"          # "player" | "device"
    event_family: str = ""              # one of 13 families
    event_name: str = ""                # original UGG event_type
    object_id: str = ""                 # session_id, device_id, etc.
    object_type: str = ""               # "credit_session", "device", etc.
    object_category: str = ""
    value: float = 0.0
    properties: dict = Field(default_factory=dict)
    source_event_id: str = ""
    occurred_at: str = ""
    received_at: str = ""


class ActorProfile(BaseModel):
    actor_id: str
    player_name: str = ""
    lifecycle_stage: str = "new"        # new/active/power/at_risk/dormant/resurrected
    churn_score: float = 50.0           # from PIRS (0-100)
    churn_risk: float = 0.5             # 1 - (churn_score / 100)
    tier: str = "bronze"
    tier_multiplier: float = 1.0
    lapse_risk: float = 0.0             # from PIRS (0-100)
    fatigue_score: float = 0.0          # 0.0-1.0, higher = more fatigued
    affinity_vectors: dict = Field(default_factory=dict)  # {game_type: weight, ...}
    lifetime_value: float = 0.0         # coin_in_lifetime
    last_action_at: Optional[str] = None
    actions_today: int = 0
    suppressed_until: Optional[str] = None
    opted_in_channels: list = Field(default_factory=lambda: ["in_app_surface", "in_app_inbox"])
    days_since_last_visit: int = 0
    visits_30d: int = 0
    session_count: int = 0
    events_last_7_days: int = 0
    last_device_id: Optional[str] = None
    updated_at: str = ""


class FlywheelRule(BaseModel):
    id: str = ""
    app_id: str = "ugg"
    key: str                            # unique stable identifier
    name: str = ""
    family: str                         # rule family (loss_recovery, etc.)
    trigger_type: str = "event"         # "event" | "scheduled" | "manual"
    trigger_events: list = Field(default_factory=list)   # EventFamily values
    cron_interval_seconds: int = 0      # for scheduled rules
    audience_lifecycle: list = Field(default_factory=list)  # lifecycle stages eligible
    audience_min_churn: float = 0.0
    audience_max_churn: float = 100.0
    scoring: dict = Field(default_factory=lambda: {
        "base_priority": 0.5,
        "urgency": 0.5,
        "relevance_weight": 0.5,
    })
    poc_base: float = 0.0               # base POC amount (before tier multiplier)
    message_template: str = ""
    channel_order: list = Field(default_factory=lambda: ["in_app_surface", "in_app_inbox"])
    frequency_cap_hours: float = 24.0   # per-user per-rule cooldown
    max_per_day: int = 1
    priority: int = 50                  # 0-100, higher = more important
    enabled: bool = True
    metadata: dict = Field(default_factory=dict)


class ActionCandidate(BaseModel):
    id: str = ""
    actor_id: str
    rule_id: str = ""
    rule_key: str = ""
    family: str = ""
    event_id: str = ""                  # triggering flywheel event
    object_id: str = ""
    target_device_id: str = ""
    poc_amount: float = 0.0             # before tier multiplier
    message_template: str = ""
    score: float = 0.0
    score_components: dict = Field(default_factory=dict)
    urgency: float = 0.5
    relevance: float = 0.5
    channel: str = "in_app_surface"
    immediate: bool = True              # deliver now vs. via worker
    created_at: str = ""
    expires_at: str = ""


class FlywheelAction(BaseModel):
    id: str = ""
    app_id: str = "ugg"
    actor_id: str
    rule_id: str = ""
    rule_key: str = ""
    family: str = ""
    action_type: str = "poc_award"      # "poc_award" | "message" | "badge"
    poc_amount: float = 0.0             # after tier multiplier
    message_template: str = ""
    rendered_message: str = ""
    target_device_id: Optional[str] = None
    channel: str = "in_app_surface"
    score: float = 0.0
    score_components: dict = Field(default_factory=dict)
    status: str = "approved"            # candidate/approved/dispatched/delivered/completed/rejected/expired
    immediate: bool = True
    source_event_id: str = ""
    policies_passed: list = Field(default_factory=list)
    policies_blocked_by: Optional[str] = None
    decision_rationale: str = ""
    created_at: str = ""
    dispatched_at: Optional[str] = None
    delivered_at: Optional[str] = None
    delivery_id: Optional[str] = None


class FlywheelDelivery(BaseModel):
    id: str = ""
    app_id: str = "ugg"
    action_id: str = ""
    channel: str = ""
    status: str = "pending"             # pending/sent/delivered/failed
    provider_message_id: str = ""
    rendered_content: dict = Field(default_factory=dict)
    attempts: int = 0
    last_attempt_at: Optional[str] = None
    delivered_at: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = ""


class ExecutionLog(BaseModel):
    id: str = ""
    app_id: str = "ugg"
    worker_name: str
    started_at: str = ""
    ended_at: Optional[str] = None
    status: str = "running"             # running/completed/failed
    items_processed: int = 0
    errors: int = 0
    summary: str = ""
    error_details: Optional[str] = None
