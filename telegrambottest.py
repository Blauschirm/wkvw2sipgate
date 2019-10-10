from telegram.ext import Updater, CommandHandler, Filters, CallbackContext, MessageHandler
from telegram import Update, Message, Bot, ParseMode
import logging, json
from threading import Thread, Event
from crawl import get_month, TimeSlot
from typing import List, Set, Dict, Tuple, Optional
from math import ceil, floor

from main import init_logger


class IntervalThread(Thread):
    def __init__(self, timeout, callback):
        Thread.__init__(self)
        self.__stop_event = Event()
        self.callback = callback
        self.timeout = timeout

    def stop(self):
        self.__stop_event.set()

    def run(self):
        while not self.__stop_event.wait(self.timeout):
            print("Timer")
            self.callback()


# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

init_logger()
logger = logging.getLogger('telegrambot')

registered_chat_ids = [-1001463054189, 37081412, 119489385] # todo save / load from disk

command_descriptions = {}

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.message.chat_id, text=f"Oh, hello #{update.message.chat_id}")
    if not update.message.chat_id in registered_chat_ids:
        registered_chat_ids.append(update.message.chat_id)

def stop(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.message.chat_id, text=f"Bye #{update.message.chat_id}")
    registered_chat_ids.remove(update.message.chat_id)

def hello(update: Update, context: CallbackContext):
    # Stuff here
    # args will be available as context.args
    # jobqueue will be available as context.jobqueue
    update.message.reply_text(f'Hello {update.message.from_user.first_name}')

def echo(update: Update, context: CallbackContext):
    # Stuff here
    # args will be available as context.args
    # jobqueue will be available as context.jobqueue
    update.message.reply_text(f'{update.message.text[5:]}')

def help(update: Update, context: CallbackContext):
    global command_descriptions
    reply_text = "Hier sind alle verfügbaren Befehle:\n\n"
    reply_text += ''.join([str(key) + ":\n" + str(value) + "\n\n" for key, value in command_descriptions.items()])
    update.message.reply_text(reply_text)

def status(update: Update, context: CallbackContext):
    global TESTING
    update.message.reply_text(f"Der Bot läuft (yay!) {'im Testmodus' if TESTING else 'normal'}. Registered chats: {registered_chat_ids}")

def message_everybody(bot: Bot):
    print("MESSAGING EVERYBODY!")
    for id in registered_chat_ids:
        try:
            bot.send_message(chat_id=id, text="1 piep piep piep, ich hab euch alle lieb!")
        except Exception as err:
            print("Des hat ned 'klappt", err)

def return_day(update: Update, context: CallbackContext):
    day_id = int(context.args[0], 10) - 1 if len(context.args) > 0 else 0
    day_data: List[TimeSlot] = get_month()[day_id]
    reply_text = f"Fuer den {day_id + 1}.:\n"
    for shift_id, shift_name in enumerate(["NSF1", "NSFW2", "Dude?"]):
        max_phone_number_length = max(map(lambda slot: len(slot.phone_number), day_data[shift_id]), default=5)
        print("max phone number len", max_phone_number_length)
        reply_text += f"*Gruppe {shift_name}*\n"
        reply_text += "```\n" # Telegram does not currently support Markdown tables so have to use verbatim
        reply_text += f"|Start| End |{' ' * ceil((max_phone_number_length-5)/2.)}Phone{' ' * floor((max_phone_number_length-5)/2)}|\n"
        reply_text += f"|-----|-----|{'-' * max_phone_number_length}|\n"
        for slot in day_data[shift_id]:
            reply_text += f"|{slot.start_time}|{slot.end_time}|{slot.phone_number:{max_phone_number_length}}|\n"
        reply_text += "```\n"
    update.message.reply_markdown(reply_text)

def unknown_command(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")
    update.message.reply_text("Command unknown. Type /help to see the list of available commands.")

# Read config
with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)
TESTING = config_data["TESTING"]
token = config_data["telegram"]["token"]

command_descriptions.update({
    '/start' : "Startet den Bot und abonniert alle Updates.",
    '/stop' : "Deabonniert dich von allen Updates.",
    '/status' : "Zeigt den Status des Bots und Skriptes",
    '/day XX': "Zeigt die Umleitungen für den XXten Tag des Monats. Ohne Zahl, die von heute",
    '/help' : "Diese Hilfe, duuh",
    '/hello' : "Huhu",
    '/echo' : "ECHO, Echo, echo..."
    })

updater = Updater(token, use_context=True) # todo load bot ID from disk

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('stop', stop))
updater.dispatcher.add_handler(CommandHandler('hello', hello))
updater.dispatcher.add_handler(CommandHandler('echo', echo))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('status', status))
updater.dispatcher.add_handler(CommandHandler('day', return_day))
updater.dispatcher.add_handler(MessageHandler(Filters._Command(), unknown_command))

if len(updater.dispatcher.handlers[0]) - 1 != len(command_descriptions):
    # check if all commands are explained, the unknown command handler doesn't need explantion it is not callable
    logger.warning("Error with Command descriptions. Check if all commands are explained")

t = IntervalThread(60, lambda: message_everybody(updater.bot))
# t.start()

try:
    updater.start_polling()
    updater.idle()
finally:
    print("Forbei Ende Ous!")
    t.stop()