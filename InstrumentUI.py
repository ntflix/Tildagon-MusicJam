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
    instrumentName: str

    def __init__(
        self,
        instrumentName: str,
        onMusicEvent: Callable[[MusicEvent, ButtonEvent], None],
    ) -> None:
        super().__init__()
        self.held_buttons: set[Any] = set()
        self.instrumentName = instrumentName
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
            if button_name in self.held_buttons:
                return
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

        bridge_connected = self.bridgeMAC is not None
        ctx.font_size = 20
        if bridge_connected:
            ctx.rgb(0, 0.5, 0).move_to(0, -70).text(f"connected: {self.bridgeMAC}")
            ctx.rgb(0.9, 0.2, 0.9).move_to(0, 38).text("move to pitch bend")
            ctx.rgb(0.9, 0.2, 0.9).move_to(0, 56).text("and modulate!")
        else:
            ctx.rgb(0.95, 0.1, 0.2).move_to(0, -70).text("not connected")
        ctx.rgb(0, 0.6, 0.4).move_to(0, -40).text("you are")

        ctx.font_size = 40
        ctx.rgb(1.0, 0.8, 1.0)

        # Calculate width at desired font size
        width = ctx.text_width(self.instrumentName)
        max_width = 230

        # Scale font down if text is too wide
        if width > max_width:
            ctx.font_size = 40 * max_width / width
            # round to nearest 0.125 for consistency
            ctx.font_size = int(ctx.font_size * 8) / 8

        ctx.move_to(0, 0).text(self.instrumentName)

    def update(self, delta: int) -> bool:
        return True

    def setBridgeMAC(self, mac: str) -> None:
        self.bridgeMAC = mac
