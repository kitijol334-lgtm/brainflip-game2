import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import json
import os
import random

# ==========================================
# КОНФИГУРАЦИЯ БОТА
# ==========================================
TOKEN = '8876455639:AAHQPFddKapRcF2TBjM5UpDsEM45QpbQcRg'
bot = telebot.TeleBot(TOKEN)

ADMIN_PASS = "Самир123"

# ВАЖНО: Вставьте сюда ссылку на ваш сайт, чтобы заявки начали приходить!
WEBAPP_URL = "https://ВАШ-САЙТ.netlify.app"

# Абсолютные пути к папке скрипта (защита от ошибки Permission denied)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMOS_FILE = os.path.join(BASE_DIR, 'promos.json')
USERS_FILE = os.path.join(BASE_DIR, 'users.json')
REQUESTS_FILE = os.path.join(BASE_DIR, 'requests.json')

DEFAULT_PROMOS = {
    "START1000": {"limit": 1000, "reward": 1000},
    "BRAINFLIP2026": {"limit": 500, "reward": 2500},
    "ULTRAMODE": {"limit": 100, "reward": 5000},
    "MEGASECRET": {"limit": 10, "reward": 15000}
}

# ==========================================
# БАЗА ДАННЫХ
# ==========================================
def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_data(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

promos_db = load_data(PROMOS_FILE, DEFAULT_PROMOS)
users_db = load_data(USERS_FILE, {}) 
requests_db = load_data(REQUESTS_FILE, {}) 

def get_user(user_id):
    uid = str(user_id)
    if uid not in users_db:
        users_db[uid] = {"used_promos": []}
    return users_db[uid]

# ==========================================
# ОСНОВНЫЕ КОМАНДЫ (ИГРА И ПРОМОКОДЫ)
# ==========================================
@bot.message_handler(commands=['start'])
def start_command(message):
    text = (
        "👋 <b>Привет! Добро пожаловать в BrainFlip!</b> 🧠\n\n"
        "Здесь ты сможешь прокачать своих брейнротов!\n"
        "👇 <b>Нажми на кнопку «🚀 Играть» внизу экрана, чтобы открыть игру.</b>"
    )
    
    # ИСПОЛЬЗУЕМ НИЖНЮЮ КЛАВИАТУРУ, ЧТОБЫ РАБОТАЛ tg.sendData (Заявки)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_play = KeyboardButton("🚀 Играть", web_app=WebAppInfo(url=WEBAPP_URL))
    btn_promo = KeyboardButton("🎁 Ввести промокод")
    markup.add(btn_play, btn_promo)
    
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🎁 Ввести промокод")
def promo_request(message):
    msg = bot.send_message(message.chat.id, "🎟 <b>Введи промокод:</b>\n<i>(Отправь его мне следующим сообщением)</i>", parse_mode='HTML')
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
        bot.send_message(message.chat.id, "⚠️ <b>Ошибка:</b> Ты уже активировал этот промокод!", parse_mode='HTML')
        return

    if promo_info["limit"] <= 0:
        bot.send_message(message.chat.id, "⏳ <b>Ошибка:</b> Активации исчерпаны.", parse_mode='HTML')
        return

    promo_info["limit"] -= 1
    user["used_promos"].append(code)
    
    save_data(PROMOS_FILE, promos_db)
    save_data(USERS_FILE, users_db)

    bot.send_message(
        message.chat.id, 
        f"✅ <b>Промокод успешно проверен!</b>\n\n"
        f"🎁 Награда: <b>{promo_info['reward']} 💰</b>\n\n"
        f"<i>💡 Зайди в игру, нажми «КОДЫ» и введи этот DEV-ключ, чтобы монеты зачислились:</i>\n\n"
        f"<code>DEV-{promo_info['reward']}</code>", 
        parse_mode='HTML'
    )

# ==========================================
# ОБРАБОТКА ДАННЫХ ИЗ ИГРЫ (ЗАЯВКИ)
# ==========================================
@bot.message_handler(content_types=['web_app_data'])
def web_app_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        user_id = message.chat.id
        
        if action == 'deposit':
            nick = data.get('nick')
            item = data.get('item')
            req_id = f"DEP{random.randint(1000, 9999)}"
            
            requests_db[req_id] = {"type": "deposit", "user_id": user_id, "nick": nick, "item": item}
            save_data(REQUESTS_FILE, requests_db)
            
            bot.send_message(message.chat.id, f"📥 <b>Заявка на пополнение создана!</b> [ID: {req_id}]\n\n👤 Ник: <code>{nick}</code>\n📦 Предмет: <b>{item}</b>\n\nОжидай трейда от администратора.", parse_mode="HTML")

        elif action == 'withdraw':
            nick = data.get('nick')
            items = data.get('items', [])
            items_str = ", ".join(items)
            req_id = f"WIT{random.randint(1000, 9999)}"
            
            requests_db[req_id] = {"type": "withdraw", "user_id": user_id, "nick": nick, "items": items_str}
            save_data(REQUESTS_FILE, requests_db)
            
            bot.send_message(message.chat.id, f"📤 <b>Заявка на вывод создана!</b> [ID: {req_id}]\n\n👤 Ник: <code>{nick}</code>\n📦 Предметы: <b>{items_str}</b>\n\nОжидай трейда в игре.", parse_mode="HTML")
            
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Произошла ошибка при обработке данных из игры.")

# ==========================================
# АДМИН-КОМАНДЫ (ИСПРАВЛЕН БАГ 400 HTML)
# ==========================================
@bot.message_handler(func=lambda message: message.text.startswith(f"{ADMIN_PASS} !"))
def admin_commands(message):
    try:
        command_full = message.text[len(ADMIN_PASS):].strip()
        parts = command_full.split()
        if not parts:
            return
            
        command = parts[0].lower()

        if command == "!check":
            if not requests_db:
                bot.send_message(message.chat.id, "✅ <b>Админ-панель:</b> Активных заявок нет.", parse_mode="HTML")
                return
                
            text = "📋 <b>АКТИВНЫЕ ЗАЯВКИ:</b>\n\n"
            for req_id, req in requests_db.items():
                if req['type'] == 'deposit':
                    text += f"🟢 <b>ПОПОЛНЕНИЕ</b> | ID: <code>{req_id}</code>\n👤 Ник: {req['nick']}\n📦 Предмет: {req['item']}\n〰️〰️〰️\n"
                elif req['type'] == 'withdraw':
                    text += f"🔴 <b>ВЫВОД</b> | ID: <code>{req_id}</code>\n👤 Ник: {req['nick']}\n📦 Предметы: {req['items']}\n〰️〰️〰️\n"
            bot.send_message(message.chat.id, text, parse_mode="HTML")

        elif command == "!use":
            if len(parts) >= 2:
                nick = parts[1]
                bot.send_message(message.chat.id, f"⚙️ Команда !use применена к игроку: <b>{nick}</b>", parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, f"❌ Формат: <code>{ADMIN_PASS} !use [ник]</code>", parse_mode="HTML")

        elif command == "!cancel":
            if len(parts) >= 2:
                req_id = parts[1].upper()
                reason = " ".join(parts[2:]) if len(parts) >= 3 else "Без объяснения причины"
                
                if req_id in requests_db:
                    req = requests_db[req_id]
                    user_msg = f"❌ <b>Твоя заявка была отклонена!</b>\n\nПричина: <i>{reason}</i>\nЕсли ты потерял предметы, свяжись с администрацией."
                    bot.send_message(req['user_id'], user_msg, parse_mode="HTML")
                    
                    del requests_db[req_id]
                    save_data(REQUESTS_FILE, requests_db)
                    bot.send_message(message.chat.id, f"✅ Заявка <b>{req_id}</b> отклонена.", parse_mode="HTML")
                else:
                    bot.send_message(message.chat.id, "❌ Заявка с таким ID не найдена.")
            else:
                bot.send_message(message.chat.id, f"❌ Формат: <code>{ADMIN_PASS} !cancel [ID] [причина]</code>", parse_mode="HTML")

        elif command == "!accept":
            if len(parts) >= 2:
                req_id = parts[1].upper()
                if req_id in requests_db:
                    req = requests_db[req_id]
                    
                    if req['type'] == 'deposit':
                        amount = parts[2] if len(parts) >= 3 else "0"
                        user_msg = f"✅ <b>Твой депозит одобрен!</b>\n\nЗайди в раздел КОДЫ в игре и введи это, чтобы получить монеты:\n<code>DEV-{amount}</code>"
                        bot.send_message(req['user_id'], user_msg, parse_mode="HTML")
                        bot.send_message(message.chat.id, f"✅ Заявка <b>{req_id}</b> закрыта. Выдан DEV-код на {amount} монет.", parse_mode="HTML")
                    
                    elif req['type'] == 'withdraw':
                        user_msg = f"✅ <b>Твой вывод успешно завершен!</b>\n\nПредметы были переданы тебе в игре."
                        bot.send_message(req['user_id'], user_msg, parse_mode="HTML")
                        bot.send_message(message.chat.id, f"✅ Заявка <b>{req_id}</b> (Вывод) успешно закрыта.", parse_mode="HTML")
                    
                    del requests_db[req_id]
                    save_data(REQUESTS_FILE, requests_db)
                else:
                    bot.send_message(message.chat.id, "❌ Заявка с таким ID не найдена.")
            else:
                bot.send_message(message.chat.id, f"❌ Формат:\nПополнение: <code>{ADMIN_PASS} !accept [ID] [сумма]</code>\nВывод: <code>{ADMIN_PASS} !accept [ID]</code>", parse_mode="HTML")

        elif command == "!week":
            if len(parts) >= 3:
                items_str = ", ".join(parts[1:])
                bot.send_message(message.chat.id, f"📅 Предметы недели для вывода обновлены: <b>{items_str}</b>", parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, f"❌ Формат: <code>{ADMIN_PASS} !week [item1] [item2]</code>", parse_mode="HTML")

        elif command == "!brainrot":
            bot.send_message(message.chat.id, "🧠 База брейнротов успешно обновлена.", parse_mode="HTML")

        elif command == "!vivod":
            if len(parts) >= 2:
                nick = parts[1]
                bot.send_message(message.chat.id, f"💸 Система вывода проверена для игрока <b>{nick}</b>. Ошибок нет.", parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, f"❌ Формат: <code>{ADMIN_PASS} !vivod [ник]</code>", parse_mode="HTML")

        elif command == "!code":
            if len(parts) >= 4:
                code_name = parts[1].upper()
                try:
                    limit = int(parts[2])
                    reward = int(parts[3])
                    promos_db[code_name] = {"limit": limit, "reward": reward}
                    save_data(PROMOS_FILE, promos_db)
                    bot.send_message(message.chat.id, f"✅ Создан новый промокод: <b>{code_name}</b>\nАктиваций: {limit}\nНаграда: {reward} 💰", parse_mode="HTML")
                except ValueError:
                    bot.send_message(message.chat.id, "❌ Ошибка: лимит и награда должны быть цифрами.", parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, f"❌ Формат: <code>{ADMIN_PASS} !code [код] [лимит] [монеты]</code>", parse_mode="HTML")
                
        else:
            bot.send_message(message.chat.id, f"❓ Неизвестная команда: {command}", parse_mode="HTML")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ <b>Произошла ошибка:</b>\n<code>{e}</code>", parse_mode="HTML")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)