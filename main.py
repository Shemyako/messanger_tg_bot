import telebot
from auth_module import Auth_module
from db_connection import Connection

'''
Обновлять чат у второго собеседника
'''

# session = Session(engine)

# # rudimentary relationships are produced
# session.add(User(name="foo@bar.com", password="Ola", tg_id="None"))
# session.commit()
# print(User)

conf = []
with open("conf.txt", "r") as f:
    conf = f.read().split("|")
# print(conf)
assert len(conf) == 2

connection = Connection(conf[1])
auth_module = Auth_module(connection)

# user_data = auth_module.check_user("957897bdf80742a4a8fe4bb307c3d4c8", "123123", 123123)
# print(User)
# print(Message)
# print(engine)




bot = telebot.TeleBot(conf[0])
authed = set()
pre_authed = set()
pre_login = set()
chats = {}


@bot.message_handler(commands=["start"])
def start_handler(message):
    if message.from_user.id in pre_authed:
        pre_authed.remove(message.from_user.id)
    if message.from_user.id in pre_login:
        pre_login.remove(message.from_user.id)

    # Создаём клавиатуру
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    if message.from_user.id not in authed: 
        keyboard.add("🖐Войти🖐")
        keyboard.add("🤝Зарегистрироваться🤝")
    else:
        keyboard.add("🚪Выйти🚪")

    bot.send_message(message.from_user.id, "Авторизация", reply_markup = keyboard)


@bot.message_handler(func=lambda message: message.from_user.id not in authed and message.text == "🖐Войти🖐", 
                        content_types = ['text'])
def login_handler(message):
    pre_login.add(message.from_user.id)
    bot.send_message(message.from_user.id, "Введите через пробел логин и пароль")


@bot.message_handler(func=lambda message: message.from_user.id not in authed and message.text == "🤝Зарегистрироваться🤝", 
                        content_types = ['text'])
def signup_handler(message):
    bot.send_message(message.from_user.id, "Введите пароль для создаваемой записи")
    pre_authed.add(message.from_user.id)
    

@bot.message_handler(func=lambda message: message.from_user.id in authed and message.text == "🚪Выйти🚪", 
                        content_types = ['text'])
def logout_handler(message):
    authed.remove(message.from_user.id)
    start_handler(message)
    data_to_delete_message = connection.logout_user(message.from_user.id)
    bot.delete_message(data_to_delete_message[0], data_to_delete_message[1]) 


@bot.message_handler(func=lambda message: message.from_user.id in authed)
def message_sended(message):
    ###
    # До 50 символов
    ###
    data_to_delete_message = connection.send_message(
        message.from_user.id,           # From
        chats[message.from_user.id],    # To
        message.text                    # Text
    )

    keyboard = form_chats(data_to_delete_message[0], chats[message.from_user.id])
    
    bot.delete_message(message.from_user.id, data_to_delete_message[1]) 
    msg = bot.send_message(message.from_user.id, "Чат с " + str(chats[message.from_user.id]), reply_markup = keyboard)
    connection.message_sended(data_to_delete_message[0], msg.id)


@bot.message_handler(func=lambda message: message.from_user.id in pre_authed)
def sign_in(message):
    ###
    # Проверка пароля
    ###
    user_data = auth_module.create_user(message.text, message.from_user.id)
    bot.send_message(message.from_user.id, "`" + user_data[0] + "` <- Логин", parse_mode = "Markdown") 
    pre_authed.remove(message.from_user.id)


@bot.message_handler(func=lambda message: message.from_user.id in pre_login)
def login(message):
    ###
    # Проверка введённого
    ###
    user_data = message.text.split()
    login = message.text.split()[0]
    user_data = auth_module.check_user(user_data[0], user_data[1])

    pre_login.remove(message.from_user.id)
    
    if (user_data == False):
        bot.send_message(message.from_user.id, "Неуспешно") 
        return

    data_to_delete_message = connection.logout_user(login = login)
    if data_to_delete_message.count(None) == 0:
        bot.delete_message(data_to_delete_message[0], data_to_delete_message[1]) 
    
    if data_to_delete_message[0] in authed:
        authed.remove(data_to_delete_message[0])

    connection.login_user(user_data, message.from_user.id)

    keyboard = form_keyboard(data_to_delete_message[2], message.from_user.id)

    mes = bot.send_message(
        message.from_user.id, 
        "Всё тип-топ, id -> " + str(data_to_delete_message[2]), 
        reply_markup = keyboard
    )

    connection.message_sended(data_to_delete_message[2], mes.id)

    authed.add(message.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data[:5] == "chat~" and call.from_user.id in authed)
def chat_selected_handler(call):
    data = call.data.split("~")
    # print(type(ten_messages))

    keyboard = form_chats(data[1], data[2])

    chats[call.from_user.id] = data[2]
    bot.edit_message_text(
        chat_id = call.message.chat.id, 
        message_id = call.message.message_id,
        text='Чат с ' + data[2],
        reply_markup = keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data[:4] == "menu" and call.from_user.id in authed)
def menu_handler(call):
    if call.from_user.id in chats:
        del chats[call.from_user.id]
    keyboard = form_keyboard(call.data[4:], call.from_user.id)

    bot.edit_message_text(
        chat_id = call.message.chat.id,
        message_id = call.message.message_id,
        text="Всё тип-топ, id -> " + call.data[4:],
        reply_markup = keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data[:4] == "exit" and call.from_user.id in authed)
def exit_handler(call):
    if call.from_user.id in chats:
        del chats[call.from_user.id]
    logout_handler(call)


@bot.callback_query_handler(func=lambda call: call.data[:6] == "delete" and call.from_user.id in authed)
def exit_handler(call):
    if call.from_user.id in chats:
        del chats[call.from_user.id]
    pass


@bot.callback_query_handler(func=lambda call: call.data[:8] == "new_chat" and call.from_user.id in authed)
def new_chat_handler(call):
    # print(call)
    pass


@bot.callback_query_handler(func=lambda call: call.from_user.id in authed)
def callback_text_handler(call):
    bot.answer_callback_query(callback_query_id=call.id, text=call.data, show_alert=True)


def form_keyboard(id, tg_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("Новый чат", callback_data="new_chat" + str(id)))

    ### Chats
    chats = connection.get_ten_chats(id)
    formed = set()
    for chat in chats:
        if chat.to_user == id:
            if chat.from_user in formed:
                continue
            formed.add(chat.from_user)
            keyboard.add(telebot.types.InlineKeyboardButton(chat.from_user, callback_data="chat~" + str(id) + "~" + str(chat.from_user)))
        else:
            if chat.to_user in formed:
                continue
            formed.add(chat.to_user)
            keyboard.add(telebot.types.InlineKeyboardButton(chat.to_user, callback_data="chat~" + str(id) + "~" + str(chat.to_user)))
    del formed
    ###
    
    keyboard.add(
        telebot.types.InlineKeyboardButton("Выйти", callback_data="exit" + str(id)),
        telebot.types.InlineKeyboardButton("Удалить всё", callback_data="delete" + str(id))
    )

    return keyboard


def form_chats(id_from, id_to):
    ten_messages = connection.get_chat(id_from, id_to)
    ten_messages.reverse()
    keyboard = telebot.types.InlineKeyboardMarkup()
    for message in ten_messages:
        keyboard.add(telebot.types.InlineKeyboardButton(str(message.from_user) + ": " + message.text, callback_data=message.text))
    
    keyboard.add(telebot.types.InlineKeyboardButton("Выйти", callback_data="menu" + str(id_from)))
    return keyboard


bot.polling()