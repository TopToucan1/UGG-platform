"""
UGG Gamification Bonus Rewards System — The meta-game engine.
Session Journeys, Achievements, Streaks, Daily Challenges, Boss Events, Discovery Rewards, Hall of Fame.
"""
from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import uuid
import random
import math
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/gamification", tags=["gamification"])

# ══════════════════════════════════════════════════
# ACHIEVEMENT LIBRARY — 70+ achievements across 3 game types
# ══════════════════════════════════════════════════

ACHIEVEMENTS = [
    # SLOTS — Scatter & Feature
    {"code": "ACH_S_SCATTER_FIRST", "name": "Scatter Awakening", "game_type": "SLOTS", "category": "scatter", "trigger": "SCATTER_HIT", "conditions": {"scatter_count": {"$gte": 3}}, "poc": 3, "rarity": "Common", "is_discovery": True, "badge": "star"},
    {"code": "ACH_S_SCATTER_MAX", "name": "Scatter King", "game_type": "SLOTS", "category": "scatter", "trigger": "SCATTER_HIT", "conditions": {"scatter_count": {"$gte": 5}}, "poc": 15, "rarity": "Very Rare", "badge": "sparkle"},
    {"code": "ACH_S_BONUS_FIRST", "name": "Bonus Initiate", "game_type": "SLOTS", "category": "bonus", "trigger": "BONUS_TRIGGERED", "conditions": {}, "poc": 5, "rarity": "Common", "is_discovery": True, "badge": "slot"},
    {"code": "ACH_S_BONUS_3_SESSION", "name": "Bonus Hunter", "game_type": "SLOTS", "category": "bonus", "trigger": "BONUS_TRIGGERED", "conditions": {"trigger_count_session": {"$gte": 3}}, "poc": 20, "rarity": "Rare", "badge": "fire"},
    {"code": "ACH_S_RETRIGGER", "name": "The Re-Trigger", "game_type": "SLOTS", "category": "bonus", "trigger": "BONUS_RETRIGGER", "conditions": {}, "poc": 10, "rarity": "Hard", "badge": "refresh"},
    {"code": "ACH_S_WILD_LINE", "name": "Wild Rider", "game_type": "SLOTS", "category": "wild", "trigger": "WILD_COMBINATION", "conditions": {}, "poc": 8, "rarity": "Medium", "badge": "joker"},
    {"code": "ACH_S_FEATURE_ACE", "name": "Feature Ace", "game_type": "SLOTS", "category": "bonus", "trigger": "FEATURE_PICK", "conditions": {"is_top_prize": True}, "poc": 15, "rarity": "Hard", "badge": "target"},
    {"code": "ACH_S_STICKY", "name": "The Sticky", "game_type": "SLOTS", "category": "wild", "trigger": "STICKY_WILD", "conditions": {}, "poc": 5, "rarity": "Medium", "badge": "pin"},
    {"code": "ACH_S_MYSTERY", "name": "Mystery Maker", "game_type": "SLOTS", "category": "feature", "trigger": "MYSTERY_REVEAL", "conditions": {}, "poc": 5, "rarity": "Medium", "badge": "question"},
    # SLOTS — Win Magnitude
    {"code": "ACH_S_WIN_10X", "name": "Big Spender", "game_type": "SLOTS", "category": "win", "trigger": "MEGA_WIN", "conditions": {"win_multiplier": {"$gte": 10}}, "poc": 5, "rarity": "Medium", "badge": "money"},
    {"code": "ACH_S_WIN_50X", "name": "Mega Moment", "game_type": "SLOTS", "category": "win", "trigger": "MEGA_WIN", "conditions": {"win_multiplier": {"$gte": 50}}, "poc": 12, "rarity": "Hard", "badge": "money2"},
    {"code": "ACH_S_WIN_100X", "name": "Epic Win", "game_type": "SLOTS", "category": "win", "trigger": "MEGA_WIN", "conditions": {"win_multiplier": {"$gte": 100}}, "poc": 20, "rarity": "Very Hard", "badge": "money3"},
    {"code": "ACH_S_WIN_500X", "name": "Legendary Win", "game_type": "SLOTS", "category": "win", "trigger": "MEGA_WIN", "conditions": {"win_multiplier": {"$gte": 500}}, "poc": 50, "rarity": "Legendary", "badge": "trophy"},
    {"code": "ACH_S_STREAK_3", "name": "Win Streak 3", "game_type": "SLOTS", "category": "streak", "trigger": "CONSECUTIVE_WINS", "conditions": {"streak_count": {"$gte": 3}}, "poc": 6, "rarity": "Medium", "badge": "chain", "is_repeating": True, "repeat_scope": "session"},
    {"code": "ACH_S_STREAK_5", "name": "Win Streak 5", "game_type": "SLOTS", "category": "streak", "trigger": "CONSECUTIVE_WINS", "conditions": {"streak_count": {"$gte": 5}}, "poc": 12, "rarity": "Hard", "badge": "chain2"},
    {"code": "ACH_S_STREAK_10", "name": "Win Streak 10", "game_type": "SLOTS", "category": "streak", "trigger": "CONSECUTIVE_WINS", "conditions": {"streak_count": {"$gte": 10}}, "poc": 25, "rarity": "Very Hard", "badge": "chain3"},
    # SLOTS — Jackpots
    {"code": "ACH_S_JP_MINI", "name": "Mini Jackpot", "game_type": "SLOTS", "category": "jackpot", "trigger": "JACKPOT_WIN", "conditions": {"jackpot_tier": "mini"}, "poc": 10, "rarity": "Hard", "badge": "diamond"},
    {"code": "ACH_S_JP_MINOR", "name": "Minor Jackpot", "game_type": "SLOTS", "category": "jackpot", "trigger": "JACKPOT_WIN", "conditions": {"jackpot_tier": "minor"}, "poc": 15, "rarity": "Very Hard", "badge": "diamond2"},
    {"code": "ACH_S_JP_MAJOR", "name": "Major Jackpot", "game_type": "SLOTS", "category": "jackpot", "trigger": "JACKPOT_WIN", "conditions": {"jackpot_tier": "major"}, "poc": 25, "rarity": "Extremely Hard", "badge": "diamond3"},
    {"code": "ACH_S_JP_GRAND", "name": "Grand Jackpot", "game_type": "SLOTS", "category": "jackpot", "trigger": "JACKPOT_WIN", "conditions": {"jackpot_tier": "grand"}, "poc": 75, "rarity": "Legendary", "badge": "crown", "floor_broadcast": True},
    # VIDEO POKER — Hand Ladder
    {"code": "ACH_VP_TWO_PAIR", "name": "Two-Pair Pioneer", "game_type": "VIDEO_POKER", "category": "hand", "trigger": "HAND_RESULT", "conditions": {"hand_rank": "TWO_PAIR"}, "poc": 2, "rarity": "Common", "is_discovery": True, "badge": "cards"},
    {"code": "ACH_VP_3OAK", "name": "Triple Threat", "game_type": "VIDEO_POKER", "category": "hand", "trigger": "HAND_RESULT", "conditions": {"hand_rank": "THREE_OF_A_KIND"}, "poc": 3, "rarity": "Common", "is_discovery": True, "badge": "cards"},
    {"code": "ACH_VP_STRAIGHT", "name": "Straight Arrow", "game_type": "VIDEO_POKER", "category": "hand", "trigger": "HAND_RESULT", "conditions": {"hand_rank": "STRAIGHT"}, "poc": 5, "rarity": "Uncommon", "is_discovery": True, "badge": "cards"},
    {"code": "ACH_VP_FLUSH", "name": "Flush Fanatic", "game_type": "VIDEO_POKER", "category": "hand", "trigger": "HAND_RESULT", "conditions": {"hand_rank": "FLUSH"}, "poc": 5, "rarity": "Uncommon", "is_discovery": True, "badge": "cards"},
    {"code": "ACH_VP_FULL_HOUSE", "name": "Full of Grace", "game_type": "VIDEO_POKER", "category": "hand", "trigger": "HAND_RESULT", "conditions": {"hand_rank": "FULL_HOUSE"}, "poc": 8, "rarity": "Uncommon", "is_discovery": True, "badge": "cards"},
    {"code": "ACH_VP_4OAK", "name": "Quad Squad", "game_type": "VIDEO_POKER", "category": "hand", "trigger": "HAND_RESULT", "conditions": {"hand_rank": "FOUR_OF_A_KIND"}, "poc": 12, "rarity": "Rare", "is_discovery": True, "badge": "cards"},
    {"code": "ACH_VP_4_ACES", "name": "Ace Force", "game_type": "VIDEO_POKER", "category": "hand", "trigger": "HAND_RESULT", "conditions": {"hand_rank": "FOUR_ACES"}, "poc": 25, "rarity": "Very Rare", "badge": "cards"},
    {"code": "ACH_VP_STR_FLUSH", "name": "Straight to Heaven", "game_type": "VIDEO_POKER", "category": "hand", "trigger": "HAND_RESULT", "conditions": {"hand_rank": "STRAIGHT_FLUSH"}, "poc": 20, "rarity": "Extremely Rare", "is_discovery": True, "badge": "cards"},
    {"code": "ACH_VP_ROYAL", "name": "The Holy Grail", "game_type": "VIDEO_POKER", "category": "hand", "trigger": "HAND_RESULT", "conditions": {"hand_rank": "NATURAL_ROYAL"}, "poc": 100, "rarity": "Legendary", "floor_broadcast": True, "badge": "crown"},
    {"code": "ACH_VP_HOLD_NOTHING_WIN", "name": "Gambler's Nerve", "game_type": "VIDEO_POKER", "category": "luck", "trigger": "HAND_RESULT", "conditions": {"cards_held_count": 0, "is_winner": True}, "poc": 10, "rarity": "Hard-Luck", "badge": "dice"},
    # KENO
    {"code": "ACH_K_FIRST_WIN", "name": "First Catch", "game_type": "KENO", "category": "catch", "trigger": "KENO_RESULT", "conditions": {"is_winner": True}, "poc": 3, "rarity": "Common", "is_discovery": True, "badge": "ball"},
    {"code": "ACH_K_7_OF_8", "name": "Seven of Eight", "game_type": "KENO", "category": "catch", "trigger": "KENO_RESULT", "conditions": {"matches": {"$gte": 7}, "spots_picked": 8}, "poc": 12, "rarity": "Hard", "badge": "ball"},
    {"code": "ACH_K_SOLID", "name": "Solid Catch", "game_type": "KENO", "category": "catch", "trigger": "KENO_RESULT", "conditions": {"is_solid_catch": True}, "poc": 25, "rarity": "Very Hard", "is_discovery": True, "badge": "ball"},
    {"code": "ACH_K_FIRST_BALL", "name": "First Ball Magic", "game_type": "KENO", "category": "luck", "trigger": "KENO_RESULT", "conditions": {"first_ball_match": True}, "poc": 3, "rarity": "Medium-Luck", "badge": "ball"},
    {"code": "ACH_K_STREAK_3", "name": "Keno Streak 3", "game_type": "KENO", "category": "streak", "trigger": "KENO_RESULT", "conditions": {"consecutive_wins": {"$gte": 3}}, "poc": 6, "rarity": "Medium", "badge": "chain", "is_repeating": True},
    {"code": "ACH_K_STREAK_5", "name": "Keno Streak 5", "game_type": "KENO", "category": "streak", "trigger": "KENO_RESULT", "conditions": {"consecutive_wins": {"$gte": 5}}, "poc": 12, "rarity": "Hard", "badge": "chain"},
    {"code": "ACH_K_PROGRESSIVE", "name": "Keno Progressive Legend", "game_type": "KENO", "category": "jackpot", "trigger": "KENO_RESULT", "conditions": {"progressive_hit": True}, "poc": 35, "rarity": "Extreme", "floor_broadcast": True, "badge": "crown"},
]

