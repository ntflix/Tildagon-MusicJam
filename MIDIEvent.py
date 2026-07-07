class MIDIEvent:
    NOTE_OFF = 0x80
    NOTE_ON = 0x90
    POLY_AFTERTOUCH = 0xA0
    CONTROL_CHANGE = 0xB0
    PROGRAM_CHANGE = 0xC0
    CHANNEL_AFTERTOUCH = 0xD0
    PITCH_BEND = 0xE0

    def __init__(
        self,
        midi_channel: int,
        event_type: int,
        data_byte_1: int = 0,
        data_byte_2: int = 0,
    ):
        if not (0 <= midi_channel <= 15):
            raise ValueError(f"MIDI channel must be 0-15. Actual value: {midi_channel}")
        # if not (0 <= data_byte_1 <= 127):
        #     raise ValueError(f"Data byte 1 must be 0-127. Actual value: {data_byte_1}")
        # if not (0 <= data_byte_2 <= 127):
        #     raise ValueError(f"Data byte 2 must be 0-127. Actual value: {data_byte_2}")

        self.midi_channel = midi_channel & 0x0F
        self.event_type = event_type
        self.data_byte_1 = data_byte_1
        self.data_byte_2 = data_byte_2

    def __str__(self) -> str:
        return (
            f"MIDIEvent(midi_channel={self.midi_channel}, "
            f"\tevent_type={hex(self.event_type)}, "
            f"\tdata_byte_1={self.data_byte_1}, "
            f"\tdata_byte_2={self.data_byte_2})"
        )
