from .. import messages
from .handler import MessageHandler

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..messenger import Messenger
    from railway.turnout import Turnout
    import socketio.server


class TurnoutInputRequestHandler(MessageHandler):
    def __init__(self, messenger: "Messenger", turnouts: list["Turnout"]):
        super().__init__(messenger)
        self.turnouts = turnouts

    def handle(self, data: list[int]):
        message = messages.TurnoutInputRequestMessage(data)
        message.decode()
        for requested_turnout in message.requested_turnouts:
            for count, input_reference in enumerate([self.turnouts[requested_turnout].input_reference_plus,
                                                     self.turnouts[requested_turnout].input_reference_minus]):
                response_msg = messages.DistributeTurnoutIOReference(requested_turnout, input_reference, count)
                self.messenger.publish(response_msg)


class ReceiveInputUpdatesHandler(MessageHandler):
    def __init__(self, messenger: "Messenger", turnouts: list["Turnout"], sio: "socketio.Server"):
        super().__init__(messenger)
        self.turnouts = turnouts
        self.sio = sio

    def handle(self, data: list[int]):
        message = messages.ReceiveInputUpdatesMessage(data)
        message.decode()

        for turnout in self.turnouts:
            if turnout.input_reference_plus is None or turnout.input_reference_plus is None:
                continue

            if turnout.input_reference_minus.compare(
                    message.module_id,
                    message.input_type,
                    message.input_address):
                input_pin = (message.read_value >> turnout.input_reference_minus.pin_no) & 1
                turnout.set_input_pin_minus(input_pin)

            if turnout.input_reference_plus.compare(
                    message.module_id,
                    message.input_type,
                    message.input_address):
                input_pin = (message.read_value >> turnout.input_reference_plus.pin_no) & 1
                turnout.set_input_pin_plus(input_pin)

        # ToDo: create method for response in EspCommunicator
        response_data = {turnout.id: turnout.current_pos for turnout in self.turnouts}
        print("[ESP] emit: update_switch_positions", response_data)
        self.sio.emit("update_switch_positions", {'data': response_data})
