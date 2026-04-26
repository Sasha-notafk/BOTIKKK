import json
import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# 🔐 TOKEN через Render ENV
TOKEN = os.getenv("BOT_TOKEN")

# 📦 загрузка данных
with open("data.json", "r", encoding="utf-8") as f:
    games = json.load(f)

state = {}

def get_state(chat_id):
    if chat_id not in state:
        state[chat_id] = {}
    return state[chat_id]


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧠 Dota 2", callback_data="game_dota")],
        [InlineKeyboardButton("🔫 Brawl Stars", callback_data="game_brawl")],
        [InlineKeyboardButton("🏰 Clash Royale", callback_data="game_clash")]
    ]

    await update.message.reply_text(
        "🎮 Выбери игру:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# выбор игры
async def choose_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    chat_id = q.message.chat.id
    st = get_state(chat_id)

    st.clear()
    st["game"] = q.data.split("_")[1]

    await q.edit_message_text("👥 Введи количество игроков:")


# ввод данных
async def setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    st = get_state(chat_id)

    text = update.message.text

    if not text.isdigit():
        return

    if "players" not in st:
        st["players"] = int(text)
        await update.message.reply_text("🕵️ Введи количество шпионов:")
    else:
        st["spies"] = int(text)
        await start_game(update, context)


# старт игры
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    st = get_state(chat_id)

    game = games[st["game"]]

    st["index"] = 0

    st["main_hero"] = random.choice(game["heroes"])

    roles = ["spy"] * st["spies"] + ["player"] * (st["players"] - st["spies"])
    random.shuffle(roles)

    st["roles"] = roles

    kb = [[InlineKeyboardButton("👀 Посмотреть роль", callback_data="show")]]

    await update.message.reply_text(
        f"🎮 {st['game'].upper()}\n👉 Игрок 1",
        reply_markup=InlineKeyboardMarkup(kb)
    )


# показать роль
async def show_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    chat_id = q.message.chat.id
    st = get_state(chat_id)

    role = st["roles"][st["index"]]

    if role == "spy":
        text = "🕵️‍♂️ ТЫ ШПИОН"
    else:
        hero = st["main_hero"]
        text = f"🎭 {hero['en']} - {hero['ru']}"

    msg = await context.bot.send_message(chat_id=chat_id, text=text)

    import asyncio
    await asyncio.sleep(2)
    await msg.delete()

    st["index"] += 1

    if st["index"] >= st["players"]:
        kb = [[InlineKeyboardButton("🔁 Играть снова", callback_data="restart")]]

        await context.bot.send_message(
            chat_id=chat_id,
            text="🔥 Игра завершена!",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    kb = [[InlineKeyboardButton("👀 Посмотреть роль", callback_data="show")]]

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"👉 Игрок {st['index'] + 1}",
        reply_markup=InlineKeyboardMarkup(kb)
    )


# рестарт
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    chat_id = q.message.chat.id
    st = get_state(chat_id)
    st.clear()

    keyboard = [
        [InlineKeyboardButton("🧠 Dota 2", callback_data="game_dota")],
        [InlineKeyboardButton("🔫 Brawl Stars", callback_data="game_brawl")],
        [InlineKeyboardButton("🏰 Clash Royale", callback_data="game_clash")]
    ]

    await q.edit_message_text(
        "🎮 Выбери игру:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# app
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(choose_game, pattern="^game_"))
app.add_handler(CallbackQueryHandler(show_role, pattern="^show$"))
app.add_handler(CallbackQueryHandler(restart, pattern="^restart$"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, setup))

app.run_polling()