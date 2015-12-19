# -*- coding: utf-8 -*-
import requests
import logging
from bs4 import BeautifulSoup
import tabulate
import re

_weekdays = [
        u'понедельник',
        u'вторник',
        u'среда',
        u'четверг',
        u'пятница',
        u'суббота',
        u'воскресенье'
    ]


def get_group_token(group_name):
    logging.info('gettting token for group {}...'.format(group_name))

    url = 'http://www.bsuir.by/schedule/rest/studentGroup'
    req = requests.get(url)

    logging.info('groups list obtainded, parsing...')

    soup = BeautifulSoup(req.content, 'lxml')

    for group in soup.find_all('studentgroup'):
        if group.find('name').string == group_name:
            return str(group.id.string)

    return None


def get_current_week():
    url = 'http://www.bsuir.by/schedule/schedule.xhtml'
    req = requests.get(url)

    soup = BeautifulSoup(req.content, 'html')

    week_string = soup.find_all('span', {'class': 'week'})[0].string

    return re.findall('\d', week_string)[0]


def get_schedule(group_token):
    logging.info('getting schedule for group {}...'.format(group_token))

    url = 'http://www.bsuir.by/schedule/rest/schedule/{}'.format(group_token)
    req = requests.get(url)

    logging.info('schedule obtained, parsing...')

    soup = BeautifulSoup(req.content.decode('utf-8'), 'lxml')

    def get_string_content(tag):
        return tag.string if tag else ''

    def get_employee_name(lesson_data):
        if not lesson_data.employee:
            return ''

        return u' '.join([
            get_string_content(lesson_data.employee.lastname),
            get_string_content(lesson_data.firstname),
            get_string_content(lesson_data.middlename)
        ])

    schedule = [[]] * 7

    for day_schedule_data in soup.find_all('schedulemodel'):
        weekday_id = _weekdays.index(day_schedule_data.weekday.string.lower())

        day_schedule = []

        for lesson in day_schedule_data.find_all('schedule'):
            day_schedule.append({
                'subgroup': int(lesson.numsubgroup.string),
                'weeknumbers': map(lambda t: int(t.string), lesson.find_all('weeknumber')),
                'time': get_string_content(lesson.lessontime),
                'subject': get_string_content(lesson.subject),
                'type': get_string_content(lesson.lessontype),
                'auditory': get_string_content(lesson.auditory),
                'employee': get_employee_name(lesson)
            })

        schedule[weekday_id] = day_schedule

    return schedule


def _make_lesson_table_row(lesson):
    subgroup = lesson['subgroup']
    return [
            lesson['time'],
            lesson['subject'],
            lesson['type'],
            lesson['auditory'],
            str(subgroup) + u' подгр.' if subgroup else u''
    ]


def get_day_shedule(schedule, weekday, week_number):
    return filter(lambda t: int(week_number) in t['weeknumbers'], schedule[weekday])


def tabulate_schedule(day_schedule):
    table = []

    for lesson in day_schedule:
        table.append(
            _make_lesson_table_row(lesson)
        )

    return tabulate.tabulate(table, tablefmt="plain")


def get_weekdays_names():
    return _weekdays