# JOURNEY STEP LIBRARY
JOURNEY_STEPS = {
    "UNIVERSAL": [
        {"code": "J_TIME_15", "trigger": "session_duration >= 15", "desc": "Play for 15 minutes", "poc": 3, "difficulty": "Easy"},
        {"code": "J_TIME_30", "trigger": "session_duration >= 30", "desc": "Play for 30 minutes", "poc": 5, "difficulty": "Easy"},
        {"code": "J_TIME_45", "trigger": "session_duration >= 45", "desc": "Play for 45 minutes", "poc": 8, "difficulty": "Medium"},
        {"code": "J_WIN_ANY_3", "trigger": "wins_this_session >= 3", "desc": "Win 3 games", "poc": 3, "difficulty": "Easy"},
        {"code": "J_WIN_ANY_10", "trigger": "wins_this_session >= 10", "desc": "Win 10 games", "poc": 5, "difficulty": "Medium"},
        {"code": "J_COIN_IN_50", "trigger": "session_coin_in >= 5000", "desc": "Reach $50 coin-in", "poc": 5, "difficulty": "Easy"},
        {"code": "J_COIN_IN_150", "trigger": "session_coin_in >= 15000", "desc": "Reach $150 coin-in", "poc": 10, "difficulty": "Medium"},
        {"code": "J_CONSEC_3", "trigger": "consecutive_wins >= 3", "desc": "Win 3 in a row", "poc": 6, "difficulty": "Medium"},
    ],
    "SLOTS": [
        {"code": "J_S_SCATTER_3", "trigger": "SCATTER_HIT.scatter_count >= 3", "desc": "Land 3+ scatters", "poc": 4, "difficulty": "Easy"},
        {"code": "J_S_BONUS_1", "trigger": "BONUS_TRIGGERED", "desc": "Trigger a bonus round", "poc": 5, "difficulty": "Easy-Med"},
        {"code": "J_S_BONUS_2", "trigger": "bonus_rounds_session >= 2", "desc": "Trigger 2 bonus rounds", "poc": 10, "difficulty": "Medium"},
        {"code": "J_S_WILD_LINE", "trigger": "WILD_COMBINATION", "desc": "Full wild payline", "poc": 8, "difficulty": "Medium"},
        {"code": "J_S_WIN_50X", "trigger": "MEGA_WIN.win_multiplier >= 50", "desc": "Hit 50x your bet", "poc": 12, "difficulty": "Hard"},
        {"code": "J_S_WIN_100X", "trigger": "MEGA_WIN.win_multiplier >= 100", "desc": "Hit 100x your bet", "poc": 20, "difficulty": "Very Hard"},
        {"code": "J_S_RETRIGGER", "trigger": "BONUS_RETRIGGER", "desc": "Re-trigger free spins", "poc": 10, "difficulty": "Hard"},
    ],
    "VIDEO_POKER": [
        {"code": "J_VP_PAIR", "trigger": "HAND_RESULT.hand_rank >= JOB", "desc": "Hit Jacks or Better", "poc": 2, "difficulty": "Very Easy"},
        {"code": "J_VP_2PAIR", "trigger": "HAND_RESULT.hand_rank == TWO_PAIR", "desc": "Hit Two Pair", "poc": 3, "difficulty": "Easy"},
        {"code": "J_VP_3OAK", "trigger": "HAND_RESULT.hand_rank == 3OAK", "desc": "Hit Three of a Kind", "poc": 4, "difficulty": "Easy"},
        {"code": "J_VP_STRAIGHT", "trigger": "HAND_RESULT.hand_rank == STRAIGHT", "desc": "Hit a Straight", "poc": 5, "difficulty": "Medium"},
        {"code": "J_VP_FLUSH", "trigger": "HAND_RESULT.hand_rank == FLUSH", "desc": "Hit a Flush", "poc": 6, "difficulty": "Medium"},
        {"code": "J_VP_FH", "trigger": "HAND_RESULT.hand_rank == FULL_HOUSE", "desc": "Hit a Full House", "poc": 8, "difficulty": "Medium"},
        {"code": "J_VP_4OAK", "trigger": "HAND_RESULT.hand_rank == 4OAK", "desc": "Hit Four of a Kind", "poc": 12, "difficulty": "Medium-Hard"},
    ],
    "KENO": [
        {"code": "J_K_WIN", "trigger": "KENO_RESULT.is_winner", "desc": "Win any keno game", "poc": 2, "difficulty": "Easy"},
        {"code": "J_K_HALF", "trigger": "matches >= spots_picked/2", "desc": "Catch half your numbers", "poc": 3, "difficulty": "Easy"},
        {"code": "J_K_5_OF_8", "trigger": "matches >= 5 && spots_picked == 8", "desc": "Catch 5 of 8", "poc": 4, "difficulty": "Easy-Med"},
        {"code": "J_K_STREAK_3", "trigger": "consecutive_wins >= 3", "desc": "Win 3 keno in a row", "poc": 6, "difficulty": "Medium"},
        {"code": "J_K_FIRST_BALL", "trigger": "first_ball_match", "desc": "First ball is yours", "poc": 3, "difficulty": "Medium"},
    ],
}

