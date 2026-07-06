# pyright: reportMissingImports=false

from .Focusable import Focusable
from .Instrument import Instrument

from app_components import Menu, clear_background
from typing import Callable


class PickInstrumentUI(Focusable):
    menu: Menu

    def __init__(
        self,
        instruments: list[Instrument],
        onInstrumentSelected: Callable[[Instrument], None],
        onBack: Callable[[], None],
    ):
        self.menu = Menu(
            menu_items=[instrument.name for instrument in instruments],
            #         select_handler: Callable[[str, int], Any],
            select_handler=lambda name, index: onInstrumentSelected(instruments[index]),
            back_handler=onBack,
        )

    def draw(self, ctx):
        clear_background(ctx)
        self.menu.draw(ctx)

    def update(self, delta):
        self.menu.update(delta)
