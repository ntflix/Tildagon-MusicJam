from .ButtonEvent import ButtonEvent


class Comms:
    def __init__(self):
        pass

    async def send_note(self, note_name: str, button_event_type: ButtonEvent):
        print("send_note", note_name, button_event_type)

    async def send_xyz(self, xyz: tuple[float, float, float]):
        print("send_xyz", xyz)

    async def join_a_room(self):
        print("join_a_room")
