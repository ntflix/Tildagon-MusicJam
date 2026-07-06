# pyright: reportUnusedParameter=false, reportUnknownParameterType=false, reportUnknownParameterType=false, reportMissingParameterType=false

from .ButtonEvent import ButtonEvent


class Focusable:
    def __init__(self): ...

    def draw(
        self,
        ctx,
    ) -> None: ...

    def handle_button(self, event, buttonEventType: ButtonEvent): ...

    def update(self, delta: int) -> bool:
        return True

    def close(self) -> None:
        pass

    async def start(self) -> None: ...
