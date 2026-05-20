from models import (stat_bar, energy_emoji, mood_emoji, level_title,
                    get_avatar, calculate_daily_kbzhu, calculate_bmi, bmi_category,
                    SHOP_ITEMS)

# ── /start ──────────────────────────────────────────────────────────────────

WELCOME_NEW = """
🎮 *Добро пожаловать в Life Simulator!*

Это не просто трекер — это твой цифровой двойник.
Он ест, тренируется и растёт вместе с тобой.

Давай создадим персонажа! Как тебя зовут?
_(напиши своё имя)_
"""

WELCOME_BACK = "👾 *С возвращением, {name}!*\n\nПерсонаж скучал. Время действовать! 💪"

def ask_gender():
    return "Отлично, *{name}*! 🎉\n\nКакой пол у твоего персонажа?"

def ask_age():
    return "Сколько тебе лет? _(напиши число)_"

def ask_body_type():
    return """Выбери начальное телосложение персонажа:

🦴 /slim — Худощавый
🙂 /normal — Нормальный  
💪 /thick — Плотный
🐻 /heavy — Массивный"""

def character_created(char):
    avatar = get_avatar(char)
    return f"""
✨ *Персонаж создан!*

{avatar} *{char['name']}*
Уровень 1 — 🥚 Новичок

Теперь заполни профиль для расчёта КБЖУ:
👉 /profile

Команды:
• /food — записать еду 🍽
• /workout — тренировка 💪
• /rest — отдых 😴
• /measurements — замеры 📏
• /status — твой персонаж 📊
• /shop — магазин 🛍
"""

# ── /profile ─────────────────────────────────────────────────────────────────

ASK_WEIGHT = "⚖️ Введи свой вес в кг _(например: 65)_"
ASK_HEIGHT = "📏 Введи рост в см _(например: 168)_"
ASK_GOAL   = """🎯 Какая цель?

📉 /lose — Похудеть
⚖️ /maintain — Поддержать вес
📈 /gain — Набрать массу"""
ASK_AGE    = "🎂 Введи свой возраст _(например: 25)_"

def profile_saved(char):
    kbzhu = calculate_daily_kbzhu(char)
    bmi   = calculate_bmi(char)
    return f"""
✅ *Профиль сохранён!*

👤 {char['name']}, {char['age']} лет
⚖️ Вес: {char['weight']} кг  |  📏 Рост: {char['height']} см
📊 ИМТ: {bmi} — {bmi_category(bmi)}

*Твоя дневная норма:*
🔥 Калории: {kbzhu['calories']} ккал
🥩 Белки:   {kbzhu['protein']} г
🧈 Жиры:    {kbzhu['fat']} г
🍞 Углеводы:{kbzhu['carbs']} г

Норма пересчитывается автоматически после каждой тренировки!
"""

# ── /food ────────────────────────────────────────────────────────────────────

FOOD_PROMPT = """
🍽 *Что поел твой персонаж?*

Можешь написать текстом:
_"гречка 200г с курицей 150г"_

Или отправь 📷 *фото тарелки* — AI сам разберётся!
"""

def food_result(char, food_data):
    kbzhu    = calculate_daily_kbzhu(char)
    cal_left = max(0, kbzhu['calories'] - char['calories_today'])
    p_left   = max(0, kbzhu['protein']  - char['protein_today'])
    f_left   = max(0, kbzhu['fat']      - char['fat_today'])
    c_left   = max(0, kbzhu['carbs']    - char['carbs_today'])

    pct = min(100, round(char['calories_today'] / kbzhu['calories'] * 100))

    return f"""
🍽 *{food_data['name']}*

🔥 {food_data['kcal']} ккал  •  🥩 Б: {food_data['protein']}г  •  🧈 Ж: {food_data['fat']}г  •  🍞 У: {food_data['carbs']}г

*Съедено за день:*
{stat_bar(char['calories_today'], kbzhu['calories'])} {pct}%
{char['calories_today']} / {kbzhu['calories']} ккал

*Осталось на сегодня:*
🔥 {cal_left} ккал  •  🥩 {p_left}г  •  🧈 {f_left}г  •  🍞 {c_left}г

✨ +{25 if pct<=110 else 10} XP  •  +5 🪙

_{food_data.get('comment','Отличный выбор!')}_
"""

