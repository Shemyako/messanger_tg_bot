import telebot
from auth_module import Auth_module
from db_connection import Connection



### TODO
# Чистка чатов в отдельном потоке
# Время авторизации, выход пользователей по нему в потоке выше
# Чистка чата при выходе Ассинхронно
# До запуска смотреть users.tg_id и парсить их в authed 
###


# Open config file to check data (tg token, db data)
conf = []
with open("conf.txt", "r") as f:
    conf = f.read().split("|")
# print(conf)
assert len(conf) == 2

# Create objects to work with DB
connection = Connection(conf[1])
auth_module = Auth_module(connection)

# Create object of bot to work with tg
bot = telebot.TeleBot(conf[0])
# Users who succesfully authed
authed = set()
# Users who trying to sing up
pre_authed = set()
# Users who trying to sing in
pre_login = set()
# Dict [body] = conv_to
chats = {}


@bot.message_handler(commands=["start"])
def start_handler(message):
    """
    Function to answer on /start
    If user authed, we allow him to logout
    Other way we allowed him to sign in/up
    """
    ###
    # Сделать async удаление истории
    ###
    # try:
    #     id = message.id
    #     while True:
    #         id -= 1
    #         print(id)
    #         try:
    #             bot.delete_message(message.from_user.id, id)
    #         except telebot.apihelper.ApiTelegramException:
    #             print( "ola")
    # except Exception:
    #     print("Bola")

    # Cleaning sets if user 
    if message.from_user.id in pre_authed:
        pre_authed.remove(message.from_user.id)
    if message.from_user.id in pre_login:
        pre_login.remove(message.from_user.id)

    # Creating keyboard
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    # If user haven't authed
    if message.from_user.id not in authed: 
        keyboard.add("🖐Войти🖐")
        keyboard.add("🤝Зарегистрироваться🤝")
    else: # Other way
        keyboard.add("🚪Выйти🚪")

    # Send keyboard to user
    bot.send_message(message.from_user.id, "Авторизация", reply_markup = keyboard)


@bot.message_handler(func=lambda message: message.from_user.id not in authed and message.text == "🖐Войти🖐", 
                        content_types = ['text'])
def login_handler(message):
    '''
    This function reacts on user's typing on 🖐Войти🖐 bttn if user hasn't authed
    '''
    # Put user's tg_id in pre_login set
    # It means that he'll send login and password
    pre_login.add(message.from_user.id)

    # Send request to send login and password
    bot.send_message(message.from_user.id, "Введите через пробел логин и пароль")


@bot.message_handler(func=lambda message: message.from_user.id not in authed and message.text == "🤝Зарегистрироваться🤝", 
                        content_types = ['text'])
def signup_handler(message):
    '''
    This function reacts on user's will to sing up
    User must tap on 🤝Зарегистрироваться🤝 bttn to activate this function
    User must not be authed
    '''
    # Send request for password for user
    bot.send_message(message.from_user.id, "Введите пароль для создаваемой записи")
    # Add user in pre_authed set
    pre_authed.add(message.from_user.id)
    

@bot.message_handler(func=lambda message: message.from_user.id in authed and message.text == "🚪Выйти🚪", 
                        content_types = ['text'])
def logout_handler(message):
    """
    This function reacts on user's will to logout
    User must tap on 🚪Выйти🚪 bttn to activate this function
    User must be authed
    """
    # Remove user from all sets
    authed.remove(message.from_user.id)
    if message.from_user.id in chats:
        del chats[message.from_user.id]

    # Delete message with buttons
    data_to_delete_message = connection.logout_user(message.from_user.id)
    bot.delete_message(data_to_delete_message[0], data_to_delete_message[1]) 

    # Start start function
    start_handler(message)


#!
@bot.message_handler(func=lambda message: message.from_user.id in authed and message.from_user.id in chats)
def message_sended(message):
    """
    This function reacts on sending message to buddy from opend chat
    """
    ###!!!!!
    # До 50 символов
    ###!!!!!

    # sending message to buddy in DB
    data_to_delete_message = connection.send_message(
        message.from_user.id,           # From
        chats[message.from_user.id],    # To
        message.text                    # Text
    )

    # Form new keyboard (in that will be new message)
    keyboard = form_chats(data_to_delete_message[0], chats[message.from_user.id])
    
    # Delete old message, so we can send new
    bot.delete_message(message.from_user.id, data_to_delete_message[1]) 
    # Send new message with chat
    msg = bot.send_message(message.from_user.id, "Чат с " + str(chats[message.from_user.id]), reply_markup = keyboard)
    # Update DB about message_id, so we can update/delete it
    connection.message_sended(data_to_delete_message[0], msg.id)

    # Get buddy id
    buddy = connection.find_user_by_id(chats[message.from_user.id])
    # Check, is he in chat with user
    if buddy[0] in chats and chats[buddy[0]] == data_to_delete_message[0]:
        # Form keyboard to send
        keyboard = form_chats(chats[message.from_user.id], data_to_delete_message[0])
        # Update last message to buddy
        bot.edit_message_text(
            chat_id = buddy[0], 
            message_id = buddy[1],
            text='Чат с ' + str(data_to_delete_message[0]),
            reply_markup = keyboard
        )
    # If buddy on menu message (with chats list), 
    # update that message (so he'll see that new message sended)
    elif buddy[0] in authed and buddy[0] not in chats:
        keyboard = form_keyboard(chats[message.from_user.id],0)
        bot.edit_message_text(
            chat_id = buddy[0], 
            message_id = buddy[1],
            text = "Всё тип-топ, id -> " + str(chats[message.from_user.id]), 
            reply_markup = keyboard
        )


