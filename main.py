import threading
import socketio
import eventlet

from messenger.canbus import CanBus, CAN_ENABLED
from messenger import messages, handlers
from railway import Turnout, TrackInterruption
from railway import I2CPin, IOPort

eventlet.monkey_patch()

sio = socketio.Server(cors_allowed_origins='*')  # , logger=True, engineio_logger=True
app = socketio.WSGIApp(sio)


turnouts = [Turnout(0, 0, 4, I2CPin(0, 2, 0x21, 0), I2CPin(0, 2, 0x21, 1)),
            Turnout(1, 0, 3, I2CPin(0, 2, 0x20, 6), I2CPin(0, 2, 0x20, 7)),
            Turnout(2, 0, 2, I2CPin(0, 2, 0x20, 4), I2CPin(0, 2, 0x20, 5)),
            Turnout(3, 1, 0),
            Turnout(4, 1, 1),
            Turnout(5, 0, 1, I2CPin(0, 2, 0x20, 2), I2CPin(0, 2, 0x20, 3)),
            Turnout(6, 0, 0, I2CPin(0, 2, 0x20, 1), I2CPin(0, 2, 0x20, 0))]

trackInterruptions = [TrackInterruption(3, 2, I2CPin(0, 2, 0x22, 0), turnouts[6], "+"),
                      TrackInterruption(4, 2, I2CPin(0, 2, 0x22, 1), turnouts[6], "-"),
                      TrackInterruption(5, 2, I2CPin(0, 2, 0x22, 2), turnouts[5], "+"),
                      TrackInterruption(6, 1, I2CPin(0, 2, 0x22, 3), turnouts[2], "+"),
                      TrackInterruption(7, 1, I2CPin(0, 2, 0x22, 4)),
                      TrackInterruption(8, 1, I2CPin(0, 2, 0x22, 6)),
                      TrackInterruption(10, 1, I2CPin(0, 2, 0x22, 7), turnouts[2], "-")]  # later on 0x23/pin0 ?


class Esp32Communicator(socketio.Namespace):
    def on_connect(self, sid, environ, auth):
        print('[ESP] connect ', sid)
        data = {turnout.id: turnout.current_pos for turnout in turnouts}
        sio.emit("init_switch_positions", {'data': data})
        print("[ESP] emit: init_switch_positions", data)
        Esp32Communicator.updater()

    def on_disconnect(self, sid):
        print('[ESP] disconnect ', sid)

    def on_change_turnouts(self, sid, data: [int]):
        for turnout in data["data"]:
            turnouts[turnout].change_target_pos()
            print("Weiche " + str(turnout) + " stellen")

        msg = messages.DistributeTargetTurnoutPositionsMessage(turnouts)
        if can_messenger.publish(msg):
            # only for testing (change turnout position virtually)
            for turnout in turnouts:
                if turnout.input_reference_minus is None or turnout.input_reference_plus is None or not CAN_ENABLED:
                    turnout.current_pos = turnout.target_pos

        Esp32Communicator.send_turnout_positions()

    def on_track_interruptions_on(self, sid, data: [int]):
        self.__on_track_interruptions_change(data, True)

    def on_track_interruptions_off(self, sid, data: [int]):
        self.__on_track_interruptions_change(data, False)

    def __on_track_interruptions_change(self, data: [int], edge: bool):
        for turnout in data["data"]:
            if turnout in [0, 1] and turnouts[0].current_pos != turnouts[1].current_pos:
                track_number = 7+turnout  # Workaround: track number 7 or 8
                track_section = 1
                for index, track in enumerate(trackInterruptions):
                    if track.global_number == track_number and track.section == track_section:
                        self.__trigger_track(trackInterruptions[index], edge)
            for track in trackInterruptions:
                if track.required_turnout is None or track.required_turnout_pos is None:
                    continue
                match_turnout_id = track.required_turnout.id == turnout
                match_turnout_pos = track.required_turnout_pos == turnouts[turnout].get_current_pos_friendly()
                if match_turnout_id and match_turnout_pos:
                    self.__trigger_track(track, edge)

    def __trigger_track(self, track: TrackInterruption, edge: bool):
        msg = messages.WriteI2CPortMessage(track.output_reference, edge)
        can_messenger.publish(msg)

    @staticmethod
    def updater():
        Esp32Communicator.send_turnout_positions()
        timer = threading.Timer(0.2, Esp32Communicator.updater)
        timer.start()

    @staticmethod
    def send_turnout_positions():
        # ToDo: automatically request required inputs (depending on necessity)
        msg = messages.RequestInputsMessage(IOPort(0, 2, 0x20))
        can_messenger.publish(msg)
        msg = messages.RequestInputsMessage(IOPort(0, 2, 0x21))
        can_messenger.publish(msg)
        data = {turnout.id: turnout.current_pos for turnout in turnouts}
        sio.emit("update_switch_positions", {'data': data})


if __name__ == '__main__':
    can_messenger = CanBus()
    can_messenger.subscribe(3, handlers.TurnoutInputRequestHandler(can_messenger, turnouts))
    can_messenger.subscribe(11, handlers.ReceiveInputUpdatesHandler(can_messenger, turnouts, sio))

    # Testing
    # msg = can.Message(arbitration_id=11, data=[32, 0x20, 1])
    # can_messenger._CanBus__receive_event(msg)
    # msg = can.Message(arbitration_id=11, data=[32, 0x20, 4])
    # can_messenger._CanBus__receive_event(msg)

    # socketio to ESP32
    sio.register_namespace(Esp32Communicator())
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
