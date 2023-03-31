import os

from smart_lamp_api import SmartLampAPI
from states import States


class Environment:
    bot_token = os.getenv('BOT_TOKEN')
    bot_user_ids = os.getenv('BOT_USER_IDS').split(',')
    smart_home_token = os.getenv('SMART_HOME_TOKEN')
    lamp_device_id = os.getenv('LAMP_DEVICE_ID')
    timezone = os.getenv('TIMEZONE', 'Europe/Moscow')


class _Config:
    def __init__(self, env: Environment):
        self.env = env
        self.smart_lamp_api: SmartLampAPI | None = None
        self.states: States | None = None

    async def init(self):
        self.smart_lamp_api = SmartLampAPI(smart_home_token=self.env.smart_home_token,
                                           device_id=self.env.lamp_device_id)
        await self.smart_lamp_api.init()
        current_states = await self.smart_lamp_api.get_states
        self.states = States(**current_states)

    async def stop(self):
        await self.smart_lamp_api.session.close()


Config = _Config(env=Environment())
