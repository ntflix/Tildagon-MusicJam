from typing import Literal
from .MIDIEvent import MIDIEvent


class MusicEvent:
    type: str
    value: int

    def __init__(self, value: int):
        self.type = ""
        self.value = value

    def __str__(self):
        return f"{self.__class__.__name__}({self.type} with value {self.value})"

    def toMIDIEvent(
        self,
        midi_channel: int,
        status: Literal["on", "off"],
        notesOffset: int,
    ) -> MIDIEvent: ...


class Note(MusicEvent):
    type: Literal["note"] = "note"
    value: int = 0

    def __init__(self, value: int):
        self.value = value

    def toMIDIEvent(
        self,
        midi_channel: int,
        status: Literal["on", "off"],
        notesOffset: int,
    ) -> MIDIEvent:
        note = self.value + notesOffset
        if status == "on":
            return MIDIEvent(midi_channel, MIDIEvent.NOTE_ON, note, 127)
        else:
            return MIDIEvent(midi_channel, MIDIEvent.NOTE_OFF, note, 0)


class NullEvent(MusicEvent):
    type: Literal["null"] = "null"
    value: int = 0

    def __init__(self):
        self.value = 0
