import os

from sber_smart_bulb_api import SberSmartBulbAPI
from states import States


class Environment:
    bot_token = os.getenv('BOT_TOKEN')
    bot_user_ids = [int(uid) for uid in os.getenv('BOT_USER_IDS').split(',')]
    device_id = os.getenv('DEVICE_ID')
    timezone = os.getenv('TIMEZONE', 'Europe/Moscow')


class _Config:
    def __init__(self, env: Environment):
        self.env = env
        self.bulb_api: SberSmartBulbAPI | None = None
        self.states: States | None = None

    async def init(self):
        with open('sber_refresh_token') as f:
            refresh_token = f.read()
        self.bulb_api = SberSmartBulbAPI(refresh_token=refresh_token.strip())

    async def stop(self):
        await self.bulb_api.close()


Config = _Config(env=Environment())
