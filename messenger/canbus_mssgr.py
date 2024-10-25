from .mssgr import Messenger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .messages.message import OutboundMessage
    import can

try:
    import can
    CAN_ENABLED = True
except ModuleNotFoundError:
    CAN_ENABLED = False


class CanBus(Messenger):
    def __init__(self,
                 channel: str = 'can0',
                 bustype: str = 'socketcan',
                 bitrate: int = 125000):
        super().__init__()

        self.channel = channel
        self.bustype = bustype
        self.bitrate = bitrate

        try:
            # initialize can Listener
            bus = can.interface.Bus(channel=self.channel,
                                    bustype=self.bustype,
                                    bitrate=self.bitrate)
            notifier = can.Notifier(bus, [self.__receive_event])
        except (OSError, NameError):
            global CAN_ENABLED
            CAN_ENABLED = False
            print("[CAN] bus not available")

    def publish(self, msg: "OutboundMessage") -> bool:
        try:
            with can.interface.Bus(channel=self.channel,
                                   bustype=self.bustype,
                                   bitrate=125000) as can_bus:
                bus_msg = can.Message(arbitration_id=msg.msg_id, data=msg.encode(), is_extended_id=False)
                try:
                    can_bus.send(bus_msg)
                    print(f"[CAN] Message sent on {can_bus.channel_info} id: {bus_msg.arbitration_id} msg: {list(bus_msg.data)}")
                    return True
                except can.CanError:
                    print("[CAN] Message NOT sent")
                    return False
        except (OSError, NameError):
            print("[CAN] bus not available")
        except can.CanError:
            print("[CAN] Can't publish", msg.msg_id, msg.encode())
            return True

    def __receive_event(self, msg: "can.Message"):
        print("[CAN] received id:", msg.arbitration_id, "data", list(msg.data))
        msg_handler = self._message_handlers.get(msg.arbitration_id)
        if msg_handler:
            msg_handler.handle(msg.data)