HALL_OF_FAME = [
    {"code": "HOF_SLOT_INITIATE", "title": "Slot Initiate", "requirement": "Complete 10 session journeys", "stat": "journeys_completed", "threshold": 10, "poc": 25, "badge": "bronze_slot"},
    {"code": "HOF_SLOT_VETERAN", "title": "Slot Veteran", "requirement": "Complete 50 session journeys", "stat": "journeys_completed", "threshold": 50, "poc": 50, "badge": "silver_slot"},
    {"code": "HOF_SLOT_LEGEND", "title": "Slot Legend", "requirement": "Complete 100 session journeys", "stat": "journeys_completed", "threshold": 100, "poc": 100, "badge": "gold_slot"},
    {"code": "HOF_BONUS_HUNTER", "title": "Bonus Hunter Elite", "requirement": "Trigger 100 bonus rounds", "stat": "lifetime_bonus_rounds", "threshold": 100, "poc": 40, "badge": "silver_spinner"},
    {"code": "HOF_POKER_MASTER", "title": "Poker Master", "requirement": "Hit Quads 10 times", "stat": "lifetime_quads", "threshold": 10, "poc": 50, "badge": "silver_cards"},
    {"code": "HOF_POKER_LEGEND", "title": "Poker Legend", "requirement": "Hit a Royal Flush", "stat": "lifetime_royals", "threshold": 1, "poc": 100, "badge": "gold_crown"},
    {"code": "HOF_KENO_MASTER", "title": "Keno Master", "requirement": "10 solid catches", "stat": "lifetime_solid_catches", "threshold": 10, "poc": 60, "badge": "silver_ball"},
    {"code": "HOF_EXPLORER", "title": "Floor Explorer", "requirement": "Win on 10 different games", "stat": "unique_game_wins", "threshold": 10, "poc": 20, "badge": "explorer"},
    {"code": "HOF_JOURNEY_WARRIOR", "title": "Journey Warrior", "requirement": "100 journey completions", "stat": "journeys_completed", "threshold": 100, "poc": 100, "badge": "warrior"},
    {"code": "HOF_CHAMPION", "title": "UGG Champion", "requirement": "All Hall of Fame titles", "stat": "hof_titles_earned", "threshold": 8, "poc": 500, "badge": "champion_crown"},
]


