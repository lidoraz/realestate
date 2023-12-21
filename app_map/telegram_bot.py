import os
from ext.crypto import encrypt
import telebot
from telebot import types
import urllib.parse

API_TOKEN = os.getenv("TELEGRAM_BOT_REALESTATE_DEALS")
assert os.getenv("TELEGRAM_USERID_SALT")  # used for crypto
assert API_TOKEN
URL_TO = "https://realestate1.up.railway.app/register_?telegram_id={}"


def serve_bot_threaded():
    import threading
    t = threading.Thread(target=server_bot, daemon=True)
    t.start()


def server_bot():
    print("telebot server_bot started")
    # exit(0)

    bot = telebot.TeleBot(API_TOKEN)

    c1 = types.BotCommand(command='start', description='Start the Bot')
    c2 = types.BotCommand(command='edit', description='Edit configs')
    c3 = types.BotCommand(command='help', description='Click for Help')
    bot.set_my_commands([c1, c2, c3])

    user_dict = {}
    cities_holder = {}

    def get_details(message):
        uid = message.from_user.id
        user_config = user_dict[uid]
        return user_config, message.text

    def is_legit(value, options, is_num=False):
        if is_num and value.is_digit():
            return

    start_str = "Hello! I am a Telegram bot, I will help you get new deals in rent and sale of real estate"
    start_str += "\nTo continue, please click here:"
    start_str += f"\n <a href='{URL_TO}'>Register</a>"

    # TODO: ADD option to DELETE config from here just with user ID.

    @bot.message_handler(commands=['start'])
    def _1start(message):
        uid = message.from_user.id
        print(f"{uid=}")
        bot.set_chat_menu_button(message.chat.id, types.MenuButtonCommands('commands'))
        uid_enc = urllib.parse.quote(encrypt(uid))
        bot.send_message(chat_id=message.chat.id, text=start_str.format(uid_enc),
                         parse_mode="HTML")

        # msg = bot.send_message(message.chat.id, start_str.format(uid))
        # bot.register_next_step_handler(msg, _2choose_cities)

    print("Started bot...")
    bot.infinity_polling()
