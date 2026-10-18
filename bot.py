import telebot
import json

TOKEN = '8876455639:AAExE0fIIY99UXIC2bg42WNUd9-plPtbpfk'
bot = telebot.TeleBot(TOKEN)

# Словари для хранения данных (в оперативной памяти)
admins = set()
pending_deposits = {}    # { 'RobloxNick': {'user_id': id, 'item': item} }
pending_withdrawals = {} # { 'RobloxNick': {'user_id': id, 'items': [item1, item2]} }
promo_codes = {}         # { 'code': {'activations': 5, 'coins': 50} }

# Контекст: с кем сейчас работает админ (!use или !vivod)
admin_context = {}       # { admin_id: {'type': 'deposit'/'withdraw', 'nick': nick} }

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Играй в BrainFlip по кнопке ниже:", 
                     reply_markup=telebot.types.ReplyKeyboardRemove())
    # Здесь позже вы добавите кнопку Mini App через BotFather

@bot.message_handler(func=lambda message: message.text == 'Самир123')
def admin_login(message):
    admins.add(message.chat.id)
    bot.send_message(message.chat.id, "✅ Доступ администратора получен!\nКоманды:\n!check\n!use <ник>\n!cancel\n!accept\n!week <item1> <item2>\n!brainrot\n!vivod <ник>\n!code <код> <акт.> <монеты>")

# Обработка данных из Mini App (когда в HTML вызывается tg.sendData)
@bot.message_handler(content_types=['web_app_data'])
def web_app_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        
        if action == 'deposit':
            nick = data['nick']
            pending_deposits[nick] = {'user_id': message.chat.id, 'item': data['item']}
            bot.send_message(message.chat.id, "✅ Ваш запрос на пополнение отправлен администратору.")
            # Уведомляем админов
            for admin in admins:
                bot.send_message(admin, f"Новое пополнение!\nНик: {nick}\nБрейнрот: {data['item']}")
                
        elif action == 'withdraw':
            nick = data['nick']
            pending_withdrawals[nick] = {'user_id': message.chat.id, 'items': data['items']}
            bot.send_message(message.chat.id, "✅ Ваш запрос на вывод отправлен.")
            for admin in admins:
                bot.send_message(admin, f"Новый вывод!\nНик: {nick}\nПредметы: {', '.join(data['items'])}")
                
        elif action == 'promo':
            # Логика промокодов (клиентская часть тоже имеет хардкод для теста, но можно проверять тут)
            code = data['code']
            if code in promo_codes and promo_codes[code]['activations'] > 0:
                promo_codes[code]['activations'] -= 1
                coins = promo_codes[code]['coins']
                bot.send_message(message.chat.id, f"🎉 Промокод активирован!\nВведите в игре промокод: DEV-{coins}\nчтобы забрать монеты на баланс.")
            else:
                bot.send_message(message.chat.id, "❌ Неверный или закончившийся промокод.")
    except Exception as e:
        print(e)

# --- АДМИН КОМАНДЫ ДЛЯ ПОПОЛНЕНИЯ ---
@bot.message_handler(func=lambda msg: msg.text.startswith('!check') and msg.chat.id in admins)
def cmd_check(message):
    if not pending_deposits:
        bot.send_message(message.chat.id, "Нет активных запросов на пополнение.")
        return
    text = "🔥 Пополнения:\n"
    for nick, info in pending_deposits.items():
        text += f"Ник: {nick} | Предмет: {info['item']}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda msg: msg.text.startswith('!use ') and msg.chat.id in admins)
def cmd_use(message):
    nick = message.text.split(' ', 1)[1]
    if nick in pending_deposits:
        user_id = pending_deposits[nick]['user_id']
        admin_context[message.chat.id] = {'type': 'deposit', 'nick': nick}
        bot.send_message(user_id, "⚠️ Будьте онлайн в Roblox в течении 3 минут и ждите трейд от человека с ником: Noobtodjtvman4 или orcalerrcala7.")
        bot.send_message(message.chat.id, f"Пользователь {nick} уведомлен.")
    else:
        bot.send_message(message.chat.id, "Ник не найден.")