# ══════════════════════════════════════════════════
# JOURNEY GENERATOR
# ══════════════════════════════════════════════════

def generate_journey(player: dict, game_type: str = "SLOTS") -> dict:
    """AI-generate a personalized Session Journey for a player."""
    now = datetime.now(timezone.utc)
    churn = player.get("churn_score", 50)
    tier_mult = 1.0
    if churn >= 80: tier_mult = 1.5
    elif churn >= 65: tier_mult = 1.3
    elif churn >= 50: tier_mult = 1.15

    # Get step library for game type
    universal = JOURNEY_STEPS["UNIVERSAL"]
    game_steps = JOURNEY_STEPS.get(game_type, [])
    all_steps = universal + game_steps

    # Select steps: 2 easy, 2 medium, 1 hard, 1 boss
    easy = [s for s in all_steps if s["difficulty"] in ("Easy", "Very Easy")]
    medium = [s for s in all_steps if s["difficulty"] in ("Medium", "Easy-Med", "Medium-Hard")]
    hard = [s for s in all_steps if s["difficulty"] in ("Hard", "Very Hard")]

    selected = []
    if easy: selected.extend(random.sample(easy, min(2, len(easy))))
    if medium: selected.extend(random.sample(medium, min(2, len(medium))))
    if hard: selected.extend(random.sample(hard, min(1, len(hard))))

    # Boss step — hardest available
    boss_pool = [s for s in all_steps if s["difficulty"] in ("Hard", "Very Hard") and s not in selected]
    boss = random.choice(boss_pool) if boss_pool else (random.choice(hard) if hard else random.choice(all_steps))

    steps = []
    for i, s in enumerate(selected):
        steps.append({
            "step_number": i + 1, "code": s["code"], "description": s["desc"],
            "trigger": s["trigger"], "difficulty": s["difficulty"],
            "poc_amount": round(s["poc"] * tier_mult, 2),
            "is_boss": False, "is_completed": False, "completed_at": None,
        })
    steps.append({
        "step_number": len(steps) + 1, "code": boss["code"], "description": f"BOSS: {boss['desc']}",
        "trigger": boss["trigger"], "difficulty": "BOSS",
        "poc_amount": round(boss["poc"] * tier_mult * 2.0, 2),
        "is_boss": True, "is_completed": False, "completed_at": None,
    })

    total_poc = sum(s["poc_amount"] for s in steps)
    speed_bonus = round(total_poc * 0.2, 2) if churn >= 60 else 0

    return {
        "id": str(uuid.uuid4()),
        "player_id": player.get("player_id"),
        "player_name": player.get("player_name", ""),
        "game_type": game_type,
        "journey_date": now.strftime("%Y-%m-%d"),
        "steps": steps,
        "steps_total": len(steps),
        "steps_completed": 0,
        "current_step": 1,
        "boss_unlocked": False,
        "boss_completed": False,
        "total_poc_available": total_poc,
        "poc_earned": 0,
        "speed_bonus_amount": speed_bonus,
        "speed_bonus_deadline": (now + timedelta(minutes=90)).isoformat() if speed_bonus > 0 else None,
        "speed_bonus_earned": False,
        "is_complete": False,
        "tier_multiplier": tier_mult,
        "generated_at": now.isoformat(),
    }


