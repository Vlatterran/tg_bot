import datetime
import logging
import re
import time
from collections.abc import Iterable

import httpx
from bs4 import BeautifulSoup

MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24


def format_line(line):
    return f"\n{'=' * 40}\n{line['Время занятий']}: {line['Наименование дисциплины']}" \
           f"\n{line['Преподаватель']} | {line['Аудитория']} | {line['Вид занятий']}" \
           f" {('|' + line['Частота']) if 'Частота' in line else ''}"


dec_ru = {
    0: 'Понедельник',
    1: 'Вторник',
    2: 'Среда',
    3: 'Четверг',
    4: 'Пятница',
    5: 'Суббота',
    6: 'Воскресенье'
}
ru_dec = {
    'Понедельник': 0,
    'Вторник': 1,
    'Среда': 2,
    'Четверг': 3,
    'Пятница': 4,
    'Суббота': 5,
    'Воскресенье': 6
}
shortens = {
    'Числ': 'Числитель',
    'Знам': 'Знаменатель',
    'Еж': 'Еженедельно',
}


async def parse(groups: list[str] | None):
    async with httpx.AsyncClient() as client:
        response = await client.post('https://raspisanie.madi.ru/tplan/tasks/task3,7_fastview.php',
                                     data={'step_no': 1, 'task_id': 7})
        logging.info(response)
        soup = BeautifulSoup(response.text,
                             features='lxml')
        _groups = dict(map(lambda x: (x.attrs['value'], x.text),
                           soup.select('ul>li')))
        weekday = None
        schedule = {}
        requested_groups: Iterable[tuple[str, str]]
        if groups is None:
            requested_groups = _groups.items()
        else:
            groups = set(group.lower() for group in groups)
            requested_groups = filter(lambda kv: kv[1].lower() in groups, _groups.items())
        for group_id, group_name in requested_groups:
            group_schedule = schedule.setdefault(group_name, {})
            response = await client.post('https://raspisanie.madi.ru/tplan/tasks/tableFiller.php',
                                         data={'tab': 7, 'gp_name': group_name, 'gp_id': group_id})
            logging.info(response.text)
            soup = BeautifulSoup(response.text, features='lxml')
            raws = iter(soup.select('.timetable tr'))
            for raw in raws:
                children = [*raw.findChildren(('td', 'th'))]
                logging.info(children)
                if sum(1 for _ in children) == 1:
                    try:
                        weekday = raw.text
                    except KeyError:
                        break
                    try:
                        next(raws)
                    except StopIteration:
                        break
                else:
                    context = {'weekday': weekday, 'group': group_name}
                    line = {}
                    for i, cell in enumerate(children):
                        logging.debug(i, cell)
                        match i:
                            case 0:
                                line['Время занятий'] = cell.text
                            case 1:
                                line['Наименование дисциплины'] = cell.text
                            case 2:
                                line['Вид занятий'] = cell.text
                            case 3:
                                context['frequency'] = cell.text
                            case 4:
                                line['Аудитория'] = cell.text
                            case 5:
                                if cell.text == '':
                                    t = '--'
                                else:
                                    t = cell.text
                                line['Преподаватель'] = re.sub(r'\s{2,}', ' ', t)
                    try:
                        day = group_schedule.setdefault(context['weekday'], {})
                        logging.info(context)
                        if '.' in context['frequency']:
                            f = context['frequency'].split('.')
                            context['frequency'] = shortens[f[0]]
                            line['Частота'] = f[1]

                        day.setdefault(context['frequency'], []).append(line)
                    except KeyError:
                        if context['weekday'] != '\nПолнодневные занятия\n':
                            raise
                    except Exception as e:
                        print(type(e), e, f'\n{context}')
                        logging.exception(e)
                        break
    return schedule


class Schedule:
    def __init__(self, schedule: dict[str, dict[str, dict[str, list[dict[str, str]]]]]):
        self.schedule = schedule

    def lectures(self, day: str, group):
        date_regex = re.compile(r'(\b(0?[1-9]|[1-2][0-9]|3[0-1])[/.\\](1[0-2]|0?[1-9])\b)')
        if date_regex.match(day):
            date = [*map(int, re.split(r'[./\\-]', day))]
            requested_date = datetime.datetime(day=date[0], month=date[1], year=time.localtime().tm_year)
        else:
            requested_date = datetime.datetime.now()
            d = day.title()
            if d == '':
                pass
            if d == 'Завтра':
                requested_date += datetime.timedelta(days=1)
            elif d in ru_dec:
                requested_date += datetime.timedelta(days=(ru_dec[d] - requested_date.weekday()) % 7)
        try:
            week_day = dec_ru[requested_date.weekday()]
            week_type = 'Числитель' if is_week_even(requested_date) else 'Знаменатель'
            requested_schedule: list[dict] = self.schedule[group][week_day][week_type] + \
                                             self.schedule[group][week_day].get('Еженедельно', [])
            result = f'Расписание на {requested_date.strftime("%d.%m.%Y")} ' \
                     f'({week_day.lower()}/{week_type.lower()})'
            for i in sorted(requested_schedule, key=lambda line: line['Время занятий']):
                result += format_line(i)
            return result
        except KeyError as e:
            print(e)
            return 'Не удалось найти расписание на указанный день'

    def week_lectures(self, week_type: str):
        if week_type == '':
            f = 'Числитель' if is_week_even(datetime.date.today().timetuple()) else 'Знаменатель'
        else:
            f = week_type.title()
        result = f'Расписание на {f}'
        for day in ru_dec:
            try:
                requested_schedule = self.schedule[day][f]
                result += f'\n{day}'
                for i in requested_schedule:
                    result += format_line(line=i)
            except KeyError:
                pass
        return result


def is_week_even(day: datetime.date):
    return not bool(day.isocalendar().week % 2)
