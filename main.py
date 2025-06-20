from keep_alive import keep_alive
import telebot
from telebot import types
import random

TOKEN = "8161107014:AAH1I0srDbneOppDw4AsE2kEYtNtk7CRjOw"
bot = telebot.TeleBot(TOKEN)

user_balances = {}
user_games = {}
ADMIN_ID = 5815294733  # O'z Telegram ID'ingiz

# --- /start ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_balances.setdefault(user_id, 1000)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('💰 Balance', '🎮 Play Mines')
    markup.add('➕ Pay')
    bot.send_message(message.chat.id, "👋 Xush kelibsiz! Mines o‘yinini boshlang!", reply_markup=markup)

# --- Balans ---
@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):
    user_id = message.from_user.id
    bal = user_balances.get(user_id, 0)
    bot.send_message(message.chat.id, f"💸 Balansingiz: {bal} so‘m")

# --- O‘yin boshlash ---
@bot.message_handler(func=lambda m: m.text == "🎮 Play Mines")
def start_mines(message):
    user_id = message.from_user.id
    if user_id in user_games:
        bot.send_message(message.chat.id, "⛔ Avvalgi o‘yinni tugating yoki pulni yeching.")
        return
    msg = bot.send_message(message.chat.id, "💵 Stavka miqdorini kiriting (min 500):")
    bot.register_next_step_handler(msg, init_mines)

def init_mines(message):
    try:
        user_id = message.from_user.id
        stake = int(message.text)
        if stake < 500:
            bot.send_message(message.chat.id, "❌ Kamida 500 so‘m tikish kerak.")
            return
        if user_balances.get(user_id, 0) < stake:
            bot.send_message(message.chat.id, "❌ Yetarli balans yo‘q.")
            return

        user_balances[user_id] -= stake
        bombs = random.sample(range(25), 3)
        user_games[user_id] = {
            'stake': stake,
            'bombs': bombs,
            'opened': [],
            'multiplier': 1.0
        }
        send_mines_board(message.chat.id, user_id, bomb_triggered=False)

    except ValueError:
        bot.send_message(message.chat.id, "❌ Raqam kiriting.")

# --- Mines taxta chizish ---
def send_mines_board(chat_id, user_id, bomb_triggered=False):
    game = user_games.get(user_id)
    if not game:
        return

    markup = types.InlineKeyboardMarkup(row_width=5)
    buttons = []

    for i in range(25):
        if i in game['opened']:
            if bomb_triggered and i in game['bombs']:
                btn = types.InlineKeyboardButton("💣", callback_data="ignore")
            else:
                btn = types.InlineKeyboardButton("✅", callback_data="ignore")
        else:
            btn = types.InlineKeyboardButton(str(i + 1), callback_data=f"open_{i}")
        buttons.append(btn)

    for i in range(0, 25, 5):
        markup.row(*buttons[i:i + 5])

    if not bomb_triggered:
        markup.add(types.InlineKeyboardButton("💰 Pulni yechish", callback_data="cashout"))

    text = (
        f"🎮 Mines o‘yini
"
        f"💣 Bombalar: 3
"
        f"💵 Stavka: {game['stake']} so‘m
"
        f"📈 Multiplikator: x{round(game['multiplier'], 2)}"
    )
    bot.send_message(chat_id, text, reply_markup=markup)

# --- Katakka bosish ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    if user_id not in user_games:
        bot.answer_callback_query(call.id, "⛔ O‘yin topilmadi.")
        return

    game = user_games[user_id]

    if call.data == "cashout":
        win = min(int(game['stake'] * game['multiplier']), int(game['stake'] * 2))
        user_balances[user_id] += win
        del user_games[user_id]
        bot.edit_message_text(f"💰 {win} so‘m yutdingiz! Tabriklaymiz!", call.message.chat.id, call.message.message_id)
        return

    if call.data.startswith("open_"):
        idx = int(call.data.split("_")[1])
        if idx in game['opened']:
            bot.answer_callback_query(call.id, "✅ Bu katak ochilgan.")
            return

        if idx in game['bombs']:
            game['opened'] = list(set(game['opened'] + game['bombs']))
            send_mines_board(call.message.chat.id, user_id, bomb_triggered=True)
            del user_games[user_id]
            bot.edit_message_text("💥 Bomba topildi! Siz yutqazdingiz.", call.message.chat.id, call.message.message_id)
            return

        game['opened'].append(idx)
        game['multiplier'] *= 1.08
        send_mines_board(call.message.chat.id, user_id, bomb_triggered=False)

# --- Admin balans to‘ldirish ---
@bot.message_handler(func=lambda m: m.text == "➕ Pay")
def pay(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Bu admin uchun.")
        return
    msg = bot.send_message(message.chat.id, "🆔 Foydalanuvchi ID sini yozing:")
    bot.register_next_step_handler(msg, ask_amount)

def ask_amount(message):
    try:
        user_id = int(message.text)
        msg = bot.send_message(message.chat.id, "💵 Qancha pul qo‘shamiz?")
        bot.register_next_step_handler(msg, lambda m: add_balance(m, user_id))
    except ValueError:
        bot.send_message(message.chat.id, "❌ ID noto‘g‘ri.")

def add_balance(message, user_id):
    try:
        amount = int(message.text)
        user_balances[user_id] = user_balances.get(user_id, 0) + amount
        bot.send_message(message.chat.id, f"✅ {amount} so‘m {user_id} ga qo‘shildi.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Miqdor noto‘g‘ri.")

# --- /id komandasi ---
@bot.message_handler(commands=['id'])
def show_id(message):
    bot.send_message(message.chat.id, f"🆔 Sizning ID: `{message.from_user.id}`", parse_mode='Markdown')

# --- Botni ishga tushurish ---
print("🧐 Bot ishga tushdi...")
keep_alive()
bot.polling(none_stop=True)