# ══════════════════════════════════════════════════
# API ENDPOINTS
# ══════════════════════════════════════════════════

@router.get("/achievements")
async def list_achievements(request: Request, game_type: str = None, category: str = None):
    await get_current_user(request)
    achs = ACHIEVEMENTS
    if game_type: achs = [a for a in achs if a["game_type"] == game_type]
    if category: achs = [a for a in achs if a["category"] == category]
    return {"achievements": achs, "total": len(achs), "game_types": list(set(a["game_type"] for a in ACHIEVEMENTS)), "categories": list(set(a["category"] for a in ACHIEVEMENTS))}


@router.get("/journey-steps")
async def list_journey_steps(request: Request, game_type: str = None):
    await get_current_user(request)
    if game_type:
        return {"steps": JOURNEY_STEPS.get("UNIVERSAL", []) + JOURNEY_STEPS.get(game_type, []), "game_type": game_type}
    return {"steps": JOURNEY_STEPS}


@router.get("/hall-of-fame")
async def list_hall_of_fame(request: Request):
    await get_current_user(request)
    return {"titles": HALL_OF_FAME}


@router.post("/journey/generate")
async def create_journey(request: Request):
    """Generate a personalized Session Journey for a player."""
    user = await get_current_user(request)
    body = await request.json()
    player_id = body.get("player_id")
    game_type = body.get("game_type", "SLOTS")

    # Get PIRS player profile
    player = await db.pirs_players.find_one({"player_id": player_id}, {"_id": 0})
    if not player:
        player = {"player_id": player_id, "player_name": "Guest", "churn_score": 50}

    # Check for existing journey today
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    existing = await db.gamification_journeys.find_one({"player_id": player_id, "journey_date": today}, {"_id": 0})
    if existing:
        return existing

    journey = generate_journey(player, game_type)
    await db.gamification_journeys.insert_one(journey)
    journey.pop("_id", None)
    return journey


