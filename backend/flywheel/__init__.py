"""
FlywheelOS Engine — the orchestrator that wires event mapper, rules, decisions,
delivery, and rewards into the UGG gateway_core pipeline.

Usage:
    from flywheel import flywheel_engine
    pipeline.add_processor(flywheel_engine.process_pipeline_event)
    await flywheel_engine.start()
"""
import logging
from database import db
from flywheel.event_mapper import map_event
from flywheel.actor_profile import get_actor_profile
from flywheel.rule_engine import evaluate_event, load_default_rules
from flywheel.decision_engine import decide
from flywheel.delivery import dispatch_action
from flywheel.reward_ledger import create_reward
from flywheel.storage import save_action, save_event, ensure_indexes
from flywheel.workers import FlywheelWorkers

logger = logging.getLogger(__name__)


class FlywheelEngine:
    def __init__(self):
        self.workers = FlywheelWorkers()
        self._enabled = True
        self._started = False

    async def start(self):
        """Initialize indexes, load default rules, start workers."""
        await ensure_indexes()
        await load_default_rules()
        await self.workers.start()
        self._started = True
        logger.info("FlywheelOS engine started")

    async def stop(self):
        await self.workers.stop()
        self._started = False
        logger.info("FlywheelOS engine stopped")

    async def process_pipeline_event(self, event: dict):
        """
        Custom processor for gateway_core pipeline.
        Called after all standard stages (store, twin, session, exception, meter, broadcast, audit).
        """
        if not self._enabled or not self._started:
            return

        try:
            # 1. Map UGG event to FlywheelOS event
            fw_event = await map_event(event)
            if not fw_event:
                return

            # 2. Store flywheel event
            await save_event(fw_event)

            # 3. Only evaluate rules for identified players
            actor_id = fw_event.get("actor_id")
            if not actor_id or fw_event.get("actor_type") != "player":
                return

            # 4. Get merged actor profile
            profile = await get_actor_profile(actor_id)

            # 5. Evaluate event-triggered rules
            candidates = await evaluate_event(fw_event, profile)
            if not candidates:
                return

            # 6. Score and decide NBA
            action = await decide(candidates, profile)
            if not action:
                return

            # 7. Persist approved action
            await save_action(action)

            # 8. Create reward if action has POC
            if action.get("poc_amount", 0) > 0:
                await create_reward(action, profile)

            # 9. Dispatch immediately if flagged
            if action.get("immediate", False):
                await dispatch_action(action, profile)

        except Exception as e:
            logger.error(f"FlywheelOS pipeline processor error: {e}", exc_info=True)

    def get_status(self) -> dict:
        return {
            "enabled": self._enabled,
            "started": self._started,
            "workers": self.workers.status(),
        }


# Singleton
flywheel_engine = FlywheelEngine()
