class Instrument:
    name: str
    midiChannel: int
    shouldPitchBend: bool
    shouldModulate: bool
    hint: str | None

    def __init__(
        self,
        name: str,
        midiChannel: int,
        shouldPitchBend: bool = True,
        shouldModulate: bool = True,
        hint: str | None = None,
    ):
        self.name = name
        self.midiChannel = midiChannel
        self.shouldPitchBend = shouldPitchBend
        self.shouldModulate = shouldModulate
        self.hint = hint