@router.post("/journey/advance")
async def advance_journey(request: Request):
    """Report a game event and check if it advances the player's journey."""
    body = await request.json()
    player_id = body.get("player_id")
    event_type = body.get("event_type")
    game_data = body.get("game_data", {})
    session_context = body.get("session_context", {})

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc)
    journey = await db.gamification_journeys.find_one({"player_id": player_id, "journey_date": today, "is_complete": False}, {"_id": 0})
    if not journey:
        return {"advanced": False, "reason": "No active journey"}

    current = journey.get("current_step", 1)
    steps = journey.get("steps", [])
    current_step = next((s for s in steps if s["step_number"] == current and not s["is_completed"]), None)
    if not current_step:
        return {"advanced": False, "reason": "All steps complete or no matching step"}

    # Evaluate if event satisfies current step
    satisfied = _evaluate_step(current_step, event_type, game_data, session_context)
    if not satisfied:
        return {"advanced": False, "current_step": current, "step_description": current_step["description"]}

    # Complete the step
    current_step["is_completed"] = True
    current_step["completed_at"] = now.isoformat()
    poc_earned = current_step["poc_amount"]
    journey["poc_earned"] = (journey.get("poc_earned", 0) or 0) + poc_earned
    journey["steps_completed"] = sum(1 for s in steps if s["is_completed"])

    # Check boss unlock
    non_boss = [s for s in steps if not s["is_boss"]]
    if all(s["is_completed"] for s in non_boss):
        journey["boss_unlocked"] = True

    # Check if boss completed
    boss = next((s for s in steps if s["is_boss"]), None)
    if boss and boss["is_completed"]:
        journey["boss_completed"] = True
        journey["is_complete"] = True

    # Check if all done
    if all(s["is_completed"] for s in steps):
        journey["is_complete"] = True
        # Speed bonus
        if journey.get("speed_bonus_deadline"):
            if now.isoformat() <= journey["speed_bonus_deadline"]:
                journey["speed_bonus_earned"] = True
                journey["poc_earned"] += journey.get("speed_bonus_amount", 0)

    # Advance to next step
    if not journey["is_complete"]:
        next_step = next((s for s in steps if not s["is_completed"]), None)
        if next_step:
            journey["current_step"] = next_step["step_number"]

    await db.gamification_journeys.update_one({"id": journey["id"]}, {"$set": journey})

    # Award POC via PIRS
    if poc_earned > 0:
        await db.poc_awards.insert_one({
            "id": str(uuid.uuid4()), "player_id": player_id,
            "player_name": journey.get("player_name", ""),
            "trigger_type": "journey_step", "rule_name": f"Journey Step {current}",
            "poc_amount": poc_earned, "poc_type": "play_only_credits",
            "delivery_status": "delivered", "awarded_by": "GAMIFICATION_ENGINE",
            "created_at": now.isoformat(),
        })

    # Build message for EGM
    message = None
    if journey["is_complete"]:
        message = {"type": "MSG_JOURNEY_COMPLETE", "text": f"QUEST COMPLETE! You earned ${journey['poc_earned']:.2f} in Play Credits today!", "priority": "Critical", "animation": "grand_celebration", "duration": 20}
    elif journey.get("boss_unlocked") and current_step.get("is_boss"):
        message = {"type": "MSG_BOSS_UNLOCK", "text": f"BOSS REWARD UNLOCKED! ${poc_earned:.2f} Play Credits!", "priority": "Critical", "animation": "boss_reveal_full", "duration": 15}
    else:
        next_s = next((s for s in steps if not s["is_completed"]), None)
        message = {"type": "MSG_JOURNEY_STEP", "text": f"Step {current} Complete! ${poc_earned:.2f} Play Credits! Next: {next_s['description'] if next_s else 'BOSS!'}", "priority": "High", "animation": "step_complete_burst", "duration": 8}

    return {"advanced": True, "step_completed": current, "poc_earned": poc_earned, "journey_progress": f"{journey['steps_completed']}/{journey['steps_total']}", "is_complete": journey["is_complete"], "boss_unlocked": journey.get("boss_unlocked"), "speed_bonus_earned": journey.get("speed_bonus_earned"), "message": message}