@bot.message_handler(func=lambda message: message.from_user.id in pre_authed)
def sign_in(message):
    """
    This fucntion reacts on user's will to sign in
    User sends password, login giving forced
    User must tap 🤝Зарегистрироваться🤝 before
    """
    # Create user in DB
    user_data = auth_module.create_user(message.text, message.from_user.id)
    # Send login to user. Password was sended by user
    bot.send_message(message.from_user.id, "`" + user_data[0] + "` <- Логин", parse_mode = "Markdown") 
    # Remove user from pre_authed ser (he already signed in)
    pre_authed.remove(message.from_user.id)


@bot.message_handler(func=lambda message: message.from_user.id in pre_login)
def login(message):
    """
    This function reacts on user's will to login
    User sends <login> <password> with whitespace between
    """
    # Split sended text
    user_data = message.text.split()
    login = message.text.split()[0]
    # Looking for user in DB
    user_data = auth_module.check_user(user_data[0], user_data[1])
    # Remove user from pre_login set (he's tried to login already)
    pre_login.remove(message.from_user.id)
    
    # If user doesn't exist
    if (user_data == False):
        bot.send_message(message.from_user.id, "Неуспешно") 
        return

    # Logout user (so he could't be from two places)
    # and get information about him
    data_to_delete_message = connection.logout_user(login = login)
    # If we need to delete message from prev session, do it
    if data_to_delete_message.count(None) == 0:
        bot.delete_message(data_to_delete_message[0], data_to_delete_message[1]) 
    
    # Delete prev session from authed
    if data_to_delete_message[0] in authed:
        authed.remove(data_to_delete_message[0])

    # Login user in DB
    connection.login_user(user_data, message.from_user.id)
    # Form new keyboard
    keyboard = form_keyboard(data_to_delete_message[2], message.from_user.id)
    # Send message with menu (chat list)
    mes = bot.send_message(
        message.from_user.id, 
        "Всё тип-топ, id -> " + str(data_to_delete_message[2]), 
        reply_markup = keyboard
    )
    # Update DB about sended message
    connection.message_sended(data_to_delete_message[2], mes.id)
    # Add user to authed set
    authed.add(message.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data[:5] == "chat~" and call.from_user.id in authed)
def chat_selected_handler(call):
    """
    This function reacts on user's will to see chat with some user
    User must tap on chat bttn
    """
    # Get information from callback (my_id, buddy_id)
    data = call.data.split("~")

    # Form chat keyboard (to show messages)
    keyboard = form_chats(data[1], data[2])
    # Inform DB that user opend chat (so new messages readed)
    connection.chat_opend(data[1], data[2])
    # Save to dict that user is looking in chat with buddy
    chats[call.from_user.id] = int(data[2])

    # Send chat to user
    bot.edit_message_text(
        chat_id = call.message.chat.id, 
        message_id = call.message.message_id,
        text='Чат с ' + data[2],
        reply_markup = keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data[:4] == "menu" and call.from_user.id in authed)
def menu_handler(call):
    """
    This function reacts on user's will to go to menu from chat
    User must tap on menu bttb from chat
    """
    # If we in chat, delete us
    if call.from_user.id in chats:
        del chats[call.from_user.id]
    
    # Form new menu keyboard (chat list)
    keyboard = form_keyboard(call.data[4:], call.from_user.id)
    # Send it (by updating last message to user)
    bot.edit_message_text(
        chat_id = call.message.chat.id,
        message_id = call.message.message_id,
        text="Всё тип-топ, id -> " + call.data[4:],
        reply_markup = keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data[:4] == "exit" and call.from_user.id in authed)
def exit_handler(call):
    """
    This function reacts on user's will to exit from account
    User must tap on exit bttn from menu (chat list)
    """
    # Logout user
    if call.from_user.id in chats:
        del chats[call.from_user.id]
    logout_handler(call)


#!
@bot.callback_query_handler(func=lambda call: call.data[:6] == "delete" and call.from_user.id in authed)
def delete_handler(call):
    """
    This function reacts on user's will to delete all chats and this account
    User must tap on delete bttn in menu (chat list)
    """
    if call.from_user.id in chats:
        del chats[call.from_user.id]
    pass


