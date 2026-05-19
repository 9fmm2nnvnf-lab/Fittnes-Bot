"""
Life Simulator Fitness Bot — v2.0
Run: python bot.py
Env vars: BOT_TOKEN, OPENAI_API_KEY
"""
import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

import storage, models, messages
from ai_helper import analyze_food_text, analyze_food_photo

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# state machine: user_id → {step, data}
_state: dict[int, dict] = {}

def set_state(uid, step, **data):
    _state[uid] = {"step": step, **data}

def get_state(uid):
    return _state.get(uid, {})

def clear_state(uid):
    _state.pop(uid, None)


# ── Keyboards ────────────────────────────────────────────────────────────────

def kb_gender():
    m = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    m.add(KeyboardButton("👩 Женский"), KeyboardButton("👨 Мужской"))
    return m

def kb_body_type():
    m = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    m.add(KeyboardButton("🦴 Худощавый"), KeyboardButton("🙂 Нормальный"))
    m.add(KeyboardButton("💪 Плотный"),   KeyboardButton("🐻 Массивный"))
    return m

def kb_goal():
    m = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    m.add(KeyboardButton("📉 Похудеть"), KeyboardButton("⚖️ Поддержать"), KeyboardButton("📈 Набрать"))
    return m

def kb_workout_type():
    m = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    m.add(KeyboardButton("🏋️ Силовая"),    KeyboardButton("🏃 Кардио"))
    m.add(KeyboardButton("🧘 Йога"),        KeyboardButton("🚴 Велосипед"))
    m.add(KeyboardButton("🏊 Плавание"),    KeyboardButton("⚽ Командный спорт"))
    return m

def kb_intensity():
    m = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    m.add(KeyboardButton("😌 Лёгкая"), KeyboardButton("💪 Средняя"), KeyboardButton("🔥 Тяжёлая"))
    return m

def kb_rest_type():
    m = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    m.add(KeyboardButton("🛏 Сон"),    KeyboardButton("📖 Читаю книгу"))
    m.add(KeyboardButton("📱 Телефон"), KeyboardButton("🚶 Смена деятельности"))
    return m

def kb_main():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton("🍽 Еда"),      KeyboardButton("💪 Тренировка"))
    m.add(KeyboardButton("😴 Отдых"),    KeyboardButton("📊 Статус"))
    m.add(KeyboardButton("📏 Замеры"),   KeyboardButton("🛍 Магазин"))
    return m

def remove_kb():
    return ReplyKeyboardRemove()


# ── /start ───────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def cmd_start(message):
    uid = message.from_user.id
    if storage.user_exists(uid):
        char = storage.get_user(uid)
        bot.send_message(uid, messages.WELCOME_BACK.format(name=char["name"]), reply_markup=kb_main())
    else:
        bot.send_message(uid, messages.WELCOME_NEW)
        set_state(uid, "reg_name")


# ── /profile ─────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["profile"])
def cmd_profile(message):
    uid = message.from_user.id
    if not _check(uid): return
    bot.send_message(uid, messages.ASK_WEIGHT, reply_markup=remove_kb())
    set_state(uid, "profile_weight")


# ── /food ────────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["food"])
def cmd_food(message):
    uid = message.from_user.id
    if not _check(uid): return
    bot.send_message(uid, messages.FOOD_PROMPT, reply_markup=remove_kb())
    set_state(uid, "food_input")

@bot.message_handler(commands=["log"])
def cmd_log(message):
    uid = message.from_user.id
    if not _check(uid): return
    char = storage.get_user(uid)
    bot.send_message(uid, messages.food_log(char))


# ── /workout ─────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["workout"])
def cmd_workout(message):
    uid = message.from_user.id
    if not _check(uid): return
    bot.send_message(uid, messages.ASK_WORKOUT_TYPE, reply_markup=kb_workout_type())
    set_state(uid, "workout_type")


# ── /rest ─────────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["rest"])
def cmd_rest(message):
    uid = message.from_user.id
    if not _check(uid): return
    bot.send_message(uid, messages.ASK_REST_TYPE, reply_markup=kb_rest_type())
    set_state(uid, "rest_type")


# ── /measurements ─────────────────────────────────────────────────────────────

@bot.message_handler(commands=["measurements"])
def cmd_measurements(message):
    uid = message.from_user.id
    if not _check(uid): return
    bot.send_message(uid, messages.ASK_MEASUREMENTS, reply_markup=remove_kb())
    set_state(uid, "measure", idx=0, data={})


# ── /status ───────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["status"])
def cmd_status(message):
    uid = message.from_user.id
    if not _check(uid): return
    char = storage.get_user(uid)
    bot.send_message(uid, messages.status_message(char), reply_markup=kb_main())


# ── /shop ─────────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["shop"])
def cmd_shop(message):
    uid = message.from_user.id
    if not _check(uid): return
    char = storage.get_user(uid)
    bot.send_message(uid, messages.shop_message(char))