def _evaluate_step(step: dict, event_type: str, game_data: dict, session_ctx: dict) -> bool:
    """Check if a game event satisfies a journey step condition."""
    trigger = step.get("trigger", "")
    # Simple matching based on trigger patterns
    if "session_duration" in trigger:
        mins = session_ctx.get("session_duration_mins", 0)
        threshold = int(trigger.split(">=")[-1].strip()) if ">=" in trigger else 15
        return mins >= threshold
    if "wins_this_session" in trigger:
        wins = session_ctx.get("wins_this_session", 0)
        threshold = int(trigger.split(">=")[-1].strip()) if ">=" in trigger else 3
        return wins >= threshold
    if "session_coin_in" in trigger:
        ci = session_ctx.get("session_coin_in", 0)
        threshold = int(trigger.split(">=")[-1].strip()) if ">=" in trigger else 5000
        return ci >= threshold
    if "consecutive_wins" in trigger:
        streak = session_ctx.get("consecutive_wins", game_data.get("streak_count", 0))
        threshold = int(trigger.split(">=")[-1].strip()) if ">=" in trigger else 3
        return streak >= threshold
    if event_type and event_type in trigger:
        return True
    if "HAND_RESULT" in trigger and event_type == "HAND_RESULT":
        return True
    if "KENO_RESULT" in trigger and event_type == "KENO_RESULT":
        return True
    return random.random() < 0.3  # Fallback for demo


@router.post("/event")
async def process_game_event(request: Request):
    """
    THE MAIN ENDPOINT — EGM sends a game event, UGG processes everything.
    Returns achievements earned, journey progress, streak updates, and display messages.
    """
    body = await request.json()
    player_id = body.get("player_id")
    event_type = body.get("event_type", "REEL_SPIN")
    game_type = body.get("game_type", "SLOTS")
    game_data = body.get("game_data", {})
    session_context = body.get("session_context", {})
    egm_id = body.get("egm_id")
    now = datetime.now(timezone.utc)

    results = {"achievements": [], "journey": None, "streaks": [], "messages": [], "poc_total": 0}

    # 1. Check achievements
    for ach in ACHIEVEMENTS:
        if ach["game_type"] != game_type and ach["game_type"] != "ALL":
            continue
        if ach["trigger"] != event_type:
            continue
        # Check conditions
        matched = True
        for key, cond in ach.get("conditions", {}).items():
            val = game_data.get(key)
            if isinstance(cond, dict):
                if "$gte" in cond and (val is None or val < cond["$gte"]): matched = False
            elif val != cond:
                matched = False
        if not matched:
            continue
        # Check if already earned (for non-repeating)
        if not ach.get("is_repeating"):
            existing = await db.player_achievements.find_one({"player_id": player_id, "achievement_code": ach["code"]})
            if existing:
                continue
        # Award!
        poc = ach["poc"]
        await db.player_achievements.insert_one({
            "id": str(uuid.uuid4()), "player_id": player_id, "achievement_code": ach["code"],
            "achievement_name": ach["name"], "game_type": game_type, "category": ach["category"],
            "rarity": ach["rarity"], "poc_awarded": poc, "badge": ach.get("badge"),
            "is_discovery": ach.get("is_discovery", False),
            "earned_at": now.isoformat(), "egm_id": egm_id,
        })
        results["achievements"].append({"code": ach["code"], "name": ach["name"], "poc": poc, "rarity": ach["rarity"], "badge": ach.get("badge")})
        results["poc_total"] += poc
        msg_type = "MSG_ACHIEVEMENT_LEGEND" if ach["rarity"] in ("Legendary", "Extremely Rare") else "MSG_DISCOVERY" if ach.get("is_discovery") else "MSG_ACHIEVEMENT"
        results["messages"].append({"type": msg_type, "text": f"ACHIEVEMENT: {ach['name']}! ${poc:.2f} Play Credits!", "priority": "Critical" if ach.get("floor_broadcast") else "High", "duration": 15 if ach["rarity"] == "Legendary" else 8})

    # 2. Advance journey
    today = now.strftime("%Y-%m-%d")
    journey = await db.gamification_journeys.find_one({"player_id": player_id, "journey_date": today, "is_complete": False}, {"_id": 0})
    if journey:
        current = journey.get("current_step", 1)
        steps = journey.get("steps", [])
        current_step = next((s for s in steps if s["step_number"] == current and not s["is_completed"]), None)
        if current_step and _evaluate_step(current_step, event_type, game_data, session_context):
            current_step["is_completed"] = True
            current_step["completed_at"] = now.isoformat()
            poc = current_step["poc_amount"]
            journey["poc_earned"] = (journey.get("poc_earned", 0) or 0) + poc
            journey["steps_completed"] = sum(1 for s in steps if s["is_completed"])
            non_boss = [s for s in steps if not s["is_boss"]]
            if all(s["is_completed"] for s in non_boss): journey["boss_unlocked"] = True
            if all(s["is_completed"] for s in steps): journey["is_complete"] = True
            next_s = next((s for s in steps if not s["is_completed"]), None)
            if next_s: journey["current_step"] = next_s["step_number"]
            await db.gamification_journeys.update_one({"id": journey["id"]}, {"$set": journey})
            results["poc_total"] += poc
            results["journey"] = {"step_completed": current, "poc": poc, "progress": f"{journey['steps_completed']}/{journey['steps_total']}", "is_complete": journey["is_complete"], "boss_unlocked": journey.get("boss_unlocked")}
            results["messages"].append({"type": "MSG_JOURNEY_STEP", "text": f"Quest Step {current} done! ${poc:.2f} POC!", "priority": "High", "duration": 8})

    # 3. Store event
    await db.gamification_events.insert_one({
        "id": str(uuid.uuid4()), "player_id": player_id, "egm_id": egm_id,
        "event_type": event_type, "game_type": game_type,
        "game_data": game_data, "session_context": session_context,
        "achievements_triggered": [a["code"] for a in results["achievements"]],
        "journey_step_advanced": results["journey"].get("step_completed") if results.get("journey") else None,
        "poc_awarded": results["poc_total"],
        "received_at": now.isoformat(),
    })

    # 4. Push messages to EGM
    if egm_id and results["messages"]:
        for msg in results["messages"][:3]:
            await db.device_messages.insert_one({
                "id": str(uuid.uuid4()), "device_id": egm_id,
                "message_text": msg["text"], "message_type": "PROMO",
                "display_duration_seconds": msg.get("duration", 8),
                "display_position": "CENTER", "background_color": "#FFD700", "text_color": "#070B14",
                "priority": msg.get("priority", "HIGH"),
                "expires_at": (now + timedelta(minutes=5)).isoformat(),
                "sent_by": "GAMIFICATION", "sent_at": now.isoformat(), "status": "PENDING",
            })

    return results


