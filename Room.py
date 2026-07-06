from .MACAddress import MACAddress


class Room:
    id: int
    hostMAC: MACAddress

    def __str__(self) -> str:
        return f"Room(id={self.id}, hostMAC={self.hostMAC.hex()})"

    def __init__(self, id: int, hostMAC: MACAddress):
        self.id = id
        self.hostMAC = hostMAC
