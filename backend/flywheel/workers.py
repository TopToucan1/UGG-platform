"""
FlywheelOS Background Workers — 6 async periodic tasks.
"""
import asyncio
import uuid
import logging
from datetime import datetime, timezone
from database import db
from flywheel import config as cfg
from flywheel.storage import save_execution_log, update_execution_log

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _log_start(worker_name: str) -> str:
    log_id = str(uuid.uuid4())
    await save_execution_log({
        "id": log_id, "app_id": "ugg", "worker_name": worker_name,
        "started_at": _now(), "status": "running",
    })
    return log_id


async def _log_end(log_id: str, items: int, errors: int, summary: str, error_details: str = ""):
    status = "completed" if errors == 0 else "failed"
    await update_execution_log(log_id, {
        "ended_at": _now(), "status": status,
        "items_processed": items, "errors": errors,
        "summary": summary, "error_details": error_details or None,
    })


class FlywheelWorkers:
    def __init__(self):
        self._tasks: list[asyncio.Task] = []
        self._running = False
        self._paused = False
        self._last_run: dict[str, str] = {}

    async def start(self):
        self._running = True
        self._tasks = [
            asyncio.create_task(self._loop("profile_updater", cfg.WORKER_PROFILE_UPDATER, self._profile_updater)),
            asyncio.create_task(self._loop("scheduled_rule_runner", cfg.WORKER_SCHEDULED_RUNNER, self._scheduled_rule_runner)),
            asyncio.create_task(self._loop("action_dispatcher", cfg.WORKER_ACTION_DISPATCHER, self._action_dispatcher)),
            asyncio.create_task(self._loop("delivery_reconciler", cfg.WORKER_DELIVERY_RECONCILER, self._delivery_reconciler)),
            asyncio.create_task(self._loop("segment_evaluator", cfg.WORKER_SEGMENT_EVALUATOR, self._segment_evaluator)),
            asyncio.create_task(self._loop("score_computer", cfg.WORKER_SCORE_COMPUTER, self._score_computer)),
        ]
        logger.info("FlywheelOS: all 6 workers started")

    async def stop(self):
        self._running = False
        for t in self._tasks:
            t.cancel()
        logger.info("FlywheelOS: workers stopped")

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def status(self) -> list[dict]:
        names = ["profile_updater", "scheduled_rule_runner", "action_dispatcher",
                 "delivery_reconciler", "segment_evaluator", "score_computer"]
        return [{"name": n, "running": self._running and not self._paused,
                 "last_run": self._last_run.get(n), "scheduled": self._running}
                for n in names]

    async def run_one(self, worker_name: str) -> dict:
        """Run a single worker immediately."""
        handlers = {
            "profile_updater": self._profile_updater,
            "scheduled_rule_runner": self._scheduled_rule_runner,
            "action_dispatcher": self._action_dispatcher,
            "delivery_reconciler": self._delivery_reconciler,
            "segment_evaluator": self._segment_evaluator,
            "score_computer": self._score_computer,
        }
        handler = handlers.get(worker_name)
        if not handler:
            return {"error": f"Unknown worker: {worker_name}"}
        log_id = await _log_start(worker_name)
        try:
            items, summary = await handler()
            await _log_end(log_id, items, 0, summary)
            self._last_run[worker_name] = _now()
            return {"status": "completed", "items": items, "summary": summary}
        except Exception as e:
            await _log_end(log_id, 0, 1, "failed", str(e))
            return {"status": "failed", "error": str(e)}

    async def _loop(self, name: str, interval: int, handler):
        """Generic worker loop with execution logging."""
        await asyncio.sleep(15)  # initial delay to let startup finish
        while self._running:
            if self._paused:
                await asyncio.sleep(5)
                continue
            log_id = await _log_start(name)
            try:
                items, summary = await handler()
                await _log_end(log_id, items, 0, summary)
                self._last_run[name] = _now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                await _log_end(log_id, 0, 1, "error", str(e))
                logger.error(f"FlywheelOS worker {name} error: {e}")
            await asyncio.sleep(interval)

    # ─── Worker implementations ───

    async def _profile_updater(self) -> tuple[int, str]:
        """Recompute lifecycle, fatigue for recently active players."""
        from flywheel.actor_profile import recompute_profile
        # Find players with recent pin_sessions
        cutoff = (datetime.now(timezone.utc) - __import__("datetime").timedelta(minutes=10)).isoformat()
        recent = await db.pin_sessions.find(
            {"started_at": {"$gte": cutoff}}, {"_id": 0, "player_id": 1}
        ).to_list(500)
        player_ids = list({r["player_id"] for r in recent if r.get("player_id")})
        # Also include players with flywheel profiles marked stale
        stale = await db.flywheel_profiles.find(
            {"updated_at": {"$lt": cutoff}}, {"_id": 0, "actor_id": 1}
        ).limit(200).to_list(200)
        player_ids.extend([s["actor_id"] for s in stale if s.get("actor_id") not in player_ids])
        for pid in player_ids:
            await recompute_profile(pid)
        return len(player_ids), f"Recomputed {len(player_ids)} profiles"

    async def _scheduled_rule_runner(self) -> tuple[int, str]:
        """Evaluate scheduled rules for eligible players."""
        from flywheel.rule_engine import evaluate_scheduled
        from flywheel.decision_engine import decide
        from flywheel.delivery import dispatch_action
        from flywheel.reward_ledger import create_reward
        from flywheel.actor_profile import get_actor_profile
        from flywheel.storage import save_action

        # Target at_risk and dormant players
        profiles = await db.flywheel_profiles.find(
            {"lifecycle_stage": {"$in": ["at_risk", "dormant", "new"]}},
            {"_id": 0}
        ).limit(200).to_list(200)
        actions_created = 0
        for fp in profiles:
            profile = await get_actor_profile(fp["actor_id"])
            candidates = await evaluate_scheduled(profile)
            if not candidates:
                continue
            action = await decide(candidates, profile)
            if not action:
                continue
            await save_action(action)
            if action.get("poc_amount", 0) > 0:
                await create_reward(action, profile)
            if action.get("immediate", False):
                await dispatch_action(action, profile)
            actions_created += 1
        return actions_created, f"Scheduled rules generated {actions_created} actions"

    async def _action_dispatcher(self) -> tuple[int, str]:
        """Deliver approved non-immediate actions."""
        from flywheel.storage import get_pending_actions
        from flywheel.delivery import dispatch_action
        from flywheel.actor_profile import get_actor_profile

        pending = await get_pending_actions(50)
        dispatched = 0
        for action in pending:
            profile = await get_actor_profile(action["actor_id"])
            await dispatch_action(action, profile)
            dispatched += 1
        return dispatched, f"Dispatched {dispatched} actions"

    async def _delivery_reconciler(self) -> tuple[int, str]:
        """Check delivery status and advance reward lifecycle."""
        # Find flywheel device_messages that are still PENDING
        pending = await db.device_messages.find(
            {"sent_by": "FLYWHEEL", "status": "PENDING"},
            {"_id": 0}
        ).limit(100).to_list(100)
        reconciled = 0
        for msg in pending:
            # In a real system, check device acknowledgment. For now, auto-advance.
            await db.device_messages.update_one(
                {"id": msg["id"]}, {"$set": {"status": "DELIVERED"}}
            )
            # Advance linked reward to settled
            action_id = msg.get("flywheel_action_id")
            if action_id:
                await db.poc_awards.update_one(
                    {"flywheel_action_id": action_id, "flywheel_status": "pending"},
                    {"$set": {"flywheel_status": "settled", "delivery_status": "delivered"}}
                )
            reconciled += 1
        return reconciled, f"Reconciled {reconciled} deliveries"

    async def _segment_evaluator(self) -> tuple[int, str]:
        """Batch recompute lifecycle segments for all known players."""
        from flywheel.actor_profile import recompute_profile
        all_profiles = await db.flywheel_profiles.find({}, {"_id": 0, "actor_id": 1}).to_list(5000)
        count = 0
        for p in all_profiles:
            await recompute_profile(p["actor_id"])
            count += 1
        return count, f"Recomputed segments for {count} players"

    async def _score_computer(self) -> tuple[int, str]:
        """Recompute affinity vectors from session history."""
        # Query pin_sessions to build game-type affinity per player
        pipeline = [
            {"$match": {"player_id": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": "$player_id",
                "session_count": {"$sum": 1},
                "total_coin_in": {"$sum": "$coin_in"},
                "total_games": {"$sum": "$games_played"},
                "avg_duration": {"$avg": {"$subtract": [
                    {"$dateFromString": {"dateString": {"$ifNull": ["$ended_at", _now()]}}},
                    {"$dateFromString": {"dateString": "$started_at"}},
                ]}},
            }},
        ]
        try:
            results = await db.pin_sessions.aggregate(pipeline).to_list(5000)
        except Exception:
            results = []
        count = 0
        for r in results:
            player_id = r["_id"]
            if not player_id:
                continue
            await db.flywheel_profiles.update_one(
                {"actor_id": player_id},
                {"$set": {
                    "affinity_vectors": {
                        "total_sessions": r.get("session_count", 0),
                        "total_coin_in": r.get("total_coin_in", 0),
                        "total_games": r.get("total_games", 0),
                    },
                    "session_count": r.get("session_count", 0),
                    "updated_at": _now(),
                }},
                upsert=True,
            )
            count += 1
        return count, f"Computed scores for {count} players"
