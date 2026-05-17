from datetime import datetime

# ──────────────────────────────────────────────
#  Default character template
# ──────────────────────────────────────────────

DEFAULT_CHARACTER = {
    "name": "Герой",
    "level": 1,
    "xp": 0,
    "energy": 50,
    "strength": 10,
    "intellect": 10,
    "mood": 50,
    "created_at": "",
    "last_action": "",
    "meals_today": 0,
    "workouts_today": 0,
    "rests_today": 0,
    "total_meals": 0,
    "total_workouts": 0,
    "total_rests": 0,
    "junk_meals": 0,       # счётчик вредной еды
    "healthy_meals": 0,    # счётчик полезной еды
}

# ──────────────────────────────────────────────
#  Food category keywords
# ──────────────────────────────────────────────

# Слова → еда считается ВРЕДНОЙ
JUNK_KEYWORDS = [
    "бургер", "burger", "пицца", "pizza", "чипсы", "chips",
    "шоколад", "chocolate", "конфет", "candy", "сладк",
    "кола", "cola", "пепси", "pepsi", "фастфуд", "фаст-фуд",
    "макдак", "мак", "kfc", "кфс", "сосиск", "сардельк",
    "пирожн", "торт", "cake", "мороженое", "ice cream",
    "печеньк", "cookie", "вафл", "хот-дог", "hotdog",
    "картошка фри", "fries", "снекс", "snack", "газировк",
]

# Слова → еда считается ПОЛЕЗНОЙ
HEALTHY_KEYWORDS = [
    "гречк", "рис", "овсянк", "oatmeal", "овощ", "vegetable",
    "салат", "salad", "курица", "chicken", "рыба", "fish",
    "яйц", "egg", "творог", "cottage", "кефир", "йогурт",
    "yogurt", "фрукт", "fruit", "яблок", "apple", "банан",
    "banana", "орех", "nuts", "брокколи", "broccoli",
    "суп", "soup", "каш", "porridge", "индейк", "turkey",
    "лосось", "salmon", "тунец", "tuna", "авокадо", "avocado",
    "шпинат", "spinach", "горох", "pea", "фасол", "bean",
]


def classify_food(food_text: str) -> str:
    """Return 'healthy', 'junk', or 'neutral'."""
    text = food_text.lower()
    for kw in JUNK_KEYWORDS:
        if kw in text:
            return "junk"
    for kw in HEALTHY_KEYWORDS:
        if kw in text:
            return "healthy"
    return "neutral"

XP_PER_LEVEL = 100  # XP needed to level up


# ──────────────────────────────────────────────
#  Stat helpers (all stats clamp 0–100)
# ──────────────────────────────────────────────

def _clamp(value: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, value))


def new_character(name: str) -> dict:
    char = DEFAULT_CHARACTER.copy()
    char["name"] = name
    char["created_at"] = datetime.now().isoformat()
    char["last_action"] = datetime.now().isoformat()
    return char


# ──────────────────────────────────────────────
#  Actions
# ──────────────────────────────────────────────

def eat_food(char: dict, food_text: str) -> tuple[dict, str]:
    """Eating: effects depend on food category. Returns (char, category)."""
    category = classify_food(food_text)

    if category == "healthy":
        char["energy"]    = _clamp(char["energy"]    + 20)
        char["mood"]      = _clamp(char["mood"]       + 10)
        char["intellect"] = _clamp(char["intellect"]  + 3)
        char["xp"]        += 30
        char["healthy_meals"] = char.get("healthy_meals", 0) + 1
    elif category == "junk":
        char["energy"]    = _clamp(char["energy"]    + 10)
        char["mood"]      = _clamp(char["mood"]       + 15)  # вкусно, но...
        char["strength"]  = _clamp(char["strength"]  - 3)
        char["xp"]        += 10
        char["junk_meals"] = char.get("junk_meals", 0) + 1
    else:  # neutral
        char["energy"]    = _clamp(char["energy"]    + 15)
        char["mood"]      = _clamp(char["mood"]       + 5)
        char["xp"]        += 20

    char["meals_today"] += 1
    char["total_meals"] += 1
    char["last_action"] = datetime.now().isoformat()
    char = _check_level_up(char)
    return char, category


def do_rest(char: dict) -> dict:
    """Rest: +energy, +mood, small intellect bonus, tiny xp."""
    char["energy"]    = _clamp(char["energy"]    + 30)
    char["mood"]      = _clamp(char["mood"]       + 15)
    char["intellect"] = _clamp(char["intellect"]  + 2)
    char["xp"]        += 10
    char["rests_today"]  = char.get("rests_today",  0) + 1
    char["total_rests"]  = char.get("total_rests",  0) + 1
    char["last_action"]  = datetime.now().isoformat()
    char = _check_level_up(char)
    return char


def do_workout(char: dict, workout_text: str) -> dict:
    """Workout: +strength, -energy, +mood, +xp."""
    char["strength"] = _clamp(char["strength"] + 10)
    char["energy"]   = _clamp(char["energy"]   - 20)
    char["mood"]     = _clamp(char["mood"]      + 10)
    char["xp"]       += 50
    char["workouts_today"] += 1
    char["total_workouts"] += 1
    char["last_action"]    = datetime.now().isoformat()
    char = _check_level_up(char)
    return char


def _check_level_up(char: dict) -> dict:
    while char["xp"] >= char["level"] * XP_PER_LEVEL:
        char["xp"]    -= char["level"] * XP_PER_LEVEL
        char["level"] += 1
        # Bonus on level-up
        char["energy"]   = _clamp(char["energy"]   + 20)
        char["mood"]     = _clamp(char["mood"]      + 20)
        char["intellect"]= _clamp(char["intellect"] + 5)
    return char


# ──────────────────────────────────────────────
#  Stat bars for display
# ──────────────────────────────────────────────

def stat_bar(value: int, total: int = 100, length: int = 10) -> str:
    filled = round(value / total * length)
    return "█" * filled + "░" * (length - filled)


def energy_emoji(value: int) -> str:
    if value >= 70: return "⚡"
    if value >= 40: return "🔋"
    return "😴"


def mood_emoji(value: int) -> str:
    if value >= 70: return "😄"
    if value >= 40: return "😐"
    return "😤"


def level_title(level: int) -> str:
    titles = {
        1: "🥚 Новичок",
        2: "🐣 Начинающий",
        3: "💪 Атлет",
        5: "🔥 Машина",
        8: "🏆 Легенда",
        10: "⚡ Бог Симуляции",
    }
    for threshold in sorted(titles.keys(), reverse=True):
        if level >= threshold:
            return titles[threshold]
    return "🥚 Новичок"