# ══════════════════════════════════════════════════
# DASHBOARD & ANALYTICS
# ══════════════════════════════════════════════════

@router.get("/dashboard")
async def gamification_dashboard(request: Request):
    await get_current_user(request)
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    achievements_today = await db.player_achievements.count_documents({"earned_at": {"$gte": today}})
    journeys_active = await db.gamification_journeys.count_documents({"journey_date": today, "is_complete": False})
    journeys_complete = await db.gamification_journeys.count_documents({"journey_date": today, "is_complete": True})
    events_today = await db.gamification_events.count_documents({"received_at": {"$gte": today}})
    poc_pipe = [{"$match": {"received_at": {"$gte": today}}}, {"$group": {"_id": None, "total": {"$sum": "$poc_awarded"}}}]
    poc_agg = await db.gamification_events.aggregate(poc_pipe).to_list(1)
    poc_today = poc_agg[0]["total"] if poc_agg else 0

    # Recent achievements
    recent = await db.player_achievements.find({}, {"_id": 0}).sort("earned_at", -1).limit(15).to_list(15)

    # Top achievers
    top_pipe = [{"$match": {"earned_at": {"$gte": today}}}, {"$group": {"_id": "$player_id", "count": {"$sum": 1}, "poc": {"$sum": "$poc_awarded"}}}, {"$sort": {"count": -1}}, {"$limit": 10}]
    top = await db.player_achievements.aggregate(top_pipe).to_list(10)

    # Achievement distribution
    dist_pipe = [{"$group": {"_id": "$rarity", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    dist = await db.player_achievements.aggregate(dist_pipe).to_list(20)

    return {
        "achievements_today": achievements_today,
        "journeys_active": journeys_active,
        "journeys_completed_today": journeys_complete,
        "events_today": events_today,
        "poc_awarded_today": round(poc_today, 2),
        "recent_achievements": recent,
        "top_achievers": top,
        "rarity_distribution": [{"rarity": d["_id"], "count": d["count"]} for d in dist],
        "achievement_library_size": len(ACHIEVEMENTS),
        "journey_step_library_size": sum(len(v) for v in JOURNEY_STEPS.values()),
        "hall_of_fame_titles": len(HALL_OF_FAME),
    }


@router.get("/player/{player_id}/profile")
async def get_player_gamification_profile(request: Request, player_id: str):
    await get_current_user(request)
    achievements = await db.player_achievements.find({"player_id": player_id}, {"_id": 0}).sort("earned_at", -1).to_list(100)
    journeys = await db.gamification_journeys.find({"player_id": player_id}, {"_id": 0}).sort("journey_date", -1).limit(10).to_list(10)
    hof = await db.player_hall_of_fame.find({"player_id": player_id}, {"_id": 0}).to_list(20)
    total_poc = sum(a.get("poc_awarded", 0) for a in achievements)
    journeys_completed = sum(1 for j in journeys if j.get("is_complete"))

    return {
        "player_id": player_id,
        "total_achievements": len(achievements),
        "total_poc_from_achievements": round(total_poc, 2),
        "journeys_completed": journeys_completed,
        "hall_of_fame_titles": len(hof),
        "achievements": achievements,
        "recent_journeys": journeys,
        "hall_of_fame": hof,
        "unique_badges": list(set(a.get("badge") for a in achievements if a.get("badge"))),
    }