@bot.message_handler(commands=list(models.SHOP_ITEMS.keys()))
def cmd_buy(message):
    uid      = message.from_user.id
    if not _check(uid): return
    item_key = message.text.lstrip("/").split()[0]
    char     = storage.get_user(uid)
    ok, msg  = models.buy_item(char, item_key)
    storage.save_user(uid, char)
    bot.send_message(uid, ("✅ " if ok else "❌ ") + msg)


# ── Photo handler (food from photo) ──────────────────────────────────────────

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    uid   = message.from_user.id
    state = get_state(uid)
    if not storage.user_exists(uid):
        bot.send_message(uid, "Сначала создай персонажа — /start"); return

    if state.get("step") == "food_input":
        bot.send_message(uid, "🔍 Анализирую фото...", reply_markup=remove_kb())
        file_id   = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        photo_bytes = bot.download_file(file_info.file_path)

        result = analyze_food_photo(photo_bytes)
        if result:
            _process_food(uid, result)
        else:
            bot.send_message(uid, "😕 Не смог распознать еду. Попробуй описать текстом — /food")
        clear_state(uid)
    else:
        bot.send_message(uid, "Отправь фото еды через команду /food 🍽")


# ── Main text handler ─────────────────────────────────────────────────────────

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid   = message.from_user.id
    text  = message.text.strip()
    state = get_state(uid)
    step  = state.get("step")

    # Кнопки главного меню
    menu_map = {
        "🍽 Еда": cmd_food, "💪 Тренировка": cmd_workout,
        "😴 Отдых": cmd_rest, "📊 Статус": cmd_status,
        "📏 Замеры": cmd_measurements, "🛍 Магазин": cmd_shop,
    }
    if text in menu_map and step is None:
        menu_map[text](message); return

    # ── Регистрация ──────────────────────────────────────────────────────────
    if step == "reg_name":
        char = models.DEFAULT_CHARACTER.copy()
        char["name"] = text
        char["real_name"] = text
        storage.save_user(uid, char)
        bot.send_message(uid, messages.ask_gender().format(name=text), reply_markup=kb_gender())
        set_state(uid, "reg_gender")
        return

    if step == "reg_gender":
        char = storage.get_user(uid)
        char["gender"] = "female" if "Женский" in text else "male"
        storage.save_user(uid, char)
        bot.send_message(uid, messages.ASK_AGE, reply_markup=remove_kb())
        set_state(uid, "reg_age")
        return

    if step == "reg_age":
        char = storage.get_user(uid)
        try:
            char["age"] = int(text)
        except:
            bot.send_message(uid, "Введи число, например: 25"); return
        storage.save_user(uid, char)
        bot.send_message(uid, messages.ask_body_type(), reply_markup=kb_body_type())
        set_state(uid, "reg_body")
        return

    if step == "reg_body":
        char = storage.get_user(uid)
        body_map = {"Худощавый":"slim","Нормальный":"normal","Плотный":"thick","Массивный":"heavy"}
        for k, v in body_map.items():
            if k in text: char["body_type"] = v; break
        else: char["body_type"] = "normal"
        from datetime import datetime
        char["created_at"] = datetime.now().isoformat()
        char["last_action"] = datetime.now().isoformat()
        storage.save_user(uid, char)
        bot.send_message(uid, messages.character_created(char), reply_markup=kb_main())
        clear_state(uid)
        return

    # ── Профиль ──────────────────────────────────────────────────────────────
    if step == "profile_weight":
        try:
            w = float(text.replace(",","."))
            char = storage.get_user(uid)
            char["weight"] = w
            storage.save_user(uid, char)
            bot.send_message(uid, messages.ASK_HEIGHT)
            set_state(uid, "profile_height")
        except:
            bot.send_message(uid, "Введи число, например: 65")
        return

    if step == "profile_height":
        try:
            h = int(text)
            char = storage.get_user(uid)
            char["height"] = h
            storage.save_user(uid, char)
            bot.send_message(uid, messages.ASK_GOAL, reply_markup=kb_goal())
            set_state(uid, "profile_goal")
        except:
            bot.send_message(uid, "Введи число, например: 168")
        return

    if step == "profile_goal":
        char = storage.get_user(uid)
        if "Похудеть" in text:   char["goal"] = "lose"
        elif "Набрать" in text:  char["goal"] = "gain"
        else:                    char["goal"] = "maintain"
        storage.save_user(uid, char)
        bot.send_message(uid, messages.profile_saved(char), reply_markup=kb_main())
        clear_state(uid)
        return

    # ── Еда ──────────────────────────────────────────────────────────────────
    if step == "food_input":
        bot.send_message(uid, "🔍 Считаю КБЖУ...", reply_markup=remove_kb())
        result = analyze_food_text(text)
        if result:
            _process_food(uid, result)
        else:
            bot.send_message(uid, "😕 Не смог посчитать. Попробуй точнее, например: _гречка 200г, курица 150г_")
        clear_state(uid)
        return

    # ── Тренировка ───────────────────────────────────────────────────────────
    if step == "workout_type":
        wmap = {
            "Силовая":"Силовая 🏋️","Кардио":"Кардио 🏃","Йога":"Йога 🧘",
            "Велосипед":"Велосипед 🚴","Плавание":"Плавание 🏊","Командный":"Командный спорт ⚽"
        }
        wtype = next((v for k,v in wmap.items() if k in text), text)
        bot.send_message(uid, messages.ASK_WORKOUT_INTENSITY, reply_markup=kb_intensity())
        set_state(uid, "workout_intensity", wtype=wtype)
        return

    if step == "workout_intensity":
        imap = {"Лёгкая":"light","Средняя":"medium","Тяжёлая":"hard"}
        intensity = next((v for k,v in imap.items() if k in text), "medium")
        bot.send_message(uid, messages.ASK_WORKOUT_DURATION, reply_markup=remove_kb())
        set_state(uid, "workout_duration", wtype=state["wtype"], intensity=intensity)
        return

    if step == "workout_duration":
        try:
            dur = int(text)
        except:
            bot.send_message(uid, "Введи число минут, например: 45"); return
        char    = storage.get_user(uid)
        prev    = char["level"]
        char, xp_g, coin_g = models.do_workout(char, state["wtype"], state["intensity"], dur)
        storage.save_user(uid, char)
        clear_state(uid)
        bot.send_message(uid, messages.workout_result(char, state["wtype"], state["intensity"], dur, xp_g, coin_g), reply_markup=kb_main())
        if char.get("_leveled_up"): bot.send_message(uid, messages.levelup_message(char))
        return

    # ── Отдых ────────────────────────────────────────────────────────────────
    if step == "rest_type":
        rmap = {"Сон":"sleep","книгу":"book","Телефон":"phone","Смена":"activity"}
        rtype = next((v for k,v in rmap.items() if k in text), "activity")
        if rtype == "sleep":
            bot.send_message(uid, messages.ASK_SLEEP_HOURS, reply_markup=remove_kb())
            set_state(uid, "rest_hours", rtype=rtype)
        else:
            _do_rest(uid, rtype, 0)
            clear_state(uid)
        return

    if step == "rest_hours":
        try:
            hours = float(text.replace(",","."))
        except:
            hours = 7
        _do_rest(uid, state["rtype"], hours)
        clear_state(uid)
        return

    # ── Замеры ───────────────────────────────────────────────────────────────
    if step == "measure":
        idx  = state.get("idx", 0)
        data = state.get("data", {})
        key, label = messages.MEASUREMENT_QUESTIONS[idx]
        try:
            data[key] = float(text.replace(",","."))
        except:
            bot.send_message(uid, f"Введи число для: {label}"); return

        idx += 1
        if idx < len(messages.MEASUREMENT_QUESTIONS):
            _, next_label = messages.MEASUREMENT_QUESTIONS[idx]
            bot.send_message(uid, next_label)
            set_state(uid, "measure", idx=idx, data=data)
        else:
            char      = storage.get_user(uid)
            prev_data = char.get("measurements", {})
            char      = models.save_measurements(char, data)
            storage.save_user(uid, char)
            bot.send_message(uid, messages.measurements_result(char, data, prev_data), reply_markup=kb_main())
            clear_state(uid)
        return

    # ── Неизвестное ──────────────────────────────────────────────────────────
    bot.send_message(uid, "🤖 Используй кнопки меню или команды:\n/food /workout /rest /status /measurements /shop /profile", reply_markup=kb_main())


# ── Helpers ──────────────────────────────────────────────────────────────────

def _check(uid):
    if not storage.user_exists(uid):
        bot.send_message(uid, "👾 Сначала создай персонажа — /start")
        return False
    return True

def _process_food(uid, result):
    char = storage.get_user(uid)
    char = models.add_food(char, result["name"], result["kcal"],
                           result["protein"], result["fat"], result["carbs"])
    storage.save_user(uid, char)
    bot.send_message(uid, messages.food_result(char, result), reply_markup=kb_main())
    if char.get("_leveled_up"):
        bot.send_message(uid, messages.levelup_message(char))

def _do_rest(uid, rtype, hours):
    char = storage.get_user(uid)
    char = models.do_rest(char, rtype, hours)
    storage.save_user(uid, char)
    bot.send_message(uid, messages.rest_result(char, rtype), reply_markup=kb_main())
    if char.get("_leveled_up"):
        bot.send_message(uid, messages.levelup_message(char))


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🎮 Life Simulator Bot v2.0 запущен...")
    bot.infinity_polling()
