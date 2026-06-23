import struct


class ESPNOWBridgePacket:
    MAGIC = ord("A")
    VERSION = 1

    NOTE_OFF = 0
    NOTE_ON = 1
    PITCH_BEND = 2

    @staticmethod
    def from_midi_event(evt) -> bytes:
        status = evt.event_type & 0xF0
        channel = evt.midi_channel & 0x0F

        if status == 0x90 and evt.data_byte_2 > 0:
            pkt_type = ESPNOWBridgePacket.NOTE_ON
            note = evt.data_byte_1
            velocity = evt.data_byte_2
            bend = 0

        elif status == 0x80 or (status == 0x90 and evt.data_byte_2 == 0):
            pkt_type = ESPNOWBridgePacket.NOTE_OFF
            note = evt.data_byte_1
            velocity = evt.data_byte_2
            bend = 0

        elif status == 0xE0:
            raw14 = ((evt.data_byte_2 & 0x7F) << 7) | (evt.data_byte_1 & 0x7F)
            bend = raw14 - 8192
            pkt_type = ESPNOWBridgePacket.PITCH_BEND
            note = 0
            velocity = 0

        else:
            raise ValueError("Unsupported MIDI event for current bridge protocol")

        return struct.pack(
            "<BBBBBBhBB",
            ESPNOWBridgePacket.MAGIC,
            ESPNOWBridgePacket.VERSION,
            pkt_type,
            channel,
            note,
            velocity,
            bend,
            0,
            0,
        )