# --- АДМИН КОМАНДЫ ДЛЯ ВЫВОДА ---
@bot.message_handler(func=lambda msg: msg.text.startswith('!brainrot') and msg.chat.id in admins)
def cmd_brainrot(message):
    if not pending_withdrawals:
        bot.send_message(message.chat.id, "Нет активных запросов на вывод.")
        return
    text = "💸 Выводы:\n"
    for nick, info in pending_withdrawals.items():
        text += f"Ник: {nick} | Предметы: {', '.join(info['items'])}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda msg: msg.text.startswith('!vivod ') and msg.chat.id in admins)
def cmd_vivod(message):
    nick = message.text.split(' ', 1)[1]
    if nick in pending_withdrawals:
        user_id = pending_withdrawals[nick]['user_id']
        admin_context[message.chat.id] = {'type': 'withdraw', 'nick': nick}
        bot.send_message(user_id, "⚠️ Будьте онлайн в Roblox в течении 3 минут чтобы забрать свой брейнрот (от Noobtodjtvman4 / orcalerrcala7).")
        bot.send_message(message.chat.id, f"Пользователь {nick} уведомлен о выводе.")
    else:
        bot.send_message(message.chat.id, "Ник не найден.")

# --- ОБЩИЕ АДМИН КОМАНДЫ (ACCEPT / CANCEL) ---
@bot.message_handler(func=lambda msg: msg.text == '!cancel' and msg.chat.id in admins)
def cmd_cancel(message):
    context = admin_context.get(message.chat.id)
    if not context:
        bot.send_message(message.chat.id, "Нет активного диалога (!use или !vivod).")
        return
    
    nick = context['nick']
    if context['type'] == 'deposit':
        user_id = pending_deposits[nick]['user_id']
        bot.send_message(user_id, "❌ Отмена: Вы не были онлайн в нужное время или не дали то, что указали.")
        del pending_deposits[nick]
    else:
        user_id = pending_withdrawals[nick]['user_id']
        bot.send_message(user_id, "❌ Отмена: Вы не были онлайн в нужное время.")
        del pending_withdrawals[nick]
        
    del admin_context[message.chat.id]
    bot.send_message(message.chat.id, "Отмена завершена.")

@bot.message_handler(func=lambda msg: msg.text == '!accept' and msg.chat.id in admins)
def cmd_accept(message):
    context = admin_context.get(message.chat.id)
    if not context:
        bot.send_message(message.chat.id, "Нет активного диалога.")
        return
    
    nick = context['nick']
    if context['type'] == 'deposit':
        user_id = pending_deposits[nick]['user_id']
        # Выдаем персональный чит-код для HTML
        bot.send_message(user_id, "✅ Брейнрот успешно принят!\nВведите этот код во вкладке ПРОМОКОД в игре, чтобы получить свои монеты:\nDEV-500")
        del pending_deposits[nick]
        bot.send_message(message.chat.id, "Пополнение подтверждено (выдан код на 500 монет).")
    else:
        user_id = pending_withdrawals[nick]['user_id']
        bot.send_message(user_id, "✅ Вывод успешно завершен!")
        del pending_withdrawals[nick]
        bot.send_message(message.chat.id, "Вывод подтвержден.")
        
    del admin_context[message.chat.id]

# --- НАСТРОЙКИ (КОДЫ И НЕДЕЛЯ) ---
@bot.message_handler(func=lambda msg: msg.text.startswith('!code ') and msg.chat.id in admins)
def cmd_code(message):
    try:
        parts = message.text.split(' ')
        code = parts[1]
        activations = int(parts[2])
        coins = int(parts[3])
        promo_codes[code] = {'activations': activations, 'coins': coins}
        bot.send_message(message.chat.id, f"✅ Код {code} создан ({activations} акт. по {coins} монет).")
    except:
        bot.send_message(message.chat.id, "Ошибка. Формат: !code <промокод> <активации> <монеты>")

@bot.message_handler(func=lambda msg: msg.text.startswith('!week ') and msg.chat.id in admins)
def cmd_week(message):
    items = message.text.split(' ')[1:]
    bot.send_message(message.chat.id, f"Список недели обновлен (Вам также нужно вписать эти ID в самом файле index.html в массив WEEKLY_ITEMS для безопасности): {', '.join(items)}")

bot.polling(none_stop=True)