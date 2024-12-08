from . import messages
from .utils import Esp32Communicator
from .mssgr import Messenger
import socketio
import eventlet

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .messages.message import OutboundMessage
    from handlers import MessageHandler
    from railway import Turnout

eventlet.monkey_patch()


class SocketIO(Messenger):
    def __init__(self,
                 turnouts: List["Turnout"],
                 port: int = 5000,
                 ip: str = '0.0.0.0'):
        super().__init__()

        self.turnouts = turnouts
        self.port = port
        self.ip = ip
        self.sio = socketio.Server(cors_allowed_origins='*')  # , logger=True, engineio_logger=True
        self.app = socketio.WSGIApp(self.sio)

        @self.sio.event
        def connect(sid, environ, auth):
            print('[ESP] connect ', sid)
            data = {turnout.id: turnout.current_pos for turnout in self.turnouts}
            self.sio.emit("init_switch_positions", {'data': data})
            msg = messages.socketio.DistributeInitialTurnoutPositionsMessage(self.turnouts)
            self.publish(msg)
            print("[ESP] emit: init_switch_positions", data)
            Esp32Communicator.updater()

        @self.sio.event
        def disconnect(self2, sid):
            print('[ESP] disconnect ', sid)

    def start(self):
        # socketio to ESP32
        eventlet.wsgi.server(eventlet.listen((self.ip, self.port)), self.app)

    def publish(self, message: "OutboundMessage") -> bool:
        try:
            self.sio.emit(message.msg_id, {'data': message.encode()})
            print(f"[SocketIO] Message published with msg_id: {message.msg_id} and data: {message.encode()}")
            return True
        except Exception as e:
            print(f"[SocketIO] Failed to publish message: {str(e)}")
            return False

    def subscribe(self, msg_id: str, handler: "MessageHandler"):
        super().subscribe(msg_id, handler)

        @self.sio.on(msg_id)
        def on_message(sid, msg):
            print("[SocketIO] received event:", msg_id, "data", list(msg['data']))
            msg_handler = self._message_handlers.get(msg_id)
            if msg_handler:
                msg_handler.handle(msg)
