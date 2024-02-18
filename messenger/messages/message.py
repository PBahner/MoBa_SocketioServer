class Message:
    def __init__(self):
        pass


class OutboundMessage(Message):
    def __init__(self, msg_id: any):
        super().__init__()
        self.msg_id = msg_id

    def encode(self, *args):
        # defined in subclass
        raise NotImplemented


class InboundMessage(Message):
    def __init__(self, data: any):
        super().__init__()
        self.data = data

    def decode(self):
        # defined in subclass
        raise NotImplemented

