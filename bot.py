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
from sber_smart_bulb_api.exceptions import SberSmartBulbAPIError

from config import Config
from keyboards import (get_auth_keyboard,
                       get_colour_keyboard,
                       get_main_keyboard,
                       get_timer_keyboard,
                       get_white_keyboard)
from states import States
from texts import (get_colour_text,
                   get_timer_text,
                   get_time,
                   get_white_text)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(name)s %(message)s', style='%')
bot = Bot(token=Config.env.bot_token, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())


async def set_states():
    states = (await Config.bulb_api.get_device_states(device_id=Config.env.device_id))
    Config.states = States(**(states.model_dump() | states.colour_data_v2.model_dump()))


def get_white_data() -> tuple[str, types.InlineKeyboardMarkup]:
    return get_white_text(), get_white_keyboard()


def get_colour_data() -> tuple[str, types.InlineKeyboardMarkup]:
    return get_colour_text(), get_colour_keyboard()


def get_timer_data() -> tuple[str, types.InlineKeyboardMarkup]:
    return get_timer_text(), get_timer_keyboard()


async def set_data(callback_query: types.CallbackQuery, value: str) -> tuple[str, types.InlineKeyboardMarkup]:
    text, keyboard = get_timer_data()
    try:
        if value in ('bright_value_v2', 'temp_value_v2'):
            Config.states.work_mode = 'white'
            text, keyboard = get_white_data()
            await Config.bulb_api.set_white(device_id=Config.env.device_id, brightness=Config.states.bright_value_v2,
                                            temp=Config.states.temp_value_v2)
        if value in ('h', 's', 'v'):
            Config.states.work_mode = 'colour'
            text, keyboard = get_colour_data()
            await Config.bulb_api.set_color(device_id=Config.env.device_id, h=Config.states.h, s=Config.states.s,
                                            v=Config.states.v)
    except SberSmartBulbAPIError as e:
        await callback_query.answer(text=str(e), show_alert=True)
    return text, keyboard


