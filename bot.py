"""
Life Simulator Fitness Bot
==========================
Run:
    pip install -r requirements.txt
    python bot.py

Set your token in BOT_TOKEN below (or via env variable).
"""

import os
import telebot

import storage
import models
import messages

# ──────────────────────────────────────────────
#  Config
# ──────────────────────────────────────────────

BOT_TOKEN = os.getenv("BOT_TOKEN", "7686404527:AAHzpIKFgOtFRbC5FY-jaRVY3ZFK8qSziZs")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Tracks users mid-flow (waiting for name / food / workout text)
_waiting_for: dict[int, str] = {}


# ──────────────────────────────────────────────
#  /start
# ──────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def cmd_start(message):
    user_id = message.from_user.id

    if storage.user_exists(user_id):
        char = storage.get_user(user_id)
        bot.send_message(user_id, messages.WELCOME_BACK.format(name=char["name"]))
    else:
        bot.send_message(user_id, messages.WELCOME_NEW)
        _waiting_for[user_id] = "name"


# ──────────────────────────────────────────────
#  /food
# ──────────────────────────────────────────────

@bot.message_handler(commands=["food"])
def cmd_food(message):
    user_id = message.from_user.id
    if not _check_profile(user_id):
        return
    bot.send_message(user_id, messages.FOOD_PROMPT)
    _waiting_for[user_id] = "food"


# ──────────────────────────────────────────────
#  /workout
# ──────────────────────────────────────────────

@bot.message_handler(commands=["workout"])
def cmd_workout(message):
    user_id = message.from_user.id
    if not _check_profile(user_id):
        return
    bot.send_message(user_id, messages.WORKOUT_PROMPT)
    _waiting_for[user_id] = "workout"


@bot.message_handler(commands=["rest"])
def cmd_rest(message):
    user_id = message.from_user.id
    if not _check_profile(user_id):
        return
    char     = storage.get_user(user_id)
    prev_lvl = char["level"]
    char     = models.do_rest(char)
    storage.save_user(user_id, char)
    bot.send_message(user_id, messages.rest_result(char))
    _check_and_notify_levelup(user_id, char, prev_lvl)


# ──────────────────────────────────────────────
#  /status
# ──────────────────────────────────────────────

@bot.message_handler(commands=["status"])
def cmd_status(message):
    user_id = message.from_user.id
    if not _check_profile(user_id):
        return
    char = storage.get_user(user_id)
    bot.send_message(user_id, messages.status_message(char))


# ──────────────────────────────────────────────
#  Text input handler (name / food / workout)
# ──────────────────────────────────────────────

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = message.from_user.id
    text    = message.text.strip()
    state   = _waiting_for.get(user_id)

    # ── Waiting for character name ──
    if state == "name":
        char = models.new_character(text)
        storage.save_user(user_id, char)
        _waiting_for.pop(user_id, None)
        bot.send_message(user_id, messages.character_created(text))
        return

    # ── Waiting for food description ──
    if state == "food":
        char          = storage.get_user(user_id)
        prev_lvl      = char["level"]
        char, category = models.eat_food(char, text)
        storage.save_user(user_id, char)
        _waiting_for.pop(user_id, None)
        bot.send_message(user_id, messages.food_result(char, text, category))
        _check_and_notify_levelup(user_id, char, prev_lvl)
        return

    # ── Waiting for workout description ──
    if state == "workout":
        char     = storage.get_user(user_id)
        prev_lvl = char["level"]
        char     = models.do_workout(char, text)
        storage.save_user(user_id, char)
        _waiting_for.pop(user_id, None)
        bot.send_message(user_id, messages.workout_result(char, text))
        _check_and_notify_levelup(user_id, char, prev_lvl)
        return

    # ── Unknown input ──
    bot.send_message(user_id, (
        "🤖 Не понял команду.\n\n"
        "Попробуй:\n"
        "• /food — поесть\n"
        "• /workout — тренировка\n"
        "• /rest — отдохнуть\n"
        "• /status — посмотреть персонажа"
    ))


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _check_profile(user_id: int) -> bool:
    """Return True if profile exists, else prompt to create one."""
    if not storage.user_exists(user_id):
        bot.send_message(
            user_id,
            "👾 Сначала создай персонажа командой /start!"
        )
        return False
    return True


def _check_and_notify_levelup(user_id: int, char: dict, prev_level: int) -> None:
    if char["level"] > prev_level:
        bot.send_message(user_id, messages.levelup_message(char))


# ──────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("🎮 Life Simulator Bot запущен...")
    bot.infinity_polling()
