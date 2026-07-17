# pyright: reportMissingImports=false, reportAttributeAccessIssue=false

import asyncio
import random
import time
from typing import Literal

from app import App
from imu import acc_read
from app_components import clear_background
from system.eventbus import eventbus
from system.scheduler import scheduler
from system.scheduler.events import RequestStopAppEvent
from system.espnow import espnow_service
from events.input import Buttons, ButtonDownEvent, ButtonUpEvent

from .MusicEvent import MusicEvent
from .MIDIEvent import MIDIEvent
from .PickInstrumentUI import PickInstrumentUI
from .InstrumentUI import InstrumentUI
from .Instrument import Instrument
from .Instruments import INSTRUMENTS
from .ButtonEvent import DOWN, UP, ButtonEvent
from .Comms import Comms
from .Room import Room

NOTES_OFFSET = 57  # MIDI note number for A3
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

    def onRoomJoined(self, room: Room):
        hostMACStr = room.hostMAC.hex()
        print(f"Joined room {room.id} with host {hostMACStr}")
        self.instrumentUI.bridgeMAC = (  # pyright: ignore[reportOptionalMemberAccess]
            hostMACStr[-4:].upper()
        )

    def __init__(self):
        scheduler.stop_app(espnow_service)
        self.comms = Comms()
        self.overlays = []
        self.cleared = False
        self.button_states = Buttons(self)
        self.pickInstrumentUI = PickInstrumentUI(
            app=self,
            # instruments=sorted(INSTRUMENTS, key=lambda i: i.midiChannel),
            instruments=list(INSTRUMENTS),
            onInstrumentSelected=lambda instrument: self.onInstrumentSelected(
                instrument
            ),
            onBack=self.minimise,
        )

        # Modulation state - avoid sending redundant packets
        self._last_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0)

    async def main_loop(self, delta_ticks: int, render_update):
        if self.activeUI == "instrumentUI":
            assert (
                self.instrumentUI is not None
            ), "Instrument UI must be active to update"
            if not self.comms.room:
                eventLoop = asyncio.get_event_loop()
                eventLoop.create_task(self.comms.joinRoom(self.onRoomJoined))
            else:
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

    def onInstrumentSelected(self, instrument: Instrument):
        self.instrument = instrument
        self.instrumentUI = InstrumentUI(
            instrument=self.instrument,
            onMusicEvent=self.handleMusicEvent,
            comms=self.comms,
            notesOffset=NOTES_OFFSET,
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
        assert (
            self.instrument is not None
        ), "Instrument must be selected to handle accelerometer"

        if not self.instrumentUI.held_buttons:
            return
        self.xyz = acc_read()
        modulation: int | None = None
        pitchBend: int | None = None
        loop = asyncio.get_event_loop()

        if self.instrument.shouldModulate:
            modulation = round((-self.xyz[0] + GRAVITY) / (2 * GRAVITY) * 127)
            modulation = max(0, min(127, modulation))  # Clamp to [0, 127]
            modulationEvent = MIDIEvent(
                self.instrument.midiChannel,  # pyright: ignore[reportOptionalMemberAccess]
                MIDIEvent.CONTROL_CHANGE,
                1,  # Modulation wheel CC number
                modulation,
            )
            loop.create_task(
                self.comms.sendMIDIEvent(
                    modulationEvent,
                    self.instrument.midiChannel,  # pyright: ignore[reportOptionalMemberAccess]
                )
            )  # pyright: ignore[reportOptionalMemberAccess]

        if self.instrument.shouldPitchBend:
            pitchBend = round((self.xyz[1] + GRAVITY) / (2 * GRAVITY) * 16383)
            pitchBend = max(0, min(16383, pitchBend))  # Clamp to [0, 16383]
            pitchBendEvent = MIDIEvent(
                self.instrument.midiChannel,  # pyright: ignore[reportOptionalMemberAccess]
                MIDIEvent.PITCH_BEND,
                pitchBend & 0x7F,  # LSB
                pitchBend >> 7,  # MSB
            )
            loop.create_task(
                self.comms.sendMIDIEvent(
                    pitchBendEvent,
                    self.instrument.midiChannel,  # pyright: ignore[reportOptionalMemberAccess]
                )  # pyright: ignore[reportOptionalMemberAccess]
            )

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
        if self.comms.room is None:
            print("Not connected to a room, cannot send MIDI event")
            return

        midiEvent = musicEvent.toMIDIEvent(
            midi_channel=self.instrument.midiChannel,  # pyright: ignore[reportOptionalMemberAccess]
            status="on" if buttonEventType == DOWN else "off",
            notesOffset=NOTES_OFFSET,  # pyright: ignore[reportOptionalMemberAccess]
        )

        loop = asyncio.get_event_loop()
        loop.create_task(
            self.comms.sendMIDIEvent(
                midiEvent,
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
        scheduler.start_app(espnow_service)
        eventbus.emit(RequestStopAppEvent(self))


__app_export__ = MusicJam
