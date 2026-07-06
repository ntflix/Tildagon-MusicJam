# pyright: reportMissingImports=false, reportAttributeAccessIssue=false

import asyncio
import random
import time

from app import App
from imu import acc_read
from app_components import clear_background
from system.eventbus import eventbus
from system.scheduler.events import RequestStopAppEvent
from events.input import Buttons, ButtonDownEvent, ButtonUpEvent

from .MusicEvent import MusicEvent
from .Focusable import Focusable
from .PickInstrumentUI import PickInstrumentUI
from .InstrumentUI import InstrumentUI
from .Instrument import Instrument
from .Instruments import INSTRUMENTS
from .ButtonEvent import DOWN, UP, ButtonEvent
from .Comms import Comms
from typing import Literal

GRAVITY = 9.81  # m/s2


class MusicJam(App):
    pickInstrumentUI: PickInstrumentUI
    instrumentUI: InstrumentUI | None = None
    activeUI: Literal["pickInstrumentUI", "instrumentUI"] = "pickInstrumentUI"

    comms: Comms
    request_fast_updates = False
    xyz: tuple[float, float, float] = (0.0, 0.0, 0.0)
    xyz_threshold: float = 0.1  # Minimum change in acceleration to send
    instrument: Instrument | None = None

    def get_random_midi_channel(self):
        return random.randint(0, 15)

    def get_random_octave(self):
        return random.randint(2, 5)

    def __init__(self):
        self.comms = Comms()
        self.overlays = []
        self.cleared = False
        self.button_states = Buttons(self)
        self.pickInstrumentUI = PickInstrumentUI(
            app=self,
            instruments=sorted(INSTRUMENTS, key=lambda i: i.midiChannel),
            onInstrumentSelected=lambda instrument: self.onInstrumentSelected(
                instrument
            ),
            onBack=self.minimise,
        )

        # Modulation state - avoid sending redundant packets
        self._last_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0)

    async def main_loop(self, delta_ticks: int, render_update):
        if self.activeUI == "instrumentUI":
            self.handleAccelerometer()
            self.instrumentUI.update(delta_ticks)
        elif self.activeUI == "pickInstrumentUI":
            self.pickInstrumentUI.update(delta_ticks)
        else:
            raise RuntimeError("No instrument selected and no instrument UI active")
        await render_update()

    async def run(self, render_update):
        last_time = time.ticks_ms()
        await render_update()
        while True:
            cur_time = time.ticks_ms()
            delta_ticks = time.ticks_diff(cur_time, last_time)
            await self.main_loop(delta_ticks, render_update)
            last_time = cur_time
        # One render before join
        await render_update()

        # Join room (blocking until connected)
        # await self.comms.joinRoom()

        # One render after join to show "connected to {mac}"
        await render_update()

        # Main loop: no UI update, no timer
        while True:
            # await asyncio.sleep_ms(0)  # pyright: ignore [reportAttributeAccessIssue]
            # self.handleAccelerometer()
            await render_update()

    def onInstrumentSelected(self, instrument: Instrument):
        self.instrument = instrument
        self.instrumentUI = InstrumentUI(
            instrumentName=self.instrument.name,
            onMusicEvent=self.handleMusicEvent,
        )
        eventbus.on(ButtonDownEvent, self.handleButtonDown, self)
        eventbus.on(ButtonUpEvent, self.handleButtonUp, self)
        self.pickInstrumentUI.close()
        self.pickInstrumentUI = None
        self.activeUI = "instrumentUI"
        print(
            f"Selected instrument: {instrument.name} (midiChannel {instrument.midiChannel})"
        )
        self.cleared = False

    def handleAccelerometer(self):
        assert (
            self.instrumentUI is not None
        ), "Instrument UI must be active to handle accelerometer"

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
        if self.activeUI == "pickInstrumentUI":
            self.pickInstrumentUI.draw(ctx)
        elif self.activeUI == "instrumentUI":
            assert self.instrumentUI is not None, "Instrument UI must be active to draw"
            self.instrumentUI.draw(ctx)
        ctx.restore()

    def handleMusicEvent(self, musicEvent: MusicEvent, buttonEventType: ButtonEvent):
        loop = asyncio.get_event_loop()
        loop.create_task(
            self.comms.sendEvent(
                musicEvent,
                buttonEventType,
                self.instrument.midiChannel,  # pyright: ignore[reportOptionalMemberAccess]
            )
        )

    def handleButtonDown(self, buttonDownEvent: ButtonDownEvent):
        assert (
            self.instrumentUI is not None
        ), "Instrument UI must be active to handle button events"
        self.instrumentUI.handleButton(buttonDownEvent, DOWN)

    def handleButtonUp(self, buttonUpEvent: ButtonUpEvent):
        assert (
            self.instrumentUI is not None
        ), "Instrument UI must be active to handle button events"
        self.instrumentUI.handleButton(buttonUpEvent, UP)

    def quit(self):
        eventbus.emit(RequestStopAppEvent(self))


__app_export__ = MusicJam
