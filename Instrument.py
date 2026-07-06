class Instrument:
    name: str
    midiChannel: int

    def __init__(self, name: str, midiChannel: int):
        self.name = name
        self.midiChannel = midiChannel
