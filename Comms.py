from .ButtonEvent import ButtonEvent
from .MusicEvent import MusicEvent


class Comms:
    def __init__(self):
        pass

    async def sendEvent(
        self,
        musicEvent: MusicEvent,
        buttonEventType: ButtonEvent,
        midiChannel: int,
    ):
        print(
            f"sendEvent: {musicEvent}, buttonEventType: {buttonEventType}, midiChannel: {midiChannel}"
        )

    async def sendXYZ(self, xyz: tuple[float, float, float]):
        print(f"sendXYZ: {xyz}")

    async def joinRoom(self):
        print(f"joinRoom")
