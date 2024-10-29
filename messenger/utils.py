import threading
import messages

from typing import TYPE_CHECKING, List
from railway import IOPort

if TYPE_CHECKING:
    import mssgr
    from railway import Turnout
    from railway.track import TrackInterruption


def bit_write(byte: int, position: int, value: bool) -> int:
    if value:
        # Set the bit at the specified position
        return byte | (1 << position)
    else:
        # Clear the bit at the specified position
        return byte & ~(1 << position)


def bools_to_bytes(data_list: [int]) -> [int]:
    data_list = [b == 1 for b in data_list]
    output_byte = [0]
    byte_number = 0
    for i, x in enumerate(data_list):
        exponent = ((i+1) % 8)-1
        output_byte[byte_number] += int(x * 2**exponent)
        if (i+1) % 8 == 0:
            output_byte.append(0)
            byte_number += 1
    return output_byte


class Esp32Communicator:
    can_messenger: "mssgr.Messenger" = None
    sio_messenger: "mssgr.Messenger" = None
    turnouts: List["Turnout"] = None
    track_interruptions: List["TrackInterruption"] = None

    @staticmethod
    def updater():
        Esp32Communicator.send_turnout_positions()
        Esp32Communicator.send_track_interruptions()
        timer = threading.Timer(0.05, Esp32Communicator.updater)
        timer.start()

    @staticmethod
    def send_turnout_positions():
        # ToDo: automatically request required inputs (depending on necessity)
        msg = messages.canbus.RequestInputsMessage(IOPort(0, 2, 0x20))
        Esp32Communicator.can_messenger.publish(msg)
        msg = messages.canbus.RequestInputsMessage(IOPort(0, 2, 0x21))
        Esp32Communicator.can_messenger.publish(msg)
        msg = messages.socketio.DistributeCurrentTurnoutPositionsMessage(Esp32Communicator.turnouts)
        Esp32Communicator.sio_messenger.publish(msg)

    @staticmethod
    def send_track_interruptions():
        msg = messages.socketio.DistributeCurrentTrackInterruptionsMessage(Esp32Communicator.track_interruptions)
        Esp32Communicator.sio_messenger.publish(msg)
