# pyright: reportMissingImports=false

import asyncio

from app import App
from imu import acc_read
import random

from app_components import clear_background
from system.eventbus import eventbus
from system.scheduler.events import RequestStopAppEvent
from events.input import Buttons, ButtonDownEvent, ButtonUpEvent

from .MusicJamUI import MusicJamUI
from .ButtonEvent import DOWN, UP, ButtonEvent
from .Comms import Comms

GRAVITY = 9.81  # m/s2


class MusicJam(App):
    ui: MusicJamUI
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
        self.ui = MusicJamUI()

        # Modulation state - avoid sending redundant packets
        self._last_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0)

        eventbus.on(ButtonDownEvent, self.handle_button_down, self)
        eventbus.on(ButtonUpEvent, self.handle_button_up, self)

    async def run(self, render_update):
        # One render before join
        await render_update()

        # Join room (blocking until connected)
        await self.comms.join_a_room()

        # One render after join to show "connected to {mac}"
        await render_update()

        # Main loop: no UI update, no timer
        while True:
            await asyncio.sleep_ms(100)  # pyright: ignore [reportAttributeAccessIssue]
            self.modulate_per_accel()

    def modulate_per_accel(self):
        if not self.ui.held_buttons:
            return
        self.xyz = acc_read()
        loop = asyncio.get_event_loop()
        loop.create_task(self.comms.send_xyz(self.xyz))

    def draw(self, ctx):
        if not self.cleared:
            clear_background(ctx)
            self.cleared = True
        ctx.save()
        self.ui.draw(ctx)
        ctx.restore()

    def update(self, delta: int):
        return False

    def handle_button_event(self, noteName: str, buttonEventType: ButtonEvent):
        loop = asyncio.get_event_loop()
        loop.create_task(self.comms.send_note(noteName, buttonEventType))

    def handle_button_down(self, buttonDownEvent: ButtonDownEvent):
        event: tuple[str, ButtonEvent] | None = self.ui.handle_button(
            buttonDownEvent, DOWN
        )
        if event is not None:
            self.handle_button_event(event[0], event[1])

    def handle_button_up(self, buttonUpEvent: ButtonUpEvent):
        event: tuple[str, ButtonEvent] | None = self.ui.handle_button(buttonUpEvent, UP)
        if event is not None:
            self.handle_button_event(event[0], event[1])

    def quit(self):
        eventbus.emit(RequestStopAppEvent(self))


__app_export__ = MusicJam
