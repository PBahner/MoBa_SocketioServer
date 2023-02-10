import socketio
import eventlet
import time

sio = socketio.Server(cors_allowed_origins='*') #, logger=True, engineio_logger=True
app = socketio.WSGIApp(sio)

CAN_ENABLED = True

if CAN_ENABLED:
    import can


class Switches:
    def __init__(self, id):
        self.current_pos = False
        self.target_pos = False
        self.id = id

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
        data.insert(5, False)
        data.insert(5, False)
        data.insert(5, False)
        print(data)
        data = CanCommunicator.bools_to_bytes(data)
        print("data", data)
        if CanCommunicator.send_msg(1, data):
            for switch in switches:
                switch.current_pos = switch.target_pos

    @staticmethod
    def send_msg(id, data):
        if not CAN_ENABLED:
            return
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

    def on_disconnect(self, sid):
        print('disconnect ', sid)

    def on_change_switches(self, sid, data):
        for switch in data["data"]:
            switches[switch].change_switch_state()
            print("Weiche " + str(switch) + " stellen")
        CanCommunicator.send_switch_states()
        # sio.emit("state_change_request", {'data': data})


sio.register_namespace(Esp32Communicator())

if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
