from typing import Literal


class MusicEvent:
    type: str
    value: int

    def __init__(self, value: int):
        self.type = ""
        self.value = value

    def __str__(self):
        return f"{self.__class__.__name__}({self.type} with value {self.value})"


class Note(MusicEvent):
    type: Literal["note"] = "note"
    value: int = 0

    def __init__(self, value: int):
        self.value = value


class NullEvent(MusicEvent):
    type: Literal["null"] = "null"
    value: int = 0

    def __init__(self):
        self.value = 0


# e: MusicEvent = NoteOn(value=60)
