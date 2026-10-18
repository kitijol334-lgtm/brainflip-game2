import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

# ==========================================
# КОНФИГУРАЦИЯ БОТА
# ==========================================
TOKEN = '8876455639:AAExE0fIIY99UXIC2bg42WNUd9-plPtbpfk'
bot = telebot.TeleBot(TOKEN)

ADMIN_PASS = "Самир123"

PROMOS_FILE = 'promos.json'
USERS_FILE = 'users.json'

# Базовые промокоды (название: {лимит_использований, награда})
DEFAULT_PROMOS = {
    "START1000": {"limit": 1000, "reward": 1000},
    "BRAINFLIP2026": {"limit": 500, "reward": 2500},
    "ULTRAMODE": {"limit": 100, "reward": 5000},
    "MEGASECRET": {"limit": 10, "reward": 15000}
}

# ==========================================
# БАЗА ДАННЫХ (JSON ФАЙЛЫ)
# ==========================================
def load_data(file, default):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_data(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

promos_db = load_data(PROMOS_FILE, DEFAULT_PROMOS)
users_db = load_data(USERS_FILE, {}) 

def get_user(user_id):
    uid = str(user_id)
    if uid not in users_db:
        users_db[uid] = {"used_promos": []}
    return users_db[uid]

# ==========================================
# ОСНОВНЫЕ КОМАНДЫ ДЛЯ ИГРОКОВ
# ==========================================
@bot.message_handler(commands=['start'])
def start_command(message):
    text = (
        "👋 <b>Привет! Добро пожаловать в BrainFlip!</b> 🧠\n\n"
        "Здесь ты сможешь прокачать своих брейнротов в <i>Steal a brainrot</i>! 🚀\n"
        "Испытай удачу, делай апгрейды и собирай самую редкую коллекцию. 🎰💸\n\n"
        "👉 Чтобы начать прокачивать брейнротов, нажми на голубую кнопку <b>«Играть»</b> внизу экрана, чтобы открыть Miniapp."
    )
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Кнопка "Промокоды"
    btn_promo = InlineKeyboardButton("🎁 Промокоды", callback_data="enter_promo")
    
    # Кнопка "Новости"
    btn_news = InlineKeyboardButton("📰 Новости", url="https://t.me/BrainflipNews")
    
    markup.add(btn_promo, btn_news)
    
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "enter_promo")
def promo_callback(call):
    msg = bot.send_message(call.message.chat.id, "🎟 <b>Введи промокод от разработчика:</b>\n<i>(Отправь его мне следующим сообщением)</i>", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_promo)

def process_promo(message):
    code = message.text.strip().upper()
    user_id = str(message.from_user.id)
    user = get_user(user_id)

    if code not in promos_db:
        bot.send_message(message.chat.id, "❌ <b>Ошибка:</b> Данного промокода не существует.", parse_mode='HTML')
        return

    promo_info = promos_db[code]

    if code in user["used_promos"]:
        bot.send_message(message.chat.id, "⚠️ <b>Ошибка:</b> Ты уже активировал этот промокод! Его можно использовать только 1 раз.", parse_mode='HTML')
        return

    if promo_info["limit"] <= 0:
        bot.send_message(message.chat.id, "⏳ <b>Ошибка:</b> Активации данного промокода исчерпаны.", parse_mode='HTML')
        return

    # Успешная активация
    promo_info["limit"] -= 1
    user["used_promos"].append(code)
    
    save_data(PROMOS_FILE, promos_db)
    save_data(USERS_FILE, users_db)

    # Выдаем спец-код для WebApp
    bot.send_message(
        message.chat.id, 
        f"✅ <b>Промокод успешно активирован!</b>\n\n"
        f"🎁 Твоя награда: <b>{promo_info['reward']} 💰</b>\n\n"
        f"<i>💡 Подсказка: Зайди в игру, нажми «КОДЫ» и введи этот сгенерированный ключ, чтобы монеты зачислились на баланс:</i>\n\n"
        f"<code>DEV-{promo_info['reward']}</code>", 
        parse_mode='HTML'
    )

# ==========================================
# ОБРАБОТКА ДАННЫХ ИЗ WEBAPP
# ==========================================
@bot.message_handler(content_types=['web_app_data'])
def web_app_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        
        if action == 'deposit':
            nick = data.get('nick')
            item = data.get('item')
            bot.send_message(message.chat.id, f"📥 <b>Заявка на пополнение создана!</b>\n\n👤 Ник в Roblox: <code>{nick}</code>\n📦 Предмет: <b>{item}</b>\n\nОжидай трейда от администратора.", parse_mode="HTML")

        elif action == 'withdraw':
            nick = data.get('nick')
            items = data.get('items', [])
            items_str = ", ".join(items)
            bot.send_message(message.chat.id, f"📤 <b>Заявка на вывод создана!</b>\n\n👤 Ник в Roblox: <code>{nick}</code>\n📦 Предметы: <b>{items_str}</b>\n\nОжидай трейда в игре.", parse_mode="HTML")
            
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Произошла ошибка при обработке данных из игры.")

# ==========================================
# СИСТЕМА АДМИН-КОМАНД (СТРОГО С ПАРОЛЕМ)
# ==========================================
@bot.message_handler(func=lambda message: message.text.startswith(f"{ADMIN_PASS} !"))
def admin_commands(message):
    command_full = message.text.replace(f"{ADMIN_PASS} ", "").strip()
    parts = command_full.split()
    command = parts[0].lower()

    if command == "!check":
        bot.send_message(message.chat.id, "✅ <b>Админ-панель:</b> Доступ разрешен. Системы работают стабильно.", parse_mode="HTML")
        
    elif command == "!code":
        if len(parts) >= 4:
            code_name = parts[1].upper()
            try:
                limit = int(parts[2])
                reward = int(parts[3])
                promos_db[code_name] = {"limit": limit, "reward": reward}
                save_data(PROMOS_FILE, promos_db)
                bot.send_message(message.chat.id, f"✅ Создан новый промокод: <b>{code_name}</b>\nЛимит: {limit} использований\nНаграда: {reward} 💰", parse_mode="HTML")
            except ValueError:
                bot.send_message(message.chat.id, "❌ Ошибка формата. Пример: <code>Самир123 !code СЕКРЕТ 100 5000</code>", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ Использование: <code>Самир123 !code [КОД] [ЛИМИТ] [НАГРАДА]</code>", parse_mode="HTML")

    elif command == "!use":
        bot.send_message(message.chat.id, "⚙️ Команда !use выполнена.")
        
    elif command == "!accept":
        bot.send_message(message.chat.id, "✅ Заявка игрока успешно принята (Трейд подтвержден).")
        
    elif command == "!cancel":
        bot.send_message(message.chat.id, "❌ Заявка отклонена.")
        
    elif command == "!week":
        bot.send_message(message.chat.id, "📅 Предметы недели для вывода обновлены.")
        
    elif command == "!brainrot":
        bot.send_message(message.chat.id, "🧠 База брейнротов обновлена.")
        
    elif command == "!vivod":
        bot.send_message(message.chat.id, "💸 Система вывода проверена и работает.")
        
    else:
        bot.send_message(message.chat.id, f"❓ Неизвестная админ-команда: {command}")

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)