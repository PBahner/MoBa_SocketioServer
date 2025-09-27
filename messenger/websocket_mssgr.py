import asyncio
import websockets
import json
from typing import List, TYPE_CHECKING

from messenger import messages
from messenger.mssgr import Messenger
from messenger.utils import Esp32Communicator

if TYPE_CHECKING:
    from .messages.message import OutboundMessage
    from handlers import MessageHandler
    from railway import Turnout


class WebSocketMessenger(Messenger):
    def __init__(self,
                 turnouts: List["Turnout"],
                 port: int = 5000,
                 ip: str = '0.0.0.0'):
        super().__init__()

        self.turnouts = turnouts
        self.port = port
        self.ip = ip

        self.__clients: set[websockets.WebSocketServerProtocol] = set()

    async def __broadcast(self, message: str) -> None:
        """Send a message to all connected clients."""
        if not self.__clients:
            return
        # await asyncio.gather(*[client.send(message) for client in self.__clients], return_exceptions=True)
        for client in list(self.__clients):
            try:
                await asyncio.wait_for(client.send(message), timeout=0.5)
            except Exception:
                self.__clients.remove(client)

    async def __handler(self, websocket: websockets.WebSocketServerProtocol) -> None:
        self.__clients.add(websocket)

        print('[WebSocket] connect')

        # Send initial turnout positions
        msg = messages.socketio.DistributeInitialTurnoutPositionsMessage(self.turnouts)
        self.publish(msg)
        print("[WebSocket] emit: init_switch_positions", msg)
        Esp32Communicator.updater()

        try:
            async for message in websocket:
                msg = json.loads(message)
                msg_id = msg.get('msg_id')
                msg_data = msg.get('data')
                print("[WebSocket] received event:", msg_id, "data", list(msg_data))
                msg_handler = self._message_handlers.get(msg_id)
                if msg_handler:
                    msg_handler.handle(msg_data)
        except websockets.ConnectionClosed:
            print('[WebSocket] disconnect')
        finally:
            self.__clients.remove(websocket)

    async def __run(self) -> None:
        async with websockets.serve(self.__handler, self.ip, self.port):
            print(f"[WebSocket] Server started on {self.ip}:{self.port}")
            await asyncio.Future()

    def start(self) -> None:
        asyncio.run(self.__run())

    def publish(self, message: "OutboundMessage") -> bool:
        try:
            if self.__clients:
                loop = asyncio.get_event_loop()
                data = json.dumps({'msg_id': message.msg_id, 'data': message.encode()})
                loop.call_soon_threadsafe(asyncio.create_task, self.__broadcast(data))
                print(f"[WebSocket] Message published with msg_id: {message.msg_id} and data: {message.encode()}")
            else:
                pass
                # print("[WebSocket] No connected clients to publish the message.")
            return True
        except Exception as e:
            print(f"[WebSocket] Failed to publish message: {str(e)}")
            return False
