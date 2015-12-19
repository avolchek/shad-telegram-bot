# -*- coding: utf-8 -*-
from telegram import Updater
import shelve
from collections import defaultdict
import logging
import schedule_api
import datetime
import sys


class ChatDataStorage:
    def __init__(self):
        pass

    def open_database(self):
        self.db = shelve.open('chat_data.db', writeback=True)

    def close_database(self):
        self.db.close()

    def ensure(self, chat_id):
        if chat_id not in self.db:
            self.db[chat_id] = defaultdict(str)

    def get_data(self, chat_id, key):
        chat_id = str(chat_id)
        self.ensure(chat_id)
        return self.db[chat_id][key]

    def set_data(self, chat_id, key, value):
        chat_id = str(chat_id)
        self.ensure(chat_id)
        self.db[chat_id][key] = value

db = ChatDataStorage()


def help_command(bot, update):
    logging.debug('/help command called in chat {}'.format(update.message.chat_id))

    greeting = 'Привет. Я предоставляю информацию о расписании занятий для студентов БГУИР.\n' \
               'Доступные команды:\n' \
               '/help - список команд\n' \
               '/today - расписание на сегодня\n' \
               '/week - расписание на неделю\n' \
               '/group - задать номер учебной группы\n' \


    bot.sendMessage(chat_id=update.message.chat_id,
                    text=greeting
                    )

def set_group_command(bot, update):
    logging.debug('/group command called')

    instructions = 'Введите номер вашей группы.'

    bot.sendMessage(chat_id=update.message.chat_id,
                    text=instructions
                    )

    db.set_data(update.message.chat_id, 'state', 'wait-for-group')


def week_command(bot, update):
    logging.debug('/week command called in chat {}'.format(update.message.chat_id))

    group_token = db.get_data(update.message.chat_id, 'group')
    logging.debug('current group token is {}'.format(group_token))

    schedule = schedule_api.get_schedule(group_token)
    current_week = schedule_api.get_current_week()

    for i in xrange(7):
        message = u'{}\n{}'.format(
            schedule_api.get_weekdays_names()[i].title(),
            schedule_api.tabulate_schedule(
                schedule_api.get_day_shedule(schedule, i, current_week)
            )
        )

        bot.sendMessage(chat_id=update.message.chat_id,
                        text=message
                        )


def text_message(bot, update):
    logging.debug('new message in chat {}: {}'.format(
        update.message.chat_id,
        update.message.text
    ))

    chat_state = db.get_data(update.message.chat_id, 'state')

    if chat_state == 'wait-for-group':
        db.set_data(update.message.chat_id, 'state', '')

        group_name = update.message.text.strip()
        group_token = schedule_api.get_group_token(group_name)

        if group_token:
            db.set_data(update.message.chat_id, 'group', group_token)
            bot.sendMessage(chat_id=update.message.chat_id,
                            text='Группа успешно изменена.'
                            )
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text='Нету такой группы :('
                            )


def today_command(bot, update):
    logging.debug('/today command called in chat {}'.format(update.message.chat_id))

    weekday = datetime.datetime.now().weekday()
    current_week = schedule_api.get_current_week()

    group_token = db.get_data(update.message.chat_id, 'group')
    schedule = schedule_api.get_schedule(group_token)

    today_schedule = u'\n'.join([
        schedule_api.get_weekdays_names()[weekday].title(),
        schedule_api.tabulate_schedule(
            schedule_api.get_day_shedule(schedule, weekday, current_week)
        )
    ])

    bot.sendMessage(chat_id=update.message.chat_id,
                    text=today_schedule
                    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print 'usage: python {} bot_token'.format(sys.argv[0])
        sys.exit(0)

    updater = Updater(token=sys.argv[1])
    dispatcher = updater.dispatcher

    dispatcher.addTelegramCommandHandler('start', help_command)
    dispatcher.addTelegramCommandHandler('help', help_command)
    dispatcher.addTelegramCommandHandler('group', set_group_command)
    dispatcher.addTelegramCommandHandler('today', today_command)
    dispatcher.addTelegramCommandHandler('week', week_command)
    dispatcher.addTelegramMessageHandler(text_message)

    db.open_database()

    logging.debug('polling started...')
    updater.start_polling()

    while True:
        line = raw_input()

        if line == 'stop':
            break

    updater.stop()
    db.close_database()
