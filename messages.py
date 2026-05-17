from models import stat_bar, energy_emoji, mood_emoji, level_title


# ──────────────────────────────────────────────
#  /start
# ──────────────────────────────────────────────

WELCOME_NEW = """
🎮 *Добро пожаловать в Life Simulator!*

Ты только что создал своего персонажа — цифрового двойника, который растёт вместе с тобой.

Ешь — он наберётся сил.
Тренируйся — он станет мощнее.
Ленись — и он это почувствует 😅

Как назовём твоего героя?
_(просто напиши имя)_
"""

WELCOME_BACK = """
👾 *С возвращением, {name}!*

Твой персонаж скучал. Время действовать!
"""


def character_created(name: str) -> str:
    return f"""
✨ *Персонаж создан!*

Имя: *{name}*
Уровень: 1 — 🥚 Новичок

Начальные характеристики установлены. Удачи, герой!

Используй:
• /food — покормить персонажа 🍎
• /workout — провести тренировку 💪
• /rest — отдохнуть 😴
• /status — посмотреть статус 📊
"""


# ──────────────────────────────────────────────
#  /food
# ──────────────────────────────────────────────

FOOD_PROMPT = """
🍽 *Что ел твой герой?*

Напиши любым текстом — например:
_"гречка с курицей"_ или _"шоколадка (без осуждения)"_

Бот определит: полезная еда 🥦, вредная 🍔 или нейтральная 🍞 — и начислит бонусы соответственно.
"""


def food_result(char: dict, food_text: str, category: str) -> str:
    if category == "healthy":
        header  = "🥦 *Здоровое питание! Герой в восторге!*"
        bonuses = "⚡ +20 Энергия  •  😄 +10 Настроение  •  🧠 +3 Интеллект  •  ✨ +30 XP"
        comment = "Твой герой питается как чемпион. Так держать! 🏆"
    elif category == "junk":
        header  = "🍔 *Вредная еда... но как вкусно!*"
        bonuses = "⚡ +10 Энергия  •  😄 +15 Настроение  •  💪 −3 Сила  •  ✨ +10 XP"
        comment = _junk_comment(char.get("junk_meals", 0))
    else:
        header  = "🍞 *Поел. Нормально.*"
        bonuses = "⚡ +15 Энергия  •  😄 +5 Настроение  •  ✨ +20 XP"
        comment = "Простая еда — тоже топливо для героя."

    return f"""
{header}

Съел: _{food_text}_

{bonuses}

⚡ Энергия:    {stat_bar(char['energy'])} {char['energy']}/100
😄 Настроение: {stat_bar(char['mood'])} {char['mood']}/100
🧠 Интеллект:  {stat_bar(char['intellect'])} {char['intellect']}/100

_{comment}_
"""


def _junk_comment(junk_count: int) -> str:
    if junk_count <= 1:
        return "Раз в жизни можно. Герой не осуждает себя."
    if junk_count <= 3:
        return "Уже {j}-й раз... Может, разбавить чем-то полезным? 🥦".format(j=junk_count)
    return "Герой превращается в диванного короля 👑 Добавь тренировку — /workout"


# ──────────────────────────────────────────────
#  /rest
# ──────────────────────────────────────────────

REST_VARIANTS = [
    ("😴", "Герой вздремнул", "Короткий сон восстановил силы."),
    ("🛋", "Герой полежал на диване", "Иногда ничегонеделание — тоже стратегия."),
    ("🧘", "Герой помедитировал", "Разум очистился. Интеллект растёт."),
    ("📖", "Герой почитал книгу", "Лежать с умной книгой — это тоже отдых."),
    ("🎮", "Герой поиграл в игры", "Разгрузка мозга засчитана!"),
]


