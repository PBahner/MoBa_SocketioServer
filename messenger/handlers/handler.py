from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..messenger import Messenger


class MessageHandler:
    def __init__(self, messenger: "Messenger"):
        self.messenger = messenger

    def handle(self, data: any):
        # defined in subclass
        raise NotImplemented
