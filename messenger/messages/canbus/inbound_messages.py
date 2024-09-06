from messages.message import InboundMessage


class TurnoutInputRequestMessage(InboundMessage):
    requested_turnouts = None

    def decode(self):
        self.requested_turnouts = self.data


class ReceiveInputUpdatesMessage(InboundMessage):
    input_address = None
    input_type = None
    module_id = None
    read_value = None

    def decode(self):
        self.module_id = self.data[0] & 0x0F
        self.input_type = self.data[0] >> 4
        self.input_address = self.data[1]
        self.read_value = self.data[2]
