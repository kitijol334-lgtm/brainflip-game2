import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import json

# ==========================================
# КОНФИГУРАЦИЯ БОТА
# ==========================================
TOKEN = '8876455639:AAHQPFddKapRcF2TBjM5UpDsEM45QpbQcRg'
bot = telebot.TeleBot(TOKEN)

# ВАЖНО: Вставьте сюда ссылку на ваш сайт!
WEBAPP_URL = "https://ВАШ-САЙТ.netlify.app"

# ==========================================
# ОСНОВНАЯ КОМАНДА ЗАПУСКА
# ==========================================
@bot.message_handler(commands=['start'])
def start_command(message):
    text = (
        "👋 <b>Привет! Добро пожаловать в BrainFlip Ultra Premium V2!</b> 🧠\n\n"
        "👇 <b>Нажми на кнопку «🚀 Играть» внизу экрана.</b>\n\n"
        f"<i>Твой Telegram ID:</i> <code>{message.chat.id}</code> (сообщи его админу при заявке)"
    )
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_play = KeyboardButton("🚀 Играть", web_app=WebAppInfo(url=WEBAPP_URL))
    markup.add(btn_play)
    
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ==========================================
# ОБРАБОТКА ДАННЫХ ИЗ ИГРЫ (СВЯЗЬ С HTML)
# ==========================================
@bot.message_handler(content_types=['web_app_data'])
def web_app_data(message):
    try:
        # Получаем данные из HTML скрипта
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        
        # 1. Заявка на пополнение от игрока
        if action == 'deposit':
            text = (
                f"📥 <b>Заявка на пополнение [{data['req_id']}]</b>\n\n"
                f"👤 Ник: <code>{data['nick']}</code>\n"
                f"📦 Предмет: <b>{data['item']}</b>\n"
                f"🆔 Ваш TG ID: <code>{data['tg_id']}</code>\n\n"
                f"<i>Ожидайте, администратор проверит заявку.</i>"
            )
            bot.send_message(message.chat.id, text, parse_mode="HTML")

        # 2. Заявка на вывод от игрока
        elif action == 'withdraw':
            items_str = ", ".join(data.get('items', []))
            text = (
                f"📤 <b>Заявка на вывод [{data['req_id']}]</b>\n\n"
                f"👤 Ник: <code>{data['nick']}</code>\n"
                f"📦 Предметы: <b>{items_str}</b>\n"
                f"🆔 Ваш TG ID: <code>{data['tg_id']}</code>\n\n"
                f"<i>Ожидайте, администратор свяжется с вами.</i>"
            )
            bot.send_message(message.chat.id, text, parse_mode="HTML")

        # 3. Админ принял заявку
        elif action == 'admin_accept':
            target_id = data.get('target_tg_id')
            req_id = data.get('req_id')
            
            user_msg = f"✅ <b>Заявка {req_id} ОДОБРЕНА!</b>\n\nУ вас есть <b>3 минуты</b>, чтобы зайти в игру!"
            
            try:
                # Отправляем сообщение игроку
                bot.send_message(target_id, user_msg, parse_mode="HTML")
                # Подтверждаем админу
                bot.send_message(message.chat.id, f"✅ Уведомление об одобрении отправлено пользователю {target_id}.", parse_mode="HTML")
            except Exception:
                bot.send_message(message.chat.id, "❌ Ошибка: неверный TG ID или бот заблокирован пользователем.")

        # 4. Админ отклонил заявку
        elif action == 'admin_reject':
            target_id = data.get('target_tg_id')
            req_id = data.get('req_id')
            
            user_msg = f"❌ <b>Внимание по заявке {req_id}!</b>\n\nПроизошла ошибка, вывод/пополнение не прошёл. Если это был вывод, предметы возвращены в инвентарь."
            
            try:
                # Отправляем сообщение игроку
                bot.send_message(target_id, user_msg, parse_mode="HTML")
                # Подтверждаем админу
                bot.send_message(message.chat.id, f"✅ Уведомление об отказе отправлено пользователю {target_id}.", parse_mode="HTML")
            except Exception:
                bot.send_message(message.chat.id, "❌ Ошибка отправки сообщения пользователю.")

        # 5. Обновление брейнрота недели
        elif action == 'admin_update_weekly':
            items = data.get('items', [])
            items_text = ", ".join(items) if items else "Пусто"
            bot.send_message(message.chat.id, f"⚙️ <b>База Брейнротов обновлена!</b>\nРазрешены для вывода: {items_text}", parse_mode="HTML")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Произошла системная ошибка: <code>{e}</code>", parse_mode="HTML")

if __name__ == '__main__':
    print("Бот успешно запущен и работает! Теперь все функции вынесены в саму игру.")
    bot.polling(none_stop=True)