# pyright: reportUnknownVariableType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnannotatedClassAttribute=false, reportMissingParameterType=false, reportMissingImports=false

from typing import Any, Callable
from .MusicEvent import MusicEvent, NullEvent, Note
from .Focusable import Focusable
from .ButtonEvent import ButtonEvent, DOWN, UP

from app_components import clear_background
from events.input import Buttons, ButtonDownEvent, ButtonUpEvent
from frontboards.twentyfour import BUTTONS as BUTTONS_24
from frontboards.twentysix import (
    BUTTONS as BUTTONS_26,
    JOYSTICK as JOYSTICK_26,
    PROX as PROX_26,
    TOUCH as TOUCH_26,
)


class InstrumentUI(Focusable):
    BUTTON_VALUES = {
        "UP": Note(0),
        "RIGHT": Note(1),
        "CONFIRM": Note(2),
        "DOWN": Note(3),
        "LEFT": Note(4),
        "CANCEL": Note(5),
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

    bridge_mac: str | None = None

    def __init__(self, onMusicEvent: Callable[[MusicEvent, ButtonEvent], None]) -> None:
        super().__init__()
        self.held_buttons: set[Any] = set()
        self._onMusicEvent = onMusicEvent

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
            self.held_buttons.add(button_name)
            self._onMusicEvent(self._note_event_for_button(button_name), DOWN)
        elif buttonEventType == UP:
            self.held_buttons.discard(button_name)
            self._onMusicEvent(self._note_event_for_button(button_name), UP)

    def draw(self, ctx) -> None:
        clear_background(ctx)
        ctx.font = "sans-serif"
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE

        ctx.font_size = 30
        ctx.rgb(1, 0.8, 1).move_to(0, -52).text("MIDI")

        bridge_mac = self.bridge_mac
        bridge_connected = bridge_mac is not None
        ctx.font_size = 20
        if bridge_connected:
            ctx.rgb(0, 0.5, 0).move_to(0, -24).text(
                f"Connected to {bridge_mac[-4:].upper()}"
            )
        else:
            ctx.rgb(0.95, 0.1, 0.2).move_to(0, -24).text("Not connected to bridge")

        ctx.rgb(0.9, 0.2, 0.9).move_to(0, 48).text("Move to pitch")
        ctx.rgb(0.9, 0.2, 0.9).move_to(0, 64).text("bend and modulate!")
