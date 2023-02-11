import socketio
import eventlet
import time

sio = socketio.Server(cors_allowed_origins='*') #, logger=True, engineio_logger=True
app = socketio.WSGIApp(sio)

CAN_ENABLED = False

if CAN_ENABLED:
    import can


class Switches:
    __pos = {
        "+": False,
        "-": True,
        "": 2,
    }

    def __init__(self, switch_id):
        self.current_pos = self.__pos["+"]
        self.target_pos = self.__pos["+"]
        self.id = switch_id

    def change_switch_state(self):
        self.target_pos = not self.current_pos


switches = [Switches(0), Switches(1), Switches(2), Switches(3), Switches(4), Switches(5), Switches(6)]


class CanCommunicator:
    @staticmethod
    def bools_to_bytes(list):
        output_byte = [0]
        byte_number = 0
        for i, x in enumerate(list):
            exponent = ((i+1) % 8)-1
            output_byte[byte_number] += int(x * 2**exponent)
            if (i+1) % 8 == 0:
                output_byte.append(0)
                byte_number += 1
        return output_byte

    @staticmethod
    def send_switch_states():
        data = [s.target_pos for s in switches]
        print(data)
        data = CanCommunicator.bools_to_bytes(data)
        print("data", data)
        if CanCommunicator.send_msg(1, data):
            for switch in switches:
                # only for testing
                switch.current_pos = switch.target_pos

    @staticmethod
    def send_msg(id, data):
        if not CAN_ENABLED:
            return True
        bustype = 'socketcan'
        channel = 'can0'
        with can.interface.Bus(channel=channel, bustype=bustype, bitrate=125000) as bus:
            msg = can.Message(arbitration_id=id, data=data, is_extended_id=False)
            try:
                bus.send(msg)
                print(f"Message sent on {bus.channel_info}")
                return True
            except can.CanError:
                print("Message NOT sent")
                return False


class Esp32Communicator(socketio.Namespace):
    def on_connect(self, sid, environ, auth):
        print('connect ', sid)
        data = {switch.id: switch.current_pos for switch in switches}
        sio.emit("init_switch_positions", {'data': data})

    def on_disconnect(self, sid):
        print('disconnect ', sid)

    def on_change_switches(self, sid, data):
        response_data = {}
        for switch in data["data"]:
            switches[switch].change_switch_state()
            print("Weiche " + str(switch) + " stellen")
        CanCommunicator.send_switch_states()
        for switch in data["data"]:
            # response data only for testing
            response_data[switches[switch].id] = switches[switch].target_pos
        print("response: ", response_data)
        sio.emit("update_switch_positions", {'data': response_data})
        # sio.emit("state_change_request", {'data': data})


sio.register_namespace(Esp32Communicator())

if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
