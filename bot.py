import logging
from contextlib import suppress

from aiogram import (Bot,
                     Dispatcher,
                     executor,
                     types)
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.storage import FSMContext
from aiogram.utils.exceptions import MessageNotModified
from aiogram.utils.markdown import hbold

from keyboards import (get_colour_keyboard,
                       get_main_keyboard,
                       get_timer_keyboard,
                       get_white_keyboard)
from config import Config
from smart_lamp_api import (SmartLampAPIError,
                            TimeoutSmartLampAPIError,
                            UnknownSmartLampAPIError)
from texts import (get_colour_text,
                   get_timer_text,
                   get_time,
                   get_white_text)


logging.basicConfig(level=logging.INFO)
bot = Bot(token=Config.env.bot_token, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())


def get_white_data() -> tuple[str, types.InlineKeyboardMarkup]:
    return get_white_text(), get_white_keyboard()


def get_colour_data() -> tuple[str, types.InlineKeyboardMarkup]:
    return get_colour_text(), get_colour_keyboard()


def get_timer_data() -> tuple[str, types.InlineKeyboardMarkup]:
    return get_timer_text(), get_timer_keyboard()


async def set_data(callback_query: types.CallbackQuery, value: str) -> tuple[str, types.InlineKeyboardMarkup]:
    text, keyboard = get_timer_data()
    try:
        if value in ('brightness', 'temp'):
            Config.states['mode'] = 'white'
            text, keyboard = get_white_data()
            await Config.smart_lamp_api.set_white(brightness=Config.states.brightness,
                                                  temp=Config.states.temp)
        if value in ('h', 's', 'v'):
            Config.states['mode'] = 'colour'
            text, keyboard = get_colour_data()
            await Config.smart_lamp_api.set_color(h=Config.states.h, s=Config.states.s, v=Config.states.v)
    except (SmartLampAPIError, TimeoutSmartLampAPIError, UnknownSmartLampAPIError) as e:
        await callback_query.answer(text=e, show_alert=True)
    return text, keyboard


@dp.message_handler(user_id=Config.env.bot_user_ids, state='*')
async def main(message: types.Message):
    try:
        Config.states['on_off'] = (await Config.smart_lamp_api.get_states)['on_off']
        await message.answer(text=hbold('Выбери команду'), reply_markup=get_main_keyboard())
    except (SmartLampAPIError, TimeoutSmartLampAPIError, UnknownSmartLampAPIError) as e:
        await message.answer(text=e)


