"""
FlywheelOS Configuration — constants, thresholds, scoring weights, worker intervals.
All values are tunable per deployment. Override via flywheel_config collection.
"""

# ── Scoring weights (must sum to ~1.0 before fatigue penalty) ──
SCORE_W_PRIORITY = 0.25
SCORE_W_RELEVANCE = 0.25
SCORE_W_URGENCY = 0.20
SCORE_W_CHANNEL = 0.15
SCORE_W_TIER = 0.15
SCORE_FATIGUE_MULT = 0.30       # fatigue_score * this = penalty
SCORE_MIN_THRESHOLD = 0.10      # discard candidates below this

# ── Policy defaults ──
GLOBAL_DAILY_CAP = 5            # max actions per player per day
DEFAULT_QUIET_HOURS_START = None # no quiet hours for 24/7 gaming (set to hour int if needed)
DEFAULT_QUIET_HOURS_END = None

# ── Rule defaults ──
LOSS_RECOVERY_MIN_LOSS = 20.0   # minimum net loss to trigger loss_recovery
MILESTONE_THRESHOLDS = [100, 250, 500, 1000, 2500]  # coin-in milestones in dollars
MILESTONE_PROXIMITY_PCT = 0.10  # within 10% triggers milestone_proximity
RE_ENTRY_DORMANT_DAYS = 7       # days absent before re_entry fires
RE_ENTRY_POC_BASE = 10.0        # base POC for re_entry (before tier multiplier)
SESSION_EXTENSION_MINUTES = 45  # min session length for extension offer
COLD_STREAK_GAMES = 20          # games without a win triggers cold_streak_comfort
SOCIAL_PROOF_WIN_COUNT = 3      # recent wins at site to trigger social_proof
GROUP_MOMENTUM_THRESHOLD = 0.20 # 20% increase in site play volume

# ── Delivery ──
EGM_MESSAGE_DURATION_SEC = 15   # how long POC offer shows on EGM screen
EGM_MESSAGE_BG_COLOR = "#00D97E"
EGM_MESSAGE_TEXT_COLOR = "#FFFFFF"

# ── Reward idempotency ──
REWARD_AUTO_SETTLE = True       # auto-advance pending→settled (no manual verification in v1)

# ── Worker intervals (seconds) ──
WORKER_PROFILE_UPDATER = 60
WORKER_SCHEDULED_RUNNER = 120
WORKER_ACTION_DISPATCHER = 10
WORKER_DELIVERY_RECONCILER = 300
WORKER_SEGMENT_EVALUATOR = 3600
WORKER_SCORE_COMPUTER = 1800

# ── Lifecycle stage thresholds ──
LIFECYCLE_NEW_MAX_VISITS = 3
LIFECYCLE_POWER_MIN_EVENTS_WEEK = 5
LIFECYCLE_POWER_RECENCY_DAYS = 7
LIFECYCLE_AT_RISK_LAPSE_MIN = 50
LIFECYCLE_AT_RISK_CHURN_MAX = 35
LIFECYCLE_DORMANT_DAYS = 30
LIFECYCLE_RESURRECTED_WINDOW_DAYS = 7

# ── Event families ──
EVENT_FAMILIES = [
    "interest_view", "interest_follow", "progress_start", "progress_advance",
    "commitment", "competition_loss", "competition_win", "resource_gain",
    "resource_spend", "share", "return_visit", "conversion", "negative_signal",
]
