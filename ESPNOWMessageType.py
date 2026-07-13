class ESPNOWMessageTypes:
    JOIN = 0x01
    LEAVE = 0x02
    DATA = 0x03
    ADVERTISEMENT = 0x04
    JOINEDACK = 0x05
    INSTRUMENTS = 0x06
    NOTE_KEEPALIVE = 0x07

    @staticmethod
    def fromValue(value: int) -> int:
        if value == ESPNOWMessageTypes.JOIN:
            return ESPNOWMessageTypes.JOIN
        elif value == ESPNOWMessageTypes.LEAVE:
            return ESPNOWMessageTypes.LEAVE
        elif value == ESPNOWMessageTypes.DATA:
            return ESPNOWMessageTypes.DATA
        elif value == ESPNOWMessageTypes.ADVERTISEMENT:
            return ESPNOWMessageTypes.ADVERTISEMENT
        elif value == ESPNOWMessageTypes.JOINEDACK:
            return ESPNOWMessageTypes.JOINEDACK
        elif value == ESPNOWMessageTypes.INSTRUMENTS:
            return ESPNOWMessageTypes.INSTRUMENTS
        elif value == ESPNOWMessageTypes.NOTE_KEEPALIVE:
            return ESPNOWMessageTypes.NOTE_KEEPALIVE
        else:
            raise ValueError(f"Invalid message type: {value}")