@dp.callback_query_handler(text='on_off', user_id=Config.env.bot_user_ids, state='ready')
async def on_off(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state('not_ready')
    try:
        status = not (await Config.smart_lamp_api.get_states)['on_off']
        Config.states.update(on_off=status, time=None)
        await Config.smart_lamp_api.set_on_off(value=Config.states.on_off)
        with suppress(MessageNotModified):
            await callback_query.message.edit_reply_markup(reply_markup=get_main_keyboard())
        await callback_query.answer()
    except (SmartLampAPIError, TimeoutSmartLampAPIError, UnknownSmartLampAPIError) as e:
        await callback_query.answer(text=e, show_alert=True)
    await state.set_state('ready')


@dp.callback_query_handler(text_startswith='scene', user_id=Config.env.bot_user_ids, state='ready')
async def scene(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state('not_ready')
    value = callback_query.data.split('_')[1]
    try:
        await Config.smart_lamp_api.set_scene(scene=value)
        Config.states.update(mode='scene', scene=value)
        with suppress(MessageNotModified):
            await callback_query.message.edit_reply_markup(reply_markup=get_main_keyboard())
        await callback_query.answer()
    except (SmartLampAPIError, TimeoutSmartLampAPIError, UnknownSmartLampAPIError) as e:
        await callback_query.answer(text=e, show_alert=True)
    await state.set_state('ready')


@dp.callback_query_handler(text='white', user_id=Config.env.bot_user_ids, state='*')
async def white(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(text=get_white_text(),
                                           reply_markup=get_white_keyboard())
    await callback_query.answer()


@dp.callback_query_handler(text='colour', user_id=Config.env.bot_user_ids, state='*')
async def colour(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(text=get_colour_text(),
                                           reply_markup=get_colour_keyboard())
    await callback_query.answer()


@dp.callback_query_handler(text='timer', user_id=Config.env.bot_user_ids, state='*')
async def timer(callback_query: types.CallbackQuery):
    try:
        current_states = await Config.smart_lamp_api.get_states
        new_states = {'on_off': not current_states['on_off']}
        if not current_states['timer']:
            new_states['time'] = None
        Config.states.update(**new_states)
        text, keyboard = get_timer_data()
        await callback_query.message.edit_text(text=text, reply_markup=keyboard)
        await callback_query.answer()
    except (SmartLampAPIError, TimeoutSmartLampAPIError, UnknownSmartLampAPIError) as e:
        await callback_query.answer(text=e, show_alert=True)


@dp.callback_query_handler(text_startswith=['up_step', 'down_step'], user_id=Config.env.bot_user_ids, state='*')
async def action_step(callback_query: types.CallbackQuery):
    action, _, value = callback_query.data.split('_')
    if action == 'up':
        Config.states + 'step'
    else:
        Config.states - 'step'
    text, keyboard = {'white': get_white_data, 'colour': get_colour_data, 'timer': get_timer_data}[value]()
    await callback_query.message.edit_text(text=text, reply_markup=keyboard)
    await callback_query.answer()


@dp.callback_query_handler(text_startswith=['up', 'down'], user_id=Config.env.bot_user_ids, state='ready')
async def down(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state('not_ready')
    action, value = callback_query.data.split('_')
    if action == 'up':
        Config.states + value
    else:
        Config.states - value
    text, keyboard = await set_data(callback_query=callback_query, value=value)
    await callback_query.message.edit_text(text=text, reply_markup=keyboard)
    await callback_query.answer()
    await state.set_state('ready')


@dp.callback_query_handler(text_startswith='default', user_id=Config.env.bot_user_ids, state='ready')
async def default(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state('not_ready')
    values = callback_query.data.split('_')
    if len(values) > 2:
        value = values[2]
        Config.states.default('step')
        text, keyboard = {'white': get_white_data, 'colour': get_colour_data, 'timer': get_timer_data}[value]()
    else:
        value = values[1]
        Config.states.default(value)
        text, keyboard = await set_data(callback_query=callback_query, value=value)
    with suppress(MessageNotModified):
        await callback_query.message.edit_text(text=text, reply_markup=keyboard)
    await callback_query.answer()
    await state.set_state('ready')


@dp.callback_query_handler(text='confirm', user_id=Config.env.bot_user_ids, state='ready')
async def confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state('not_ready')
    try:
        status = not (await Config.smart_lamp_api.get_states)['on_off']
        await Config.smart_lamp_api.set_timer(minutes=Config.states.timer)
        Config.states.update(on_off=status, time=get_time())
        text, keyboard = get_timer_data()
        with suppress(MessageNotModified):
            await callback_query.message.edit_text(text=text, reply_markup=keyboard)
        await callback_query.answer()
    except (SmartLampAPIError, TimeoutSmartLampAPIError, UnknownSmartLampAPIError) as e:
        await callback_query.answer(text=e, show_alert=True)
    await state.set_state('ready')


@dp.callback_query_handler(text='back', user_id=Config.env.bot_user_ids, state='*')
async def back(callback_query: types.CallbackQuery):
    try:
        Config.states['on_off'] = (await Config.smart_lamp_api.get_states)['on_off']
        await callback_query.message.edit_text(text=hbold('Выбери команду'), reply_markup=get_main_keyboard())
        await callback_query.answer()
    except (SmartLampAPIError, TimeoutSmartLampAPIError, UnknownSmartLampAPIError) as e:
        await callback_query.answer(text=e, show_alert=True)


async def on_startup(_):
    for user_id in Config.env.bot_user_ids:
        await dp.current_state(user=int(user_id)).set_state('ready')
    await Config.init()


async def on_shutdown(_):
    await Config.stop()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True,
                           on_startup=on_startup,
                           on_shutdown=on_shutdown)
