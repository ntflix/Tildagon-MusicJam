class MIDIEvent:
    NOTE_OFF = 0x80
    NOTE_ON = 0x90
    POLY_AFTERTOUCH = 0xA0
    CONTROL_CHANGE = 0xB0
    PROGRAM_CHANGE = 0xC0
    CHANNEL_AFTERTOUCH = 0xD0
    PITCH_BEND = 0xE0
    SYSEX = 0xF0

    def __init__(
        self,
        midi_channel: int,
        event_type: int,
        data_byte_1: int = 0,
        data_byte_2: int = 0,
        sysex_data: bytes = b"",
    ):
        if not (0 <= midi_channel <= 15):
            raise ValueError("MIDI channel must be 0-15")
        if not (0 <= data_byte_1 <= 127):
            raise ValueError("Data byte 1 must be 0-127")
        if not (0 <= data_byte_2 <= 127):
            raise ValueError("Data byte 2 must be 0-127")
        if len(sysex_data) > 246:
            raise ValueError("SysEx data must be 0-246 bytes")

        self.midi_channel = midi_channel & 0x0F
        self.event_type = event_type
        self.data_byte_1 = data_byte_1
        self.data_byte_2 = data_byte_2
        self.sysex_data = sysex_data
