import threading
import socketio

from messenger.canbus_mssgr import CanBus
from messenger.socketio_mssgr import SocketIO
from messenger import handlers
from railway import Turnout, TrackInterruption
from railway import I2CPin
from messenger.utils import Esp32Communicator

import webserver

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


if __name__ == '__main__':
    can_messenger = CanBus()
    sio_messenger = SocketIO(turnouts)

    can_messenger.subscribe(3, handlers.TurnoutInputRequestHandler(can_messenger, turnouts))
    can_messenger.subscribe(11, handlers.ReceiveInputUpdatesHandler(can_messenger, turnouts, sio_messenger))
    sio_messenger.subscribe(
        'change_turnouts',
        handlers.TurnoutChangeRequestHandler(sio_messenger, can_messenger, turnouts)
    )
    sio_messenger.subscribe(
        'track_interruptions_on',
        handlers.TrackInterruptionOnRequestHandler(sio_messenger, can_messenger, turnouts, trackInterruptions)
    )
    sio_messenger.subscribe(
        'track_interruptions_off',
        handlers.TrackInterruptionOffRequestHandler(sio_messenger, can_messenger, turnouts, trackInterruptions)
    )
    Esp32Communicator.can_messenger = can_messenger
    Esp32Communicator.sio_messenger = sio_messenger
    Esp32Communicator.turnouts = turnouts
    Esp32Communicator.track_interruptions = trackInterruptions

    # Testing
    # msg = can.Message(arbitration_id=11, data=[32, 0x20, 1])
    # can_messenger._CanBus__receive_event(msg)
    # msg = can.Message(arbitration_id=11, data=[32, 0x20, 4])
    # can_messenger._CanBus__receive_event(msg)

    # initialize webserver thread
    local_webserver = threading.Thread(target=webserver.start_webserver, daemon=False)
    local_webserver.start()

    sio_messenger.start()
