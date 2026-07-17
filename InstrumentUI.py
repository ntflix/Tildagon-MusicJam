# pyright: reportUnknownVariableType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnannotatedClassAttribute=false, reportMissingParameterType=false, reportMissingImports=false, reportAttributeAccessIssue=false

import asyncio
import time
from typing import Any, Callable
from .MusicEvent import MusicEvent, NullEvent, Note
from .Focusable import Focusable
from .ButtonEvent import ButtonEvent, DOWN, UP
from .Instrument import Instrument
from .PurplePattern import PurpleRandom
from .Comms import Comms

from system.eventbus import eventbus
from system.patterndisplay.events import PatternSet
from events.input import Buttons, ButtonDownEvent, ButtonUpEvent
from app_components import set_color


class InstrumentUI(Focusable):
    BUTTON_VALUES = {
        "A": Note(0),
        "B": Note(1),
        "C": Note(2),
        "D": Note(3),
        "E": Note(4),
        "F": Note(5),
        # 2026 frontboard touchpads
        "TOUCH1": Note(0),
        "TOUCH2": Note(1),
        "TOUCH3": Note(2),
        "TOUCH4": Note(3),
        "TOUCH5": Note(4),
        "TOUCH6": Note(5),
        "TOUCH7": Note(6),
        "TOUCH8": Note(7),
        "TOUCH9": Note(8),
        "TOUCH10": Note(9),
        "TOUCH11": Note(10),
        "TOUCH12": Note(11),
    }

    bridgeMAC: str | None = None
    instrument: Instrument
    _comms: Comms
    _notesOffset: int

    darkPurple = (0.2, 0.0, 0.2)
    purpleText = (0.6, 0.4, 0.6)
    lavenderText = (1.0, 0.8, 1.0)

    # Keepalive tracking
    _held_notes: dict[str, tuple[int, int]] = {}  # button_name -> (channel, note)
    _last_keepalive_time: int = 0
    _keepalive_interval_ms: int = 50  # Send keepalive every 50ms

    def __init__(
        self,
        instrument: Instrument,
        onMusicEvent: Callable[[MusicEvent, ButtonEvent], None],
        comms: Comms,
        notesOffset: int,
    ) -> None:
        super().__init__()
        self.held_buttons: set[Any] = set()
        self._held_notes = {}  # Initialize held notes tracking
        self.instrument = instrument
        self._onMusicEvent = onMusicEvent
        self._comms = comms
        self._notesOffset = notesOffset
        self._last_keepalive_time = 0
        # eventbus.emit(PurpleRandom)

    def _note_event_for_button(self, button_name: str) -> MusicEvent:
        event = self.BUTTON_VALUES.get(button_name)
        if event is None:
            return NullEvent()
        return event

    def handleButton(
        self, event: ButtonDownEvent, buttonEventType: ButtonEvent
    ) -> None:
        button_name = event.button.name

        if event.button.group == "TwentyTwentySix":
            # Handle as control button as only the TOUCH pads are notes on 2026 frontboard
            print(f"Control button pressed: {button_name}")

        if buttonEventType == DOWN:
            if button_name in self.held_buttons:
                return
            self.held_buttons.add(button_name)

            # Track the note value for this button (for keepalive purposes)
            music_event = self._note_event_for_button(button_name)
            if isinstance(music_event, Note):
                midi_note = music_event.value + self._notesOffset
                self._held_notes[button_name] = (self.instrument.midiChannel, midi_note)

            self._onMusicEvent(music_event, DOWN)
        elif buttonEventType == UP:
            self.held_buttons.discard(button_name)
            self._held_notes.pop(button_name, None)  # Remove from tracking
            self._onMusicEvent(self._note_event_for_button(button_name), UP)

    def draw(self, ctx) -> None:

        yOffset = 48
        lineHeight = 22

        # background colour
        set_color(ctx, self.darkPurple)
        ctx.rectangle(-120, -120, 240, 240).fill()

        ctx.font = "sans-serif"
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE

        bridge_connected = self.bridgeMAC is not None
        ctx.font_size = 20
        if bridge_connected:
            # ctx.rgb(0, 0.5, 0).move_to(0, -70).text(f"connected: {self.bridgeMAC}")
            ctx.rgb(self.purpleText[0], self.purpleText[1], self.purpleText[2])
            ctx.move_to(0, -yOffset).text("you are")

            ctx.font_size = 40
            # Calculate width at desired font size
            width = ctx.text_width(self.instrument.name)
            max_width = 230

            # Scale font down if text is too wide
            if width > max_width:
                ctx.font_size = 40 * max_width / width
                # round to nearest 0.125 for consistency
                ctx.font_size = int(ctx.font_size * 8) / 8

            ctx.rgb(self.lavenderText[0], self.lavenderText[1], self.lavenderText[2])
            ctx.move_to(0, 0).text(self.instrument.name)

            ctx.rgb(self.purpleText[0], self.purpleText[1], self.purpleText[2])
            ctx.font_size = 20

            if self.instrument.hint is not None:
                for i, line in enumerate(self.instrument.hint.splitlines()):
                    ctx.move_to(0, yOffset + ((i - 1) * lineHeight)).text(line)
            elif (
                self.instrument.shouldPitchBend == True
                and self.instrument.shouldModulate == True
            ):
                ctx.move_to(0, yOffset).text("tilt to pitch bend")
                ctx.move_to(0, yOffset + 18).text("and modulate!")
            elif self.instrument.shouldPitchBend == True:
                ctx.move_to(0, yOffset).text("tilt to pitch bend!")
            elif self.instrument.shouldModulate == True:
                ctx.move_to(0, yOffset).text("tilt to modulate!")
            else:
                ctx.move_to(0, yOffset).text("press some buttons!")
        else:
            ctx.font_size = 20
            ctx.rgb(0.8, 0.0, 0.1).move_to(0, -(yOffset + lineHeight)).text(
                "not connected."
            )

            ctx.rgb(
                self.purpleText[0],
                self.purpleText[1],
                self.purpleText[2],
            ).move_to(0, -yOffset * 0.8).text("go to the")

            ctx.font_size = 50
            ctx.rgb(
                self.lavenderText[0],
                self.lavenderText[1],
                self.lavenderText[2],
            ).move_to(0, 0).text("MusicJam")

            ctx.font_size = 20
            ctx.rgb(
                self.purpleText[0],
                self.purpleText[1],
                self.purpleText[2],
            ).move_to(0, yOffset * 0.8).text("installation to play!")

            # ctx.move_to(0, yOffset * 0.8 + lineHeight).text("to play!")

    def update(self, delta: int) -> bool:
        # Send keepalives for held notes at regular intervals
        current_time = time.ticks_ms()

        if self._held_notes and (
            current_time - self._last_keepalive_time >= self._keepalive_interval_ms
        ):
            loop = asyncio.get_event_loop()
            for channel, note in self._held_notes.values():
                loop.create_task(self._comms.sendNoteKeepalive(channel, note))
            self._last_keepalive_time = current_time

        return True

    def setBridgeMAC(self, mac: str) -> None:
        self.bridgeMAC = mac