@dp.callback_query_handler(text='auth', user_id=Config.env.bot_user_ids, state='*')
async def auth(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state('auth_step_2')
    await callback_query.message.edit_text(text='Отправь номер телефона в формате 79998887766')
    await callback_query.answer()


@dp.message_handler(user_id=Config.env.bot_user_ids, state='auth_step_2')
async def auth_step_2(message: types.Message, state: FSMContext):
    try:
        response = await Config.bulb_api.authenticate(phone=message.text)
        await state.set_data({'ouid': response.ouid})
        await state.set_state('auth_step_3')
        await message.answer(text='На указанный номер отправлен код. Пришли его в ответном сообщении')
    except SberSmartBulbAPIError as e:
        await message.answer(text=str(e))


@dp.message_handler(user_id=Config.env.bot_user_ids, state='auth_step_3')
async def auth_step_3(message: types.Message, state: FSMContext):
    code = message.text.strip()
    if not code.isdigit() or len(code) != 5:
        await message.answer(text='Неверный код')
    else:
        ouid = (await state.get_data())['ouid']
        try:
            response = await Config.bulb_api.verify(ouid=ouid, sms_otp=message.text)
            await Config.bulb_api.get_access_token(authcode=response.authcode)
            await set_states()
            Config.states.on_off = (await Config.bulb_api.get_device_states(device_id=Config.env.device_id)).on_off
            await message.answer(text='Авторизация прошла успешно')
            text = 'Выбери команду' if Config.states.online else 'Лампа оффлайн!'
            await message.answer(text=hbold(text), reply_markup=get_main_keyboard())
        except SberSmartBulbAPIError as e:
            await message.answer(text=str(e))
        await state.set_state('ready')


@dp.message_handler(user_id=Config.env.bot_user_ids, state='*')
async def main(message: types.Message):
    try:
        states = (await Config.bulb_api.get_device_states(device_id=Config.env.device_id))
        Config.states.on_off = states.on_off
        text = 'Выбери команду' if states.online else 'Лампа оффлайн!'
        await message.answer(text=hbold(text), reply_markup=get_main_keyboard())
    except SberSmartBulbAPIError as e:
        await message.answer(text=str(e))


@dp.callback_query_handler(text='on_off', user_id=Config.env.bot_user_ids, state='ready')
async def on_off(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state('not_ready')
    try:
        status = not (await Config.bulb_api.get_device_states(device_id=Config.env.device_id)).on_off
        Config.states.update(on_off=status, time=None)
        await Config.bulb_api.set_on_off(device_id=Config.env.device_id, value=Config.states.on_off)
        with suppress(MessageNotModified):
            await callback_query.message.edit_reply_markup(reply_markup=get_main_keyboard())
        await callback_query.answer()
    except SberSmartBulbAPIError as e:
        await callback_query.answer(text=str(e), show_alert=True)
    await state.set_state('ready')


@dp.callback_query_handler(text_startswith='scene', user_id=Config.env.bot_user_ids, state='ready')
async def scene(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state('not_ready')
    value = callback_query.data.split(':')[1]
    try:
        await Config.bulb_api.set_scene(device_id=Config.env.device_id, scene=value)
        Config.states.update(work_mode='scene', light_scene=value)
        with suppress(MessageNotModified):
            await callback_query.message.edit_reply_markup(reply_markup=get_main_keyboard())
        await callback_query.answer()
    except SberSmartBulbAPIError as e:
        await callback_query.answer(text=str(e), show_alert=True)
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
        current_states = await Config.bulb_api.get_device_states(device_id=Config.env.device_id)
        new_states = {'on_off': not current_states.on_off}
        if not current_states.sleep_timer:
            new_states['time'] = None
        Config.states.update(**new_states)
        text, keyboard = get_timer_data()
        await callback_query.message.edit_text(text=text, reply_markup=keyboard)
        await callback_query.answer()
    except SberSmartBulbAPIError as e:
        await callback_query.answer(text=str(e), show_alert=True)


@dp.callback_query_handler(text_startswith=['up:step', 'down:step'], user_id=Config.env.bot_user_ids, state='*')
async def action_step(callback_query: types.CallbackQuery):
    action, _, value = callback_query.data.split(':')
    if action == 'up':
        Config.states + 'step'
    else:
        Config.states - 'step'
    text, keyboard = {'white': get_white_data, 'colour': get_colour_data, 'timer': get_timer_data}[value]()
    await callback_query.message.edit_text(text=text, reply_markup=keyboard)
    await callback_query.answer()


@dp.callback_query_handler(text_startswith=['up', 'down'], user_id=Config.env.bot_user_ids, state='ready')
async def up_down(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state('not_ready')
    action, value = callback_query.data.split(':')
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
    values = callback_query.data.split(':')
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
        status = not (await Config.bulb_api.get_device_states(device_id=Config.env.device_id)).on_off
        await Config.bulb_api.set_timer(device_id=Config.env.device_id, minutes=Config.states.sleep_timer)
        Config.states.update(on_off=status, time=get_time())
        text, keyboard = get_timer_data()
        with suppress(MessageNotModified):
            await callback_query.message.edit_text(text=text, reply_markup=keyboard)
        await callback_query.answer()
    except SberSmartBulbAPIError as e:
        await callback_query.answer(text=str(e), show_alert=True)
    await state.set_state('ready')


@dp.callback_query_handler(text='back', user_id=Config.env.bot_user_ids, state='*')
async def back(callback_query: types.CallbackQuery):
    try:
        states = (await Config.bulb_api.get_device_states(device_id=Config.env.device_id))
        Config.states.on_off = states.on_off
        text = 'Выбери команду' if states.online else 'Лампа оффлайн!'
        await callback_query.message.edit_text(text=hbold(text), reply_markup=get_main_keyboard())
        await callback_query.answer()
    except SberSmartBulbAPIError as e:
        await callback_query.answer(text=str(e), show_alert=True)


async def on_startup(_):
    for user_id in Config.env.bot_user_ids:
        await dp.current_state(user=user_id).set_state('ready')
    await Config.init()
    if not Config.bulb_api.refresh_token:
        await dp.bot.send_message(chat_id=Config.env.bot_user_ids[0], text='Необходима авторизация',
                                  reply_markup=get_auth_keyboard())
    else:
        await set_states()


async def on_shutdown(_):
    await Config.stop()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True,
                           on_startup=on_startup,
                           on_shutdown=on_shutdown)
