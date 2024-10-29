import messenger.canbus_mssgr
from .. import messages
from .handler import MessageHandler
from main import Esp32Communicator

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..mssgr import Messenger
    from railway.turnout import Turnout
    from railway.track import TrackInterruption
    import socketio.server
    from messenger.canbus_mssgr import CanBus


class TurnoutChangeRequestHandler(MessageHandler):
    def __init__(self, messenger: "Messenger", can_messenger: "CanBus", turnouts: list["Turnout"]):
        super().__init__(messenger)
        self.can_messenger = can_messenger
        self.turnouts = turnouts

    def handle(self, data):
        message = messages.socketio.TurnoutChangeRequestMessage(data)
        message.decode()

        for turnout in message.turnouts:
            self.turnouts[turnout].change_target_pos()
            print("Weiche " + str(turnout) + " stellen")

        msg = messages.canbus.DistributeTargetTurnoutPositionsMessage(self.turnouts)
        self.can_messenger.publish(msg)
        # only for testing (change turnout position virtually)
        for turnout in self.turnouts:
            if (turnout.input_reference_minus is None or turnout.input_reference_plus is None
                    or not messenger.canbus_mssgr.CAN_ENABLED):
                turnout.current_pos = turnout.target_pos

        Esp32Communicator.send_turnout_positions()


class TrackInterruptionChangeHandler(MessageHandler):
    edge = None

    def __init__(self, messenger: "Messenger", can_messenger: "CanBus", turnouts: list["Turnout"], track_interruptions: list["TrackInterruption"]):
        super().__init__(messenger)
        self.can_messenger = can_messenger
        self.turnouts = turnouts
        self.track_interruptions = track_interruptions

    def handle(self, data):
        for turnout in data["data"]:  # ToDo: use msg.decode()
            if turnout in [0, 1] and self.turnouts[0].current_pos == self.turnouts[1].current_pos:
                track_number = 7+turnout  # Workaround: track number 7 or 8
                track_section = 1
                for index, track in enumerate(self.track_interruptions):
                    if track.global_number == track_number and track.section == track_section:
                        self.__trigger_track(self.track_interruptions[index], self.edge)
            for track in self.track_interruptions:
                if track.required_turnout is None or track.required_turnout_pos is None:
                    continue
                match_turnout_id = track.required_turnout.id == turnout
                match_turnout_pos = track.required_turnout_pos == self.turnouts[turnout].get_current_pos_friendly()
                if match_turnout_id and match_turnout_pos:
                    self.__trigger_track(track, self.edge)

    def __trigger_track(self, track: "TrackInterruption", edge: bool):
        if edge:
            track.required_turnout.lock()
        else:
            track.required_turnout.unlock()
        track.state = edge
        msg = messages.canbus.WriteI2CPortMessage(track.output_reference, edge)
        self.can_messenger.publish(msg)


class TrackInterruptionOnRequestHandler(TrackInterruptionChangeHandler):
    edge = True


class TrackInterruptionOffRequestHandler(TrackInterruptionChangeHandler):
    edge = False