def food_log(char):
    log = char.get("food_log_today", [])
    if not log:
        return "📋 Сегодня ещё ничего не записано. Используй /food!"
    lines = ["📋 *Еда за сегодня:*\n"]
    for i, item in enumerate(log, 1):
        lines.append(f"{i}. {item['time']} — {item['name']} ({item['kcal']} ккал)")
    kbzhu = calculate_daily_kbzhu(char)
    lines.append(f"\n*Итого:* {char['calories_today']} / {kbzhu['calories']} ккал")
    return "\n".join(lines)

# ── /workout ──────────────────────────────────────────────────────────────────

ASK_WORKOUT_TYPE = """
💪 *Какая тренировка?*

🏋️ /strength — Силовая
🏃 /cardio — Кардио
🧘 /yoga — Йога/растяжка
🚴 /cycling — Велосипед/велотренажёр
🏊 /swimming — Плавание
⚽ /sport — Командный спорт
"""

ASK_WORKOUT_INTENSITY = """
Интенсивность тренировки?

😌 /light — Лёгкая
💪 /medium — Средняя
🔥 /hard — Тяжёлая
"""

ASK_WORKOUT_DURATION = "⏱ Сколько минут тренировался? _(напиши число)_"

def workout_result(char, workout_type, intensity, duration, xp_gain, coin_gain, burned=0):
    intensity_names = {"light":"Лёгкая 😌","medium":"Средняя 💪","hard":"Тяжёлая 🔥"}
    eaten = char.get("calories_today", 0)
    total_burned = char.get("calories_burned_today", 0)
    balance = eaten - total_burned
    balance_str = f"+{balance}" if balance >= 0 else str(balance)
    return f"""
💥 *Тренировка засчитана!*

🏋️ {workout_type}
{intensity_names.get(intensity,'Средняя')} • ⏱ {duration} мин

🔥 Сожжено за тренировку: *{burned} ккал*

💪 Сила:      {stat_bar(char['strength'])} {char['strength']}
⚡ Энергия:   {stat_bar(char['energy'])} {char['energy']}
😄 Настроение:{stat_bar(char['mood'])} {char['mood']}

✨ +{xp_gain} XP  •  +{coin_gain} 🪙

*Баланс дня:*
🍽 Съедено: {eaten} ккал  •  🔥 Сожжено: {total_burned} ккал
⚖️ Баланс: {balance_str} ккал
"""

# ── /rest ─────────────────────────────────────────────────────────────────────

ASK_REST_TYPE = """
😴 *Как отдыхаешь?*

🛏 /sleep — Сон
📖 /book — Читаю книгу
📱 /phone — Сижу в телефоне
🚶 /activity — Смена деятельности
"""

ASK_SLEEP_HOURS = "🛏 Сколько часов поспал? _(например: 8)_"

def rest_result(char, rest_type):
    names = {"sleep":"Сон 🛏","book":"Чтение 📖","phone":"Телефон 📱","activity":"Смена деятельности 🚶"}
    tips  = {
        "sleep":    "Хороший сон — лучшее восстановление!",
        "book":     "Умный персонаж — сильный персонаж! 🧠",
        "phone":    "Иногда можно, но не злоупотребляй 😅",
        "activity": "Смена деятельности — тоже отдых!",
    }
    return f"""
✅ *{names.get(rest_type,'Отдых')} засчитан!*

⚡ Энергия:    {stat_bar(char['energy'])} {char['energy']}
🧠 Интеллект:  {stat_bar(char['intellect'])} {char['intellect']}
😄 Настроение: {stat_bar(char['mood'])} {char['mood']}

_{tips.get(rest_type,'Отдых важен!')}_
"""

# ── /measurements ─────────────────────────────────────────────────────────────

ASK_MEASUREMENTS = """
📏 *Замеры тела*

Вводи по одному — я спрошу каждый:
• Вес (кг)
• Талия (см)
• Грудь (см)
• Плечи (см)
• Ягодицы (см)
• Бёдра (см)
• Бицепс руки (см)
• Бицепс бедра (см)

Начнём! Введи вес в кг:
"""