@bot.callback_query_handler(func=lambda call: call.data[:8] == "new_chat" and call.from_user.id in authed)
def new_chat_handler(call):
    """
    This function reacts on user's will to create a chat with new user
    User must tap on new_chat bttn from menu (chat list)
    """
    # Send request for buddy loginm so we can create new chat
    mesg = bot.send_message(call.from_user.id, "Введите логин пользователя")
    # Next text from user will handle in defined function
    bot.register_next_step_handler(mesg, new_chat_creating)


def new_chat_creating(message):
    """
    This function reacts of second step of user's will to start new chat
    User send buddy id
    User must complete first step (new_chat_handler function)
    """
    # Try to find buddy by him id
    buddy = connection.find_user_by_id(message.text)
    
    # if we can't find buddy
    if buddy[0] is None:
        bot.send_message(message.from_user.id, "Неверный логин.")
    # Other way
    else:
        # Send new message in DB
        data_to_delete_message = connection.send_message(
            message.from_user.id,
            message.text,
            "Начнём общение!"
        )

        # Update buddy's menu if he authed and not in chat with someone
        if buddy[0] in authed and buddy[0] not in chats:
            keyboard = form_keyboard(message.text,0)
            bot.edit_message_text(
                chat_id = buddy[0], 
                message_id = buddy[1],
                text = "Всё тип-топ, id -> " + str(message.text), 
                reply_markup = keyboard
            )
        # Form new keyboard for user with new chat
        keyboard = form_keyboard(data_to_delete_message[0], 0)
        
        # delete old message for user
        bot.delete_message(message.from_user.id, data_to_delete_message[1])
        # Send new menu with new chat 
        msg = bot.send_message(message.from_user.id, "Всё тип-топ, id -> " + str(data_to_delete_message[0]), reply_markup = keyboard)
        # Save infromation about it in DB
        connection.message_sended(data_to_delete_message[0], msg.id)


@bot.callback_query_handler(func=lambda call: call.from_user.id in authed)
def callback_text_handler(call):
    """
    This function reacts on user's will to see on message text
    User must tap on message bttn from chat
    """
    # Send alert with message text
    bot.answer_callback_query(callback_query_id=call.id, text=call.data, show_alert=True)


def form_keyboard(id:int, tg_id):
    """
    This function forms keyboard to show menu
    Arguments:
    id      -> user id in DB
    tg_id   -> id in Telegram
    
    Returns keyboard:
    <start new chat>
    <chat list>
    <chat list>
    <exit> <delete all>
    """
    id = int(id)
    # Create keyboard
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("Новый чат", callback_data="new_chat" + str(id)))

    # Get chats for user by id
    # chats[0] -> [to_user, from_user, is_readed, id]
    chats = connection.get_ten_chats(id)
    # Create set to keep chats that formed
    formed = set()
    
    # form keyboard
    for chat in chats:

        # Sended to me
        if chat[0] == id:
            
            # If chat is already added
            if chat[1] in formed:
                continue

            # If there is new message in chat
            if chat[2] == False:
                bttn_text = "!" + str(chat[1])
            else:
                bttn_text = chat[1]
            
            # Add chat in formed set
            formed.add(chat[1])
            # Add new bttn in keyboard
            keyboard.add(telebot.types.InlineKeyboardButton(bttn_text, callback_data="chat~" + str(chat[0]) + "~" + str(chat[1])))
        
        # Sended from me
        else:
            
            # If chat is already added
            if chat[0] in formed:
                continue
            
            # Add chat in formed set
            formed.add(chat[0])
            # Add new bttn in keyboard
            keyboard.add(telebot.types.InlineKeyboardButton(chat[0], callback_data="chat~" + str(id) + "~" + str(chat[0])))
    
    # Delete formed set
    del formed
    
    # Add exit and delete bttns
    keyboard.add(
        telebot.types.InlineKeyboardButton("Выйти", callback_data="exit" + str(id)),
        telebot.types.InlineKeyboardButton("Удалить всё", callback_data="delete" + str(id))
    )

    # Return formed keyboard
    return keyboard


def form_chats(id_from, id_to):
    """
    Function to create keyboard with chat
    Arguments:
    id_from     -> User id 
    id_to       -> User id

    Returns:
    Keyboard with messages from chat
    """
    # Get messages from chat
    ten_messages = connection.get_chat(id_from, id_to)
    # Reverse list, so we may add old messages at first
    ten_messages.reverse()
    
    # Create new keyboard
    keyboard = telebot.types.InlineKeyboardMarkup()
    # Add new bttns
    # callback - text from bttn
    for message in ten_messages:
        keyboard.add(telebot.types.InlineKeyboardButton(str(message.from_user) + ": " + message.text, callback_data=message.text))
    # Add menu bttn
    keyboard.add(telebot.types.InlineKeyboardButton("Выйти", callback_data="menu" + str(id_from)))
    
    # Return formed keyboard
    return keyboard


# Polling bot
bot.polling()