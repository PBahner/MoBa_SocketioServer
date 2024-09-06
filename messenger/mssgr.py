from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .messages.message import OutboundMessage
    from .handlers.handler import MessageHandler


class Messenger:
    _message_handlers = {}

    def __init__(self):
        pass

    def publish(self, message: "OutboundMessage") -> bool:
        # must be defined in subclass
        raise NotImplemented

    def subscribe(self, msg_id: Union[int, str], handler: "MessageHandler"):
        self._message_handlers[msg_id] = handler
        print("[MSG] Handler", type(handler).__name__, "registered for msg_id", msg_id)
