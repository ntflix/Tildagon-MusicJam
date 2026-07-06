# pyright: reportUnknownVariableType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnannotatedClassAttribute=false, reportMissingParameterType=false, reportMissingImports=false

from typing import Any, Callable
from app_components import clear_background
from events.input import BUTTON_TYPES

from .Focusable import Focusable
from .ButtonEvent import ButtonEvent, DOWN, UP


class MusicJamUI(Focusable):
    BUTTON_NOTE_NAMES = {
        "UP": "A",
        "RIGHT": "B",
        "CONFIRM": "C",
        "DOWN": "D",
        "LEFT": "E",
        "CANCEL": "F",
    }

    bridge_mac: str | None = None

    def __init__(self) -> None:
        super().__init__()
        self.held_buttons: set[Any] = set()

    def _note_label_for_button(self, button_name: str) -> str:
        note_name = self.BUTTON_NOTE_NAMES.get(button_name)
        if note_name is None:
            raise ValueError(f"Unknown button name: {button_name}")
        return note_name

    def _button_name(self, button) -> str | None:
        current = button
        while current is not None:
            for name, button_type in BUTTON_TYPES.items():
                if current == button_type:
                    return name
            current = getattr(current, "parent", None)
        return None

    def handle_button(
        self, event, buttonEventType: ButtonEvent
    ) -> tuple[str, ButtonEvent] | None:
        button_name = self._button_name(event.button)
        if button_name not in self.BUTTON_NOTE_NAMES:
            print(f"Unknown button: {button_name}")
            return None

        if buttonEventType == DOWN:
            if button_name in self.held_buttons:
                return None
            self.held_buttons.add(button_name)
            return self._note_label_for_button(button_name), DOWN
        elif buttonEventType == UP:
            if button_name not in self.held_buttons:
                return None
            self.held_buttons.discard(button_name)
            return self._note_label_for_button(button_name), UP

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
