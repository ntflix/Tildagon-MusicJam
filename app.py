# pyright: reportMissingImports=false, reportAttributeAccessIssue=false

import asyncio
import random
import time
from typing import Literal
import network

from app import App
from imu import acc_read
from app_components import clear_background
from system.eventbus import eventbus
from system.scheduler import scheduler
from system.scheduler.events import RequestStopAppEvent
from system.espnow import espnow_service
from events.input import Buttons, ButtonDownEvent, ButtonUpEvent

from system.hexpansion.app import HexpansionManagerApp
from system.patterndisplay.app import PatternDisplay
from system.backleds.app import BackLEDManager
from system.notification.app import NotificationService
from system.espnow import espnow_service
from system.launcher.app import Launcher
from system.power.app import PowerManager
from system.boopscreen.app import BoopSpinner

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
    request_fast_updates = True
    xyz: tuple[float, float, float] = (0.0, 0.0, 0.0)
    xyz_threshold: float = 0.1  # Minimum change in acceleration to send
    instrument: Instrument | None = None
    cleared: bool = False

    _radio_ready: bool = False
    _radio_task: asyncio.Task | None = None

    def get_random_midi_channel(self):
        return random.randint(0, 15)

    def onRoomJoined(self, room: Room):
        assert self.comms.room.id == room.id, "Joined room does not match comms room"
        hostMACStr = room.hostMAC.hex()
        print(f"Joined room {room.id} with host {hostMACStr}")
        self.instrumentUI.bridgeMAC = (  # pyright: ignore[reportOptionalMemberAccess]
            hostMACStr[-4:].upper()
        )

    def __init__(self):
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

    def kill_background_service(self) -> None:
        scheduler.stop_app(HexpansionManagerApp())

        # Start the spinning-tilde boop animation
        scheduler.stop_app(BoopSpinner())

        # Start led pattern displayer app
        scheduler.stop_app(PatternDisplay())

        # Start back led manager
        scheduler.stop_app(BackLEDManager())

        # Start root app
        scheduler.stop_app(Launcher())

        # Start notification handler
        scheduler.stop_app(NotificationService())

        # Start power management app
        scheduler.stop_app(PowerManager())

    async def _ensure_radio_setup(self):
        """
        Ensure espnow_service is not running and STA power management is PM_NONE.
        This is retried because scheduler stop is cooperative and WLAN can be briefly
        unavailable after reset.
        """
        sta = network.WLAN(network.STA_IF)
        pm_none = sta.PM_NONE

        # Keep retrying until we can set PM_NONE successfully.
        while not self._radio_ready:
            try:
                # Request stop repeatedly; scheduler stop is not always immediate.
                scheduler.stop_app(espnow_service)
            except Exception as e:
                print(f"ESP-NOW: stop_app request failed ({e})")

            try:
                sta = network.WLAN(network.STA_IF)
                sta.config(pm=pm_none)

                # Verify actual mode where possible.
                current_pm = None
                try:
                    current_pm = sta.config("pm")
                except Exception:
                    # Some builds may not support reading pm back; treat set success as enough.
                    pass

                if current_pm is None or current_pm == pm_none:
                    self._radio_ready = True
                    print("ESP-NOW: espnow_service stopped, STA PM set to PM_NONE")
                    return
                else:
                    print(
                        f"ESP-NOW: PM verify mismatch (got {current_pm}), retrying..."
                    )
            except OSError as e:
                print(f"ESP-NOW: deferring power management ({e})")
            except Exception as e:
                print(f"ESP-NOW: unexpected radio setup error ({e})")

            await asyncio.sleep_ms(50)

    async def keep_none_sta_pm(self):
        """
        Keep STA power management set to PM_NONE while this app is active.
        This is a workaround for some ESP32 builds where PM_NONE is not persistent.
        """
        sta = network.WLAN(network.STA_IF)
        pm_none = sta.PM_NONE

        while True:
            try:
                current_pm = sta.config("pm")
                if current_pm != pm_none:
                    print(
                        f"ESP-NOW: STA PM changed to {current_pm}, resetting to PM_NONE"
                    )
                    sta.config(pm=pm_none)
            except Exception as e:
                print(f"ESP-NOW: error checking STA PM ({e})")
            await asyncio.sleep_ms(1000)

    async def _startup(self, render_update):
        # Render once so launcher/UI stays responsive while radio setup converges.
        await render_update()
        self._radio_task = asyncio.create_task(self._ensure_radio_setup())
        await self._radio_task
        self._radio_task = None
        self.kill_background_service()

        self._keep_none_pm_task = asyncio.create_task(self.keep_none_sta_pm())
        # run it in the background, no need to await it

    async def main_loop(self, delta_ticks: int, render_update):
        # If radio setup is still converging, keep UI alive but avoid app logic that
        # depends on stable ESP-NOW/WLAN state.
        if not self._radio_ready:
            await render_update()
            return

        if self.activeUI == "instrumentUI":
            assert (
                self.instrumentUI is not None
            ), "Instrument UI must be active to update"
            if not self.comms.room:
                await self.comms.joinRoom(self.onRoomJoined)
            else:
                self.handleAccelerometer()

            self.instrumentUI.update(delta_ticks)
        elif self.activeUI == "pickInstrumentUI":
            self.pickInstrumentUI.update(delta_ticks)
        else:
            raise RuntimeError("No instrument selected and no instrument UI active")
        await render_update()

    async def run(self, render_update):
        await self._startup(render_update)

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
        # Cancel radio setup task if it's still running.
        if self._radio_task is not None and not self._radio_task.done():
            self._radio_task.cancel()
        # Return device to normal background behavior when leaving MusicJam.
        # If you want espnow_service to remain stopped globally, remove this line.
        scheduler.start_app(espnow_service)
        eventbus.emit(RequestStopAppEvent(self))


__app_export__ = MusicJam
