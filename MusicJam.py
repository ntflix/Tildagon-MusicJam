# pyright: reportMissingImports=false

import asyncio

from MusicEvent import MusicEvent
from app import App
from imu import acc_read
import random

from app_components import clear_background
from system.eventbus import eventbus
from system.scheduler.events import RequestStopAppEvent
from events.input import Buttons, ButtonDownEvent, ButtonUpEvent

from .InstrumentUI import InstrumentUI
from .ButtonEvent import DOWN, UP, ButtonEvent
from .Comms import Comms

GRAVITY = 9.81  # m/s2


class MusicJam(App):
    instrumentUI: InstrumentUI
    comms: Comms
    request_fast_updates = False
    xyz: tuple[float, float, float] = (0.0, 0.0, 0.0)
    xyz_threshold: float = 0.1  # Minimum change in acceleration to send

    def get_random_midi_channel(self):
        return random.randint(0, 15)

    def get_random_octave(self):
        return random.randint(2, 5)

    def __init__(self):
        self.comms = Comms()
        self.overlays = []
        self.cleared = False
        self.button_states = Buttons(self)
        self.instrumentUI = InstrumentUI(onMusicEvent=self.handleButtonEvent)

        # Modulation state - avoid sending redundant packets
        self._last_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0)

        eventbus.on(ButtonDownEvent, self.handleButtonDown, self)
        eventbus.on(ButtonUpEvent, self.handleButtonUp, self)

    async def run(self, render_update):
        # One render before join
        await render_update()

        # Join room (blocking until connected)
        await self.comms.joinRoom()

        # One render after join to show "connected to {mac}"
        await render_update()

        # Main loop: no UI update, no timer
        while True:
            await asyncio.sleep_ms(0)  # pyright: ignore [reportAttributeAccessIssue]
            self.handleAccelerometer()

    def handleAccelerometer(self):
        if not self.instrumentUI.held_buttons:
            return
        self.xyz = acc_read()
        loop = asyncio.get_event_loop()
        loop.create_task(self.comms.sendXYZ(self.xyz))

    def draw(self, ctx):
        if not self.cleared:
            clear_background(ctx)
            self.cleared = True
        ctx.save()
        self.instrumentUI.draw(ctx)
        ctx.restore()

    def update(self, delta: int):
        return False

    def handleButtonEvent(self, musicEvent: MusicEvent, buttonEventType: ButtonEvent):
        loop = asyncio.get_event_loop()
        loop.create_task(self.comms.sendEvent(musicEvent, buttonEventType))

    def handleButtonDown(self, buttonDownEvent: ButtonDownEvent):
        self.instrumentUI.handleButton(buttonDownEvent, DOWN)

    def handleButtonUp(self, buttonUpEvent: ButtonUpEvent):
        self.instrumentUI.handleButton(buttonUpEvent, UP)

    def quit(self):
        eventbus.emit(RequestStopAppEvent(self))


__app_export__ = MusicJam
