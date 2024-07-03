import asyncio
import logging
from typing import Any

from aiohttp import (ClientSession,
                     ClientTimeout,
                     TCPConnector)
from aiohttp.client_exceptions import ClientConnectorError


class SmartLampAPIError(Exception):
    """"""


class TimeoutSmartLampAPIError(SmartLampAPIError):
    """"""


class UnknownSmartLampAPIError(SmartLampAPIError):
    """"""


class SmartLampAPI:
    def __init__(self, smart_home_token: str, device_id: str):
        self._smart_home_token: str = smart_home_token
        self._device_id: str = device_id
        self._jwt_token: str | None = None
        self._logger = logging.getLogger('SmartLampAPI')
        self._logger.setLevel(logging.INFO)

        self.session: ClientSession = ClientSession(connector=TCPConnector(verify_ssl=False),
                                                    timeout=ClientTimeout(total=60))

    async def _send_request(self, url: str = None, method: str = 'PUT', states: list[dict[str, Any]] = None,
                            headers: dict[str, Any] = None) -> dict[str, Any]:

        url = url or f'https://gateway.iot.sberdevices.ru/gateway/v1/devices/{self._device_id}/state'
        data = {'desired_state': states, 'device_id': self._device_id} if states else None
        while True:
            try:
                headers_ = headers or {'x-auth-jwt': self._jwt_token}
                async with self.session.request(method, url, json=data, headers=headers_) as response:
                    json = await response.json()
                    if response.status == 401:
                        self._logger.error('Unauthorized, trying get jwt request=%s response=%s', data, json)
                        await self._set_jwt()
                        continue
                    if response.status != 200:
                        self._logger.error('Unsuccessful request=%s response=%s', data, json)
                        state = json.get('state', {})
                        raise SmartLampAPIError(f'{state.get("title") or "Error"}: {state.get("message") or json}')
                    self._logger.info('Successful request=%s response=%s', data, json)
                    return json

            except asyncio.exceptions.TimeoutError:
                self._logger.error('TimeoutSmartLampAPIError request=%s', data)
                raise TimeoutSmartLampAPIError('Timeout error')

            except ClientConnectorError:
                self._logger.error('UnknownSmartLampAPIError request=%s', data)
                raise UnknownSmartLampAPIError('Unknown error')

    async def _set_jwt(self):
        url = 'https://companion.devices.sberbank.ru/v13/smarthome/token'
        headers = {'Authorization': f'Bearer {self._smart_home_token}'}
        data = await self._send_request(url=url, method='GET', headers=headers)
        self._jwt_token = data['token']

    @staticmethod
    def _get_states(reported_state: list[dict[str, Any]]) -> dict[str, Any]:
        states = {}
        for state in reported_state:
            if state['key'] == 'on_off':
                states['on_off'] = state['bool_value']
            if state['key'] == 'work_mode':
                states['mode'] = state['enum_value']
            if state['key'] == 'light_scene':
                states['scene'] = state['enum_value']
            if state['key'] == 'bright_value_v2':
                states['brightness'] = int(state['integer_value']) // 10 or 1
            if state['key'] == 'temp_value_v2':
                states['temp'] = int(state['integer_value']) // 10
            if state['key'] == 'colour_data_v2':
                states['h'] = state['color_value']['h']
                states['s'] = state['color_value']['s'] // 10
                states['v'] = state['color_value']['v'] // 10
            if state['key'] == 'sleep_timer':
                states['timer'] = int(state['integer_value']) // 60
        return states

    async def init(self):
        if self._jwt_token is None:
            await self._set_jwt()

    async def set_white(self, brightness: int, temp: int):
        """
        :param brightness: min 1, max 100
        :param temp: min 0, max 100
        """
        states = [
            {'key': 'light_mode', 'type': 'ENUM', 'enum_value': 'white'},
            {'key': 'light_brightness', 'type': 'INTEGER', 'integer_value': brightness * 10},
            {'key': 'light_colour_temp', 'type': 'INTEGER', 'integer_value': temp * 10}
        ]
        await self._send_request(states=states)

    async def set_color(self, h: int, s: int, v: int):
        """
        HSV (HSB) color model
        :param h: hue, min 0, max 360
        :param s: saturation, min 0, max 100
        :param v: value (brightness), min 0, max 100
        """
        states = [
            {'key': 'light_mode', 'type': 'ENUM', 'enum_value': 'colour'},
            {
                'key': 'light_colour',
                'colour_value': {'h': h, 's': s * 10, 'v': v * 10},
                'string_value': '{' + f'"h":{h},"s":{s * 10},"v":{v * 10}' + '}'
            }
        ]
        await self._send_request(states=states)

    async def set_scene(self, scene: str):
        """
        :param scene: candle | arctic | romantic | dawn | sunset | christmas | fito
        """
        states = [
            {'key': 'light_mode', 'type': 'ENUM', 'enum_value': 'scene'},
            {'key': 'light_scene', 'enum_value': scene, 'type': 'ENUM'}
        ]
        await self._send_request(states=states)

    async def set_timer(self, minutes: int):
        """
        :param minutes: min 0, max 1440
        """
        await self._send_request(states=[{'key': 'sleep_timer', 'type': 'INTEGER', 'integer_value': minutes * 60}])

    async def set_on_off(self, value: bool):
        """
        :param value: True - on, False - off
        """
        await self._send_request(states=[{'key': 'on_off', 'bool_value': value, 'type': 'BOOL'}])

    @property
    async def get_states(self) -> dict[str, Any]:
        data = await self._send_request(method='GET')
        return self._get_states(reported_state=data['reported_state'])
