import telebot
from auth_module import Auth_module
from db_connection import Connection

'''
Подумать над подключением к auth модуля db
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


@bot.message_handler(commands=["start"])
def start_handler(message):
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
    user_data = message.text.split()
    user_data = auth_module.check_user(user_data[0], user_data[1], message.from_user.id)

    pre_login.remove(message.from_user.id)
    
    if (not user_data):
        bot.send_message(message.from_user.id, "Неуспешно") 
        return

    
    keyboard = telebot.types.InlineKeyboardMarkup()
    ###
    # Все чаты по 10
    ###
    keyboard.add(telebot.types.InlineKeyboardButton("Выйти", callback_data="exit"))
    keyboard.add(telebot.types.InlineKeyboardButton("Удалить всё", callback_data="delete"))


@bot.callback_query_handler(func=lambda call: call.data[:4] == "chat-")
def chat_selected_handler(call):
    pass


@bot.callback_query_handler(func=lambda call: call.data[:3] == "menu")
def menu_handler(call):
    pass


@bot.callback_query_handler(func=lambda call: call.data[:3] == "exit")
def exit_handler(call):
    logout_handler(call)


@bot.callback_query_handler(func=lambda call: call.data[:5] == "delete")
def exit_handler(call):
    pass


bot.polling()