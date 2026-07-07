import struct

from .MIDIEvent import MIDIEvent
from .Magic import MAGIC

TYPE_CHECKING = False

if TYPE_CHECKING:  # pyright: ignore[reportUndefinedVariable]
    from typing import Annotated


class ESPNOWBridgePacket:
    VERSION = 1

    def __init__(
        self,
        magic: Annotated[bytes, "len==4"],
        channel: int,
        status: int,
        data1: int,
        data2: int,
    ):
        """
        Structure:
            0-3:    MAGIC
            4:      version
            5:      event type (status)
            6:      channel
            7:      data1
            8:      data2
        """
        self.magic = magic
        self.version = ESPNOWBridgePacket.VERSION
        self.status = status
        self.channel = channel
        self.data1 = data1
        self.data2 = data2

    @staticmethod
    def fromMIDIEvent(midiEvent: MIDIEvent) -> "ESPNOWBridgePacket":
        channel = midiEvent.midi_channel & 0x0F
        status = midiEvent.event_type & 0xF0
        data1: int
        data2: int

        if status in [MIDIEvent.NOTE_ON, MIDIEvent.NOTE_OFF]:
            note = midiEvent.data_byte_1
            velocity = midiEvent.data_byte_2
            data1 = note
            data2 = velocity

        elif status == MIDIEvent.PITCH_BEND:
            raw14 = ((midiEvent.data_byte_2 & 0x7F) << 7) | (
                midiEvent.data_byte_1 & 0x7F
            )
            bend = raw14 - 8192

            data1 = bend & 0xFF  # LSB
            data2 = (bend >> 8) & 0xFF  # MSB

        elif status == MIDIEvent.CONTROL_CHANGE:
            ccNum = midiEvent.data_byte_1
            ccVal = midiEvent.data_byte_2
            data1 = ccNum
            data2 = ccVal

        else:
            raise ValueError("Unsupported MIDI event for current bridge protocol")

        return ESPNOWBridgePacket(
            magic=MAGIC,
            channel=channel,
            status=status,
            data1=data1,
            data2=data2,
        )

    @property
    def bytes(self) -> bytes:
        return struct.pack(
            "<4sBBBBB",  # little‑endian, a 4‑byte string, then five single‑byte unsigned values
            self.magic,
            self.version,
            self.status,
            self.channel,
            self.data1,
            self.data2,
        )
