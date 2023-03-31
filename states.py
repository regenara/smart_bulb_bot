from typing import Any


class States:
    def __init__(self, on_off: bool, mode: str, scene: str, brightness: int,
                 temp: int, h: int, s: int, v: int, timer: int):
        self.on_off: bool = on_off
        self.mode: str = mode
        self.scene: str = scene
        self.brightness: int = brightness
        self.temp: int = temp
        self.h: int = h
        self.s: int = s
        self.v: int = v
        self.timer: int = timer or 1
        self.time: str | None = None
        self.step: int = 1
        self.step_index: int = 0
        self.steps = [1, 5, 10, 50, 100]

    def __setitem__(self, key: str, value: Any):
        setattr(self, key, value)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __add__(self, key: str):
        if key == 'step':
            self.step_index = self.step_index + 1 if self.step_index + 1 < 6 else 5
            self.step = self.steps[self.step_index]
        else:
            maximals = {'brightness': 100, 'temp': 100, 'h': 360, 's': 100, 'v': 100, 'timer': 1440}
            self[key] = self[key] + self.step
            if self[key] > maximals[key]:
                self[key] = maximals[key]

    def __sub__(self, key: str):
        if key == 'step':
            self.step_index = self.step_index - 1 if self.step_index - 1 > -1 else 0
            self.step = self.steps[self.step_index]
        else:
            minimals = {'brightness': 1, 'temp': 0, 'h': 0, 's': 0, 'v': 0, 'timer': 1}
            self[key] = self[key] - self.step
            if self[key] < minimals[key]:
                self[key] = minimals[key]

    def update(self, **values):
        for key, value in values.items():
            self[key] = value

    def default(self, key: str):
        if key == 'step':
            self.update(step_index=2, step=10)
        else:
            self[key] = {'brightness': 50, 'temp': 50, 'h': 180, 's': 50, 'v': 50, 'timer': 480}[key]
