# pyright: reportMissingImports=false

from typing import Callable

import aioespnow

from .ButtonEvent import ButtonEvent
from .MusicEvent import MusicEvent
from .WiFiReset import wifi_reset
from .ESPNOWMessageType import ESPNOWMessageTypes
from .Room import Room
from .Magic import MAGIC, MagicError


class HostAndMessage:
    host: bytes
    payload: bytes

    def __init__(self, host: bytes, payload: bytes):
        self.host = host
        self.payload = payload


class TimeoutError(Exception):
    pass


class Comms:
    room: Room | None = None
    onRoomJoined: Callable[[Room], None] | None = None

    def __init__(self):
        self.__sta = wifi_reset()
        self.__espnow = aioespnow.AIOESPNow()
        self.__espnow.config(timeout_ms=5000)
        print(f"STA channel: {self.__sta.config('channel')}")
        self.__espnow.active(True)

    def processMessage(
        self,
        message: HostAndMessage,
    ) -> None:
        if len(message.payload) < 5:
            raise ValueError("Message is too short to contain a message type")
        if not message.payload.startswith(MAGIC):
            # print(message.payload.decode("utf-8"))
            # raise MagicError("Invalid magic bytes in message")
            pass

        messageType: int = ESPNOWMessageTypes.fromValue(message.payload[4])

        if messageType == ESPNOWMessageTypes.ADVERTISEMENT:
            roomID: int = message.payload[5]
            if self.room is not None:
                print(
                    f"Received advertisement for room {roomID}, but already in room {self.room}. Ignoring."
                )
            else:
                capabilities: bytes = message.payload[6:]
                print(
                    f"Room advertisement received: roomID={roomID}, capabilities={capabilities}"
                )
                self.room = Room(roomID, message.host)
                if self.onRoomJoined:
                    self.onRoomJoined(self.room)
                else:
                    print("Warning: no onRoomJoined callback set but room was joined.")
        elif messageType == ESPNOWMessageTypes.INSTRUMENTS:
            print(
                f"Received instruments message: {message.payload[5:].decode('utf-8')}"
            )

    async def _receive(self) -> None:
        host, msg = await self.__espnow.arecv()
        if msg is None:
            raise TimeoutError("No message received")

        self.processMessage(HostAndMessage(host, msg))

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

    async def joinRoom(self, onRoomJoined: Callable[[Room], None]):
        self.room = None
        self.onRoomJoined = onRoomJoined

        while self.room is None:
            try:
                await self._receive()
            except TimeoutError:
                print("Timeout waiting for room info, retrying...")
                continue
