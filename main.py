import threading
import socketio
import eventlet

from railway.io_port import I2CPort
from railway.track import TrackInterruption
from railway.turnout import Turnout

eventlet.monkey_patch()

sio = socketio.Server(cors_allowed_origins='*')  # , logger=True, engineio_logger=True
app = socketio.WSGIApp(sio)

CAN_ENABLED = True

if CAN_ENABLED:
    import can

turnouts = [Turnout(0, 0, 4, I2CPort(0, 2, 0x21, 0), I2CPort(0, 2, 0x21, 1)),
            Turnout(1, 0, 3, I2CPort(0, 2, 0x20, 7), I2CPort(0, 2, 0x20, 6)),
            Turnout(2, 0, 2, I2CPort(0, 2, 0x20, 4), I2CPort(0, 2, 0x20, 5)),
            Turnout(3, 1, 0),
            Turnout(4, 1, 1),
            Turnout(5, 0, 1, I2CPort(0, 2, 0x20, 2), I2CPort(0, 2, 0x20, 3)),
            Turnout(6, 0, 0, I2CPort(0, 2, 0x20, 1), I2CPort(0, 2, 0x20, 0))]

trackInterruptions = [TrackInterruption(3, 2, I2CPort(0, 2, 0x22, 0), turnouts[6], "+"),
                      TrackInterruption(4, 2, I2CPort(0, 2, 0x22, 1), turnouts[6], "-"),
                      TrackInterruption(5, 2, I2CPort(0, 2, 0x22, 2), turnouts[5], "+"),
                      TrackInterruption(6, 1, I2CPort(0, 2, 0x22, 3), turnouts[2], "+"),
                      TrackInterruption(7, 1, I2CPort(0, 2, 0x22, 4)),
                      TrackInterruption(8, 1, I2CPort(0, 2, 0x22, 6)),
                      TrackInterruption(10, 1, I2CPort(0, 2, 0x22, 7), turnouts[2], "-")]  # later on 0x23/pin0 ?


class CanCommunicator:
    bustype = 'socketcan'
    channel = 'can0'
    i2c_value_storage: {int: {int: int}} = {}

    @staticmethod
    def bit_write(byte: int, position: int, value: bool) -> int:
        if value:
            # Set the bit at the specified position
            return byte | (1 << position)
        else:
            # Clear the bit at the specified position
            return byte & ~(1 << position)

    @staticmethod
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

    @staticmethod
    def request_inputs(module_id: int, input_type: int, input_address: int):
        data = [module_id + input_type << 4, input_address]
        CanCommunicator.send_msg(12, data)

    @staticmethod
    def write_i2c_pin(output_reference: I2CPort, output_value: bool):
        module_id = output_reference.module_id
        output_type = output_reference.interface_type
        output_address = output_reference.address

        # check if module_id already exists
        if module_id not in CanCommunicator.i2c_value_storage:
            CanCommunicator.i2c_value_storage[module_id] = {}
        # get current output value
        old_value = CanCommunicator.i2c_value_storage.get(module_id, {}).get(output_address, 0)
        new_value = CanCommunicator.bit_write(old_value,
                                              output_reference.pin_no,
                                              output_value)
        # write new value to storage
        CanCommunicator.i2c_value_storage[module_id].update({output_address: new_value})

        data = [module_id + output_type << 4, output_address, new_value]
        CanCommunicator.send_outputs(data)

    @staticmethod
    def send_outputs(data: [int]):
        CanCommunicator.send_msg(10, data)

    @staticmethod
    def send_turnout_positions():
        turnout_positions = [(s.servo_module, s.servo_number, s.target_pos) for s in turnouts]
        data = [0] * (max(p[0] for p in turnout_positions) + 1)  # get list-size (=count of servo modules)
        for module, s_number, pos in turnout_positions:
            data[module] += (pos << s_number)
        if CanCommunicator.send_msg(1, data):
            for turnout in turnouts:
                # only for testing (change turnout position virtually)
                if turnout.input_reference_minus is None or turnout.input_reference_plus is None or not CAN_ENABLED:
                    turnout.current_pos = turnout.target_pos

    @staticmethod
    def send_msg(msg_id: int, data: [int]) -> bool:
        if not CAN_ENABLED:
            return True
        with can.interface.Bus(channel=CanCommunicator.channel,
                               bustype=CanCommunicator.bustype,
                               bitrate=125000) as can_bus:
            msg = can.Message(arbitration_id=msg_id, data=data, is_extended_id=False)
            try:
                can_bus.send(msg)
                print(f"[CAN] Message sent on {can_bus.channel_info} id: {msg.arbitration_id} msg: {list(msg.data)}")
                return True
            except can.CanError:
                print("[CAN] Message NOT sent")
                return False

    @staticmethod
    def receive_event(msg):  # Inputs from IO-Modules
        print("[CAN] received id:", msg.arbitration_id, "data", list(msg.data))
        if msg.arbitration_id == 11:
            module_id = msg.data[0] & 0x0F
            input_type = msg.data[0] >> 4
            input_address = msg.data[1]
            for turnout in turnouts:
                if turnout.input_reference_plus is None or turnout.input_reference_plus is None:
                    continue
                if turnout.input_reference_minus.compare(module_id, input_type, input_address):
                    input_pin = (msg.data[2] >> turnout.input_reference_minus.pin_no) & 1
                    turnout.set_input_pin_minus(input_pin)
                if turnout.input_reference_plus.compare(module_id, input_type, input_address):
                    input_pin = (msg.data[2] >> turnout.input_reference_plus.pin_no) & 1
                    turnout.set_input_pin_plus(input_pin)

            response_data = {turnout.id: turnout.current_pos for turnout in turnouts}
            print("[ESP] emit: update_switch_positions", response_data)
            sio.emit("update_switch_positions", {'data': response_data})

        elif msg.arbitration_id == 3:  # request: turnout input-references
            for requested_turnout in msg.data:
                for count, input_reference in enumerate([turnouts[requested_turnout].input_reference_plus,
                                                         turnouts[requested_turnout].input_reference_minus]):
                    data = [input_reference.module_id + input_reference.interface_type << 4,
                            input_reference.address,
                            input_reference.pin_no,
                            count + (requested_turnout << 1)]  # first bit represents relevant turnout position
                    CanCommunicator.send_msg(2, data)


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
        CanCommunicator.send_turnout_positions()
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
        # print("setze Abschnitt", track.global_number, ".", track.section, "auf", edge)
        CanCommunicator.write_i2c_pin(track.output_reference, edge)

    @staticmethod
    def updater():
        Esp32Communicator.send_turnout_positions()
        timer = threading.Timer(0.2, Esp32Communicator.updater)
        timer.start()

    @staticmethod
    def send_turnout_positions():
        CanCommunicator.request_inputs(0, 2, 0x20)
        CanCommunicator.request_inputs(0, 2, 0x21)
        data = {turnout.id: turnout.current_pos for turnout in turnouts}
        sio.emit("update_switch_positions", {'data': data})


if __name__ == '__main__':
    # initialize can Listener
    if CAN_ENABLED:
        bus = can.interface.Bus(channel=CanCommunicator.channel,
                                bustype=CanCommunicator.bustype,
                                bitrate=125000)
        notifier = can.Notifier(bus, [CanCommunicator.receive_event])

    # socketio to ESP32
    sio.register_namespace(Esp32Communicator())
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
