from dataclasses import dataclass
from typing import Literal


class MusicEvent:
    type: str
    value: int

    def __init__(self, value: int):
        self.type = ""
        self.value = value


@dataclass
class Note(MusicEvent):
    type: Literal["note_on"] = "note_on"
    value: int = 0

    def __init__(self, value: int):
        self.value = value


@dataclass
class NullEvent(MusicEvent):
    type: Literal["null"] = "null"
    value: int = 0

    def __init__(self):
        self.value = 0


# e: MusicEvent = NoteOn(value=60)