MEASUREMENT_QUESTIONS = [
    ("weight_kg",    "⚖️ Вес (кг):"),
    ("waist",        "📏 Талия (см):"),
    ("chest",        "📏 Грудь (см):"),
    ("shoulders",    "📏 Плечи (см):"),
    ("glutes",       "📏 Ягодицы (см):"),
    ("hips",         "📏 Бёдра (см):"),
    ("bicep_arm",    "📏 Бицепс руки (см):"),
    ("bicep_leg",    "📏 Бицепс бедра (см):"),
]

def measurements_result(char, data, prev_data):
    lines = ["📊 *Замеры сохранены!* +30 XP  +15 🪙\n"]
    labels = {
        "weight_kg":"⚖️ Вес","waist":"Талия","chest":"Грудь",
        "shoulders":"Плечи","glutes":"Ягодицы","hips":"Бёдра",
        "bicep_arm":"Бицепс руки","bicep_leg":"Бицепс бедра"
    }
    for key, label in labels.items():
        val = data.get(key, "—")
        if prev_data and key in prev_data:
            diff = round(float(val) - float(prev_data[key]), 1)
            sign = "+" if diff > 0 else ""
            lines.append(f"{label}: *{val}* ({sign}{diff})")
        else:
            lines.append(f"{label}: *{val}*")
    lines.append("\n_Следующие замеры через неделю!_")
    return "\n".join(lines)

# ── /status ───────────────────────────────────────────────────────────────────

def status_message(char):
    avatar  = get_avatar(char)
    level   = char["level"]
    xp      = char["xp"]
    xp_need = level * 100
    kbzhu   = calculate_daily_kbzhu(char)
    cal_pct = min(100, round(char.get("calories_today",0) / kbzhu["calories"] * 100))

    inv = char.get("inventory", [])
    inv_str = " ".join([SHOP_ITEMS[i]["name"].split()[0] for i in inv]) if inv else "пусто"

    return f"""
{avatar} *{char['name']}*
{level_title(level)} — Уровень {level}
[{stat_bar(xp, xp_need)}] {xp}/{xp_need} XP  •  🪙 {char.get('coins',0)}

━━━━━━━━━━━━━━━━━
{energy_emoji(char['energy'])} Энергия:     {stat_bar(char['energy'])} {char['energy']}
💪 Сила:         {stat_bar(char['strength'])} {char['strength']}
🧠 Интеллект:    {stat_bar(char['intellect'])} {char['intellect']}
{mood_emoji(char['mood'])} Настроение:  {stat_bar(char['mood'])} {char['mood']}
━━━━━━━━━━━━━━━━━

🍽 *Питание сегодня:*
{stat_bar(char.get('calories_today',0), kbzhu['calories'])} {cal_pct}%
{char.get('calories_today',0)} / {kbzhu['calories']} ккал

🎒 Инвентарь: {inv_str}

📈 Тренировок всего: {char.get('total_workouts',0)}
🍎 Приёмов пищи: {char.get('total_meals',0)}

_{_status_tip(char)}_
"""

def _status_tip(char):
    kbzhu = calculate_daily_kbzhu(char)
    cal   = char.get("calories_today",0)
    if char["energy"] < 30: return "⚠️ Срочно поешь — герой без сил! /food"
    if cal < kbzhu["calories"] * 0.5: return "🍽 Ты мало ел сегодня. Не забывай про питание!"
    if cal > kbzhu["calories"] * 1.2: return "⚠️ Перебор калорий! Полегче с едой 😅"
    if char["workouts_today"] == 0: return "💪 Сегодня ещё нет тренировки. Давай — /workout!"
    return "🔥 Всё идёт отлично. Так держать!"

# ── /shop ─────────────────────────────────────────────────────────────────────

def shop_message(char):
    coins = char.get("coins", 0)
    inv   = char.get("inventory", [])
    lines = [f"🛍 *Магазин*  •  У тебя: 🪙 {coins}\n"]
    for key, item in SHOP_ITEMS.items():
        owned = "✅ Куплено" if key in inv else f"{item['price']} 🪙"
        lines.append(f"{item['name']} — {item['desc']}\n  /{key} • {owned}\n")
    return "\n".join(lines)

def levelup_message(char):
    return f"""
🎉 *LEVEL UP!*

{get_avatar(char)} Уровень *{char['level']}*!
{level_title(char['level'])}

⚡ +20 Энергия  •  😄 +20 Настроение  •  🧠 +5 Интеллект  •  🪙 +50 монет

Ты становишься лучше каждый день 💥
"""
