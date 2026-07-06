from .ButtonEvent import ButtonEvent
from .MusicEvent import MusicEvent


class Comms:
    def __init__(self):
        pass

    async def sendEvent(self, musicEvent: MusicEvent, button_event_type: ButtonEvent):
        print("sendEvent", musicEvent, button_event_type)

    async def sendXYZ(self, xyz: tuple[float, float, float]):
        print("sendXYZ", xyz)

    async def joinRoom(self):
        print("joinRoom")
