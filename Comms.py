# pyright: reportMissingImports=false

from typing import Callable

import aioespnow
import asyncio

from system.espnow import espnow_service
from system.espnow.events import EspNowReceiveEvent

from .ButtonEvent import ButtonEvent
from .MIDIEvent import MIDIEvent
from .WiFiReset import wifi_reset
from .ESPNOWMessageType import ESPNOWMessageTypes
from .ESPNOWBridgePacket import ESPNOWBridgePacket
from .Room import Room
from .Magic import MAGIC, MagicError

GRAVITY = 9.81  # m/s2


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
                try:
                    self.__espnow.add_peer(message.host)
                    print(f"Added peer {message.host.hex()} for room {roomID}")
                except OSError as e:
                    print(
                        f"Error adding peer {message.host.hex()}: {e}"
                    )  # this is here because sometimes this code path is reached even though the room is added already?? weird
                if self.onRoomJoined:
                    self.onRoomJoined(self.room)
                else:
                    print("Warning: no onRoomJoined callback set but room was joined.")
        elif messageType == ESPNOWMessageTypes.INSTRUMENTS:
            print(
                f"Received instruments message: {message.payload[5:].decode('utf-8')}"
            )

    def _on_message(self, event: EspNowReceiveEvent):
        host, msg = event.mac, event.msg
        if msg is None:
            print(f"Received message from {host.hex()} but no payload")
            return
        try:
            self.processMessage(HostAndMessage(host, msg))
        except Exception as e:
            print(f"Error processing message from {host.hex()}: {e}")
            print(f"\tMessage payload: {msg.hex()}")

    async def _send(self, address: bytes, messageType: int, payload: bytes) -> None:
        message = MAGIC + bytes([messageType]) + payload
        await self.__espnow.asend(address, message)

    async def sendMIDIEvent(
        self,
        midiEvent: MIDIEvent,
        midiChannel: int,
    ):
        print(f"sendMIDIEvent: {midiEvent}, midiChannel: {midiChannel}")
        if self.room is None:
            print("Not connected to a room, cannot send MIDI event")
            return
        try:
            payload = ESPNOWBridgePacket.fromMIDIEvent(midiEvent)
            await self._send(
                self.room.hostMAC,  # pyright: ignore[reportOptionalMemberAccess]
                ESPNOWMessageTypes.DATA,
                payload.bytes,
            )
        except Exception as e:
            print(f"Error sending MIDI event: {e}")

    async def sendNoteKeepalive(self, channel: int, note: int) -> None:
        """
        Send a NOTE_KEEPALIVE message to keep a held note alive.

        Per the bridge protocol, keepalive payload is [channel, note] (2 bytes).
        """
        print(f"sendNoteKeepalive: channel={channel}, note={note}")
        if self.room is None:
            print("Not connected to a room, cannot send keepalive")
            return
        try:
            payload = bytes([channel & 0x0F, note & 0x7F])
            await self._send(
                self.room.hostMAC,  # pyright: ignore[reportOptionalMemberAccess]
                ESPNOWMessageTypes.NOTE_KEEPALIVE,
                payload,
            )
        except Exception as e:
            print(f"Error sending note keepalive: {e}")

    async def sendXYZ(self, xyz: tuple[float, float, float]):
        print(f"sendXYZ: {xyz}")

    async def joinRoom(self, onRoomJoined: Callable[[Room], None]):
        self.room = None
        self.onRoomJoined = onRoomJoined

        espnow_service.subscribe(
            handler=self._on_message,
            app=self,
            predicate=lambda e: e.msg.startswith(MAGIC),
        )

        while self.room is None:
            await asyncio.sleep(0)
