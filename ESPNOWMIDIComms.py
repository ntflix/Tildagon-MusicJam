from .ESPNOWMessageType import ESPNOWMessageTypes
from .Room import Room
from .Comms import Comms
from .MIDIEvent import MIDIEvent
from .ESPNOWBridgePacket import ESPNOWBridgePacket


class ESPNOWMIDIComms:
    def __init__(self):
        self.comms = Comms()
        self.local_mac = self.comms.mac
        self.bridge_mac = None
        self.connected = False

    def get_local_mac(self) -> bytes:
        return self.comms.mac

    def set_bridge_mac(self, mac: bytes) -> None:
        """Set the bridge MAC address and ensure it exists as a peer."""
        if len(mac) != 6:
            raise ValueError("MAC address must be 6 bytes")

        self.bridge_mac = mac

        try:
            self.comms.e.add_peer(mac)
        except OSError as e:
            if len(e.args) >= 2 and e.args[1] == "ESP_ERR_ESPNOW_EXIST":
                pass
            else:
                raise

        self.connected = True

    async def join_a_room(self) -> Room:
        room = await self.comms.join_a_room()
        self.set_bridge_mac(room.host_mac)
        return room

    async def send_midi_event(self, midi_event: MIDIEvent) -> bool:
        if not self.bridge_mac:
            print("ERROR: Bridge MAC not set")
            return False

        try:
            payload = ESPNOWBridgePacket.from_midi_event(midi_event)
            await self.comms.send_async(
                self.bridge_mac,
                ESPNOWMessageTypes.DATA,
                payload,
            )
            return True
        except Exception as e:
            print("ERROR sending MIDI event:", e)
            return False

    def reset(self) -> None:
        self.comms.reset()
        self.local_mac = self.get_local_mac()
        self.bridge_mac = None
        self.connected = False