def rest_result(char: dict) -> str:
    import random
    emoji, action, comment = random.choice(REST_VARIANTS)
    rests = char.get("rests_today", 1)

    return f"""
{emoji} *{action}!*

⚡ +30 Энергия  •  😄 +15 Настроение  •  🧠 +2 Интеллект  •  ✨ +10 XP

⚡ Энергия:    {stat_bar(char['energy'])} {char['energy']}/100
😄 Настроение: {stat_bar(char['mood'])} {char['mood']}/100
🧠 Интеллект:  {stat_bar(char['intellect'])} {char['intellect']}/100

_{comment}_
{_rest_warning(rests)}"""


def _rest_warning(rests: int) -> str:
    if rests >= 3:
        return "\n⚠️ _Много отдыхаешь, герой. Может, /workout?_"
    return ""


# ──────────────────────────────────────────────
#  /workout
# ──────────────────────────────────────────────

WORKOUT_PROMPT = """
🏋️ *Какую тренировку провёл твой герой?*

Напиши что угодно:
_"30 минут бег"_ или _"отжимания 3х20"_
"""


def workout_result(char: dict, workout_text: str) -> str:
    return f"""
💥 *Тренировка засчитана!*

Упражнение: _{workout_text}_

💪 Сила:      {stat_bar(char['strength'])} {char['strength']}/100
⚡ Энергия:   {stat_bar(char['energy'])}   {char['energy']}/100
😄 Настроение:{stat_bar(char['mood'])}     {char['mood']}/100
✨ Опыт:      +50 XP

_{_workout_comment(char['workouts_today'])}_
"""


def _workout_comment(workouts: int) -> str:
    comments = [
        "Первая тренировка дня — герой гордится собой!",
        "Дважды за день?! Это уже серьёзно 🔥",
        "Три тренировки. Твой герой — машина. Отдохни немного.",
    ]
    return comments[min(workouts - 1, len(comments) - 1)]


# ──────────────────────────────────────────────
#  /status
# ──────────────────────────────────────────────

def status_message(char: dict) -> str:
    level     = char["level"]
    xp        = char["xp"]
    xp_needed = level * 100
    title     = level_title(level)
    healthy   = char.get("healthy_meals", 0)
    junk      = char.get("junk_meals", 0)
    rests     = char.get("total_rests", 0)

    return f"""
🧬 *Персонаж: {char['name']}*
{title} — Уровень {level}
Опыт: [{stat_bar(xp, xp_needed)}] {xp}/{xp_needed} XP

━━━━━━━━━━━━━━━━━
{energy_emoji(char['energy'])} Энергия:     {stat_bar(char['energy'])} {char['energy']}
💪 Сила:         {stat_bar(char['strength'])} {char['strength']}
🧠 Интеллект:    {stat_bar(char['intellect'])} {char['intellect']}
{mood_emoji(char['mood'])} Настроение:  {stat_bar(char['mood'])} {char['mood']}
━━━━━━━━━━━━━━━━━

📈 *Статистика:*
• Всего приёмов пищи: {char['total_meals']} (🥦 {healthy} полезных / 🍔 {junk} вредных)
• Всего тренировок:  {char['total_workouts']}
• Всего отдыхов:     {rests}

_{_status_tip(char)}_
"""


def _status_tip(char: dict) -> str:
    if char["energy"] < 30:
        return "⚠️ Герой устал — срочно поешь! /food"
    if char["strength"] < 20:
        return "💡 Хочешь стать сильнее? Время тренировки — /workout"
    if char["mood"] < 30:
        return "😤 Настроение на нуле. Может, размяться?"
    if char["level"] >= 5:
        return "🔥 Ты в огне. Продолжай в том же духе!"
    return "✨ Всё идёт по плану. Так держать, герой!"


# ──────────────────────────────────────────────
#  Level up
# ──────────────────────────────────────────────

def levelup_message(char: dict) -> str:
    return f"""
🎉 *LEVEL UP!*

Твой герой достиг уровня *{char['level']}*!
Новый титул: {level_title(char['level'])}

⚡ +20 к Энергии
😄 +20 к Настроению
🧠 +5 к Интеллекту

Ты становишься лучше каждый день 💥
"""
