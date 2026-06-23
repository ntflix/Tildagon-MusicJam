import asyncio

from app import App
from imu import acc_read
import random

from app_components import clear_background
from system.eventbus import eventbus
from system.scheduler.events import RequestStopAppEvent
from events.input import Buttons, ButtonDownEvent, ButtonUpEvent

from .MIDIEvent import MIDIEvent
from .ESPNOWMIDIComms import ESPNOWMIDIComms
from .ESPNOWMIDIClientUI import ESPNOWMIDIClientUI

GRAVITY = 9.81  # m/s2


class ESPNOWMIDIClient(App):
    request_fast_updates = False

    def get_random_midi_channel(self):
        return random.randint(0, 15)

    def get_random_octave(self):
        return random.randint(2, 5)

    def __init__(self):
        self.overlays = []
        self.cleared = False
        self.button_states = Buttons(self)
        self.midi_comms = ESPNOWMIDIComms()
        self.current_channel = self.get_random_midi_channel()
        self.current_octave = self.get_random_octave()
        self.ui = ESPNOWMIDIClientUI(
            self.midi_comms, self.current_channel, self.current_octave
        )

        # Modulation state (to avoid sending redundant packets)
        self._last_modulation: int | None = None
        self._last_bend: int | None = None
        self._modulation_threshold = 1  # minimum CC delta to send
        self._bend_threshold = 1  # minimum 14-bit delta to send

        eventbus.on(ButtonDownEvent, self.handle_button_down, self)
        eventbus.on(ButtonUpEvent, self.handle_button_up, self)

    async def run(self, render_update):
        # One render before join (optional)
        await render_update()

        # Join room (blocking until connected)
        await self.midi_comms.join_a_room()

        # One render after join to show "connected to {mac}"
        await render_update()

        # Main loop: no UI update, no timer
        while True:
            await asyncio.sleep_ms(100)
            self.modulate_per_accel()

    def modulate_per_accel(self):
        if not self.ui.held_buttons:
            return

        xyz: tuple[float, float, float] = acc_read()

        # --- Modulation (CC1): X-axis tilt → 0..127 ---
        # Tilt left  (-1g) = 0, flat (0g) = 64, tilt right (+1g) = 127
        x_tilt = min(max(xyz[0], -GRAVITY), GRAVITY)
        modulation = round((x_tilt + GRAVITY) / (2 * GRAVITY) * 127)

        # --- Pitch Bend: Y-axis tilt → 0..16383 ---
        # Tilt back  (-1g) = 0, flat (0g) = 8192, tilt forward (+1g) = 16383
        y_tilt = min(max(xyz[1], -GRAVITY), GRAVITY)
        bend = round((y_tilt + GRAVITY) / (2 * GRAVITY) * 16383)

        # Change detection: only send when values moved enough
        send_cc = (
            self._last_modulation is None
            or abs(modulation - self._last_modulation) >= self._modulation_threshold
        )
        send_pb = (
            self._last_bend is None
            or abs(bend - self._last_bend) >= self._bend_threshold
        )

        loop = asyncio.get_event_loop()
        if send_cc:
            cc_event = MIDIEvent(
                midi_channel=self.current_channel,
                event_type=MIDIEvent.CONTROL_CHANGE,
                data_byte_1=1,  # CC1 = modulation wheel
                data_byte_2=modulation,
            )
            loop.create_task(self.midi_comms.send_midi_event(cc_event))
            self._last_modulation = modulation

        if send_pb:
            pb_event = MIDIEvent(
                midi_channel=self.current_channel,
                event_type=MIDIEvent.PITCH_BEND,
                data_byte_1=bend & 0x7F,  # LSB
                data_byte_2=(bend >> 7) & 0x7F,  # MSB
            )
            loop.create_task(self.midi_comms.send_midi_event(pb_event))
            self._last_bend = bend

    def draw(self, ctx):
        if not self.cleared:
            clear_background(ctx)
            self.cleared = True
        ctx.save()
        self.ui.draw(ctx)
        ctx.restore()

    def update(self, delta: int):
        return False

    def handle_button_down(self, event: ButtonDownEvent):
        midi_event = self.ui.handle_button_down(event)
        if midi_event is not None:
            loop = asyncio.get_event_loop()
            loop.create_task(self.midi_comms.send_midi_event(midi_event))

    def handle_button_up(self, event: ButtonUpEvent):
        midi_event = self.ui.handle_button_up(event)
        if midi_event is not None:
            loop = asyncio.get_event_loop()
            loop.create_task(self.midi_comms.send_midi_event(midi_event))

    def quit(self):
        eventbus.emit(RequestStopAppEvent(self))


__app_export__ = ESPNOWMIDIClient
