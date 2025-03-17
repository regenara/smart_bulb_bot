from datetime import (datetime,
                      timedelta)

from aiogram.utils.markdown import (hbold,
                                    hcode,
                                    hide_link)
from pytz import timezone

from config import Config


def get_white_text() -> str:
    return f'{hbold("Выстави настройки")}\n' \
           f'Яркость: {hcode(Config.states.bright_value_v2, "100", sep="/")}\n' \
           f'Температура: {hcode(Config.states.temp_value_v2, "100", sep="/")}\n' \
           f'Шаг: {hcode(Config.states.step, "100", sep="/")}'


def get_colour_text() -> str:
    url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/HueScale.svg/1920px-HueScale.svg.png'
    return f'{hbold("Выстави настройки")}\n' \
           f'Тон: {hcode(Config.states.h, "360", sep="/")}\n' \
           f'Насыщенность: {hcode(Config.states.s, "100", sep="/")}\n' \
           f'Яркость: {hcode(Config.states.v, "100", sep="/")}\n' \
           f'Шаг: {hcode(Config.states.step, "100", sep="/")}' \
           f'{hide_link(url)}'


def get_timer_text() -> str:
    on_off = 'Включить' if Config.states.on_off else 'Выключить'
    current = ''
    if Config.states.time is not None:
        current = f'Таймер {"выключения" if not Config.states.on_off else "включения"} ' \
                  f'установлен на {hcode(Config.states.time)}'
    return f'{hbold("Выстави настройки и нажми кнопку", on_off, sep=" ")}\n' \
           f'Минуты:  {hcode(f"{Config.states.sleep_timer}", "1440", sep="/")}\n' \
           f'Шаг:  {hcode(Config.states.step, "100", sep="/")}\n{current}'


def get_time() -> str:
    return (datetime.now(tz=timezone(Config.env.timezone)) +
            timedelta(minutes=Config.states.sleep_timer)).strftime('%H:%M')
