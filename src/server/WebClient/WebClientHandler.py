import asyncio
import json
import websockets
from websockets import WebSocketClientProtocol

from Log.LogInterface import LogInterface


class WebClient:
    def __init__(self, websocket: WebSocketClientProtocol, ip: str, hostname: str):
        self.websocket = websocket
        self.ip = ip
        self.hostname = hostname

    def __repr__(self):
        return f"Client {self.hostname} ({self.ip})"

    def __str__(self):
        return f"Client {self.hostname} ({self.ip})"


class WebClientHandler:
    def __init__(self, api_key: str, logger: LogInterface):
        self.logger = logger
        self.clients = []
        self.api_key = api_key

    async def add_client(self, websocket: WebSocketClientProtocol):
        try:
            message = await websocket.recv()
            message = json.loads(message)
            if message.get("message") == "connect":
                client_hostname = message["hostname"]
                client_ip = message["ip"]
                client_api_key = message["api_key"]
                if client_api_key == self.api_key:
                    new_client = WebClient(websocket, client_ip, client_hostname)
                    self.clients.append(new_client)
                    self.logger.info(f"Client {client_hostname} connected.")
                    await self.keep_client_alive(new_client)
                else:
                    self.logger.error(
                        f"Client {client_hostname} failed to connect: Invalid API key."
                    )
        except Exception as e:
            self.logger.error(f"Error adding client: {e}")

    async def keep_client_alive(self, client: WebClient):
        try:
            while True:
                pong_waiter = await client.websocket.ping()
                await asyncio.wait_for(pong_waiter, timeout=10)
                await asyncio.sleep(2)
        except Exception as e:
            if "going away" in str(e):
                self.logger.info(f"Client {client} disconnected normally")
            else:
                self.logger.error(f"Client disconnected or error: {e}")
        finally:
            if client in self.clients:
                self.clients.remove(client)
                self.logger.info(f"Removed client {client}")

    def get_clients(self):
        return self.clients


class WebSocketServer:
    def __init__(
        self, host="0.0.0.0", port=8765, api_key="12345678", logger: LogInterface = None
    ):
        self.host = host
        self.port = port
        self.logger = logger or LogInterface()
        self.client_handler = WebClientHandler(api_key=api_key, logger=self.logger)

    async def start(self):
        server = await websockets.serve(self.handle_connection, self.host, self.port)
        self.logger.info(f"Server started at {self.host}:{self.port}")
        await server.wait_closed()

    async def handle_connection(self, websocket: WebSocketClientProtocol):
        await self.client_handler.add_client(websocket)

    @staticmethod
    def run():
        import asyncio

        server = WebSocketServer()
        asyncio.run(server.start())
