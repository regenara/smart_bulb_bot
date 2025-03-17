from aiogram import types

from config import Config
from texts import get_time


def get_sc_button(text: str, scene: str) -> str:
    return f'{"✅ " if Config.states.work_mode == "scene" and Config.states.light_scene == scene else ""}{text}'


def get_md_button(text: str, mode: str) -> str:
    return f'{"✅ " if Config.states.work_mode == mode else ""}{text}'


def get_keyboard(row_width: int, buttons: list[list[tuple[str, str]]]) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=row_width)
    for row in buttons:
        buttons_data = []
        for text, callback in row:
            buttons_data.append(types.InlineKeyboardButton(text=text, callback_data=callback))
        keyboard.row(*buttons_data)
    return keyboard


def get_main_keyboard() -> types.InlineKeyboardMarkup:
    buttons = [
        [
            ('Выключить' if Config.states.on_off else 'Включить', 'on_off'),
            (get_sc_button('Свеча', 'candle'), 'scene:candle')
        ],
        [
            (get_sc_button('Северное сияние', 'arctic'), 'scene:arctic'),
            (get_sc_button('Романтика', 'romantic'), 'scene:romantic')
        ],
        [
            (get_sc_button('Рассвет', 'dawn'), 'scene:dawn'),
            (get_sc_button('Закат', 'sunset'), 'scene:sunset')
        ],
        [
            (get_sc_button('Новогодний', 'christmas'), 'scene:christmas'),
            (get_sc_button('Фитосвет', 'fito'), 'scene:fito')
        ],
        [
            (get_md_button('Белый', 'white'), 'white'),
            (get_md_button('Цветной', 'colour'), 'colour')
        ],
        [
            ('Таймер', 'timer')
        ]
    ]
    return get_keyboard(row_width=2, buttons=buttons)


def get_white_keyboard() -> types.InlineKeyboardMarkup:
    buttons = [[], [], [], []]
    if Config.states.bright_value_v2 > 1:
        buttons[0].append(('◀️', 'down:bright_value_v2'))
    buttons[0].append(('Яркость', 'default:bright_value_v2'))
    if Config.states.bright_value_v2 < 100:
        buttons[0].append(('▶️', 'up:bright_value_v2'))
    if Config.states.temp_value_v2 > 1:
        buttons[1].append(('◀️', 'down:temp_value_v2'))
    buttons[1].append(('Температура', 'default:temp_value_v2'))
    if Config.states.temp_value_v2 < 100:
        buttons[1].append(('▶️', 'up:temp_value_v2'))
    if Config.states.step_index > 0:
        buttons[2].append(('◀️', 'down:step:white'))
    buttons[2].append(('Шаг', 'default:step:white'))
    if Config.states.step_index < 4:
        buttons[2].append(('▶️', 'up:step:white'))
    buttons[3].append(('⤴️ Назад', 'back'))
    return get_keyboard(row_width=3, buttons=buttons)


def get_colour_keyboard() -> types.InlineKeyboardMarkup:
    buttons = [[], [], [], [], []]
    if Config.states.h > 0:
        buttons[0].append(('◀️', 'down:h'))
    buttons[0].append(('Тон', 'default:h'))
    if Config.states.h < 360:
        buttons[0].append(('▶️', 'up:h'))
    if Config.states.s > 0:
        buttons[1].append(('◀️', 'down:s'))
    buttons[1].append(('Насыщенность', 'default:s'))
    if Config.states.s < 100:
        buttons[1].append(('▶️', 'up:s'))
    if Config.states.v > 0:
        buttons[2].append(('◀️', 'down:v'))
    buttons[2].append(('Яркость', 'default:v'))
    if Config.states.v < 100:
        buttons[2].append(('▶️', 'up:v'))
    if Config.states.step_index > 0:
        buttons[3].append(('◀️', 'down:step:colour'))
    buttons[3].append(('Шаг', 'default:step:colour'))
    if Config.states.step_index < 4:
        buttons[3].append(('▶️', 'up:step:colour'))
    buttons[4].append(('⤴️ Назад', 'back'))
    return get_keyboard(row_width=3, buttons=buttons)


def get_timer_keyboard() -> types.InlineKeyboardMarkup:
    buttons = [[], [], [], []]
    if Config.states.sleep_timer > 1:
        buttons[0].append(('◀️', f'down:sleep_timer'))
    buttons[0].append(('Минуты', f'default:sleep_timer'))
    if Config.states.sleep_timer < 1440:
        buttons[0].append(('▶️', f'up:sleep_timer'))
    if Config.states.step_index > 0:
        buttons[1].append(('◀️', f'down:step:timer'))
    buttons[1].append(('Шаг', f'default:step:timer'))
    if Config.states.step_index < 4:
        buttons[1].append(('▶️', f'up:step:timer'))
    buttons[2].append((f"{'Включить' if Config.states.on_off else 'Выключить'} в {get_time()}", f'confirm'))
    buttons[3].append(('⤴️ Назад', 'back'))
    return get_keyboard(row_width=3, buttons=buttons)


def get_auth_keyboard() -> types.InlineKeyboardMarkup:
    buttons = [[('Авторизоваться', 'auth')]]
    return get_keyboard(row_width=1, buttons=buttons)
