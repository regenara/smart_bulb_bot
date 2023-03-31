from aiogram import types

from config import Config
from texts import get_time


def get_sc_button(text: str, scene: str) -> str:
    return f'{"✅ " if Config.states.mode == "scene" and Config.states.scene == scene else ""}{text}'


def get_md_button(text: str, mode: str) -> str:
    return f'{"✅ " if Config.states.mode == mode else ""}{text}'


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
            (get_sc_button('Свеча', 'candle'), 'scene_candle')
        ],
        [
            (get_sc_button('Северное сияние', 'arctic'), 'scene_arctic'),
            (get_sc_button('Романтика', 'romantic'), 'scene_romantic')
        ],
        [
            (get_sc_button('Рассвет', 'dawn'), 'scene_dawn'),
            (get_sc_button('Закат', 'sunset'), 'scene_sunset')
        ],
        [
            (get_sc_button('Новогодний', 'christmas'), 'scene_christmas'),
            (get_sc_button('Фитосвет', 'fito'), 'scene_fito')
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
    if Config.states.brightness > 1:
        buttons[0].append(('◀️', 'down_brightness'))
    buttons[0].append(('Яркость', 'default_brightness'))
    if Config.states.brightness < 100:
        buttons[0].append(('▶️', 'up_brightness'))
    if Config.states.temp > 1:
        buttons[1].append(('◀️', 'down_temp'))
    buttons[1].append(('Температура', 'default_temp'))
    if Config.states.temp < 100:
        buttons[1].append(('▶️', 'up_temp'))
    if Config.states.step_index > 0:
        buttons[2].append(('◀️', 'down_step_white'))
    buttons[2].append(('Шаг', 'default_step_white'))
    if Config.states.step_index < 4:
        buttons[2].append(('▶️', 'up_step_white'))
    buttons[3].append(('⤴️ Назад', 'back'))
    return get_keyboard(row_width=3, buttons=buttons)


def get_colour_keyboard() -> types.InlineKeyboardMarkup:
    buttons = [[], [], [], [], []]
    if Config.states.h > 0:
        buttons[0].append(('◀️', 'down_h'))
    buttons[0].append(('Тон', 'default_h'))
    if Config.states.h < 360:
        buttons[0].append(('▶️', 'up_h'))
    if Config.states.s > 0:
        buttons[1].append(('◀️', 'down_s'))
    buttons[1].append(('Насыщенность', 'default_s'))
    if Config.states.s < 100:
        buttons[1].append(('▶️', 'up_s'))
    if Config.states.v > 0:
        buttons[2].append(('◀️', 'down_v'))
    buttons[2].append(('Яркость', 'default_v'))
    if Config.states.v < 100:
        buttons[2].append(('▶️', 'up_v'))
    if Config.states.step_index > 0:
        buttons[3].append(('◀️', 'down_step_colour'))
    buttons[3].append(('Шаг', 'default_step_colour'))
    if Config.states.step_index < 4:
        buttons[3].append(('▶️', 'up_step_colour'))
    buttons[4].append(('⤴️ Назад', 'back'))
    return get_keyboard(row_width=3, buttons=buttons)


def get_timer_keyboard() -> types.InlineKeyboardMarkup:
    buttons = [[], [], [], []]
    if Config.states.timer > 1:
        buttons[0].append(('◀️', f'down_timer'))
    buttons[0].append(('Минуты', f'default_timer'))
    if Config.states.timer < 1440:
        buttons[0].append(('▶️', f'up_timer'))
    if Config.states.step_index > 0:
        buttons[1].append(('◀️', f'down_step_timer'))
    buttons[1].append(('Шаг', f'default_step_timer'))
    if Config.states.step_index < 4:
        buttons[1].append(('▶️', f'up_step_timer'))
    buttons[2].append((f"{'Включить' if Config.states.on_off else 'Выключить'} в {get_time()}", f'confirm'))
    buttons[3].append(('⤴️ Назад', 'back'))
    return get_keyboard(row_width=3, buttons=buttons)
