import asyncio
import websockets
import threading

from Log.LogInterface import LogInterface
from WebClients.WebClientHandler import WebClientHandler
from Menu.SimpleMenu import SimpleMenu

class WebSocketServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.logger = LogInterface(log_verbose=True)
        self.client_handler = WebClientHandler(api_key="12345678", logger=self.logger)
        self.shutdown_event = asyncio.Event()

    async def start(self):
        loop = asyncio.get_running_loop()

        # Start the menu in a separate thread
        menu = SimpleMenu(self.client_handler, self.logger, loop, self.shutdown_event)
        menu_thread = threading.Thread(target=menu.run_menu, daemon=True)
        menu_thread.start()

        # Start websocket server
        server = await websockets.serve(self.handle_connection, self.host, self.port)
        self.logger.info(f"Server started at {self.host}:{self.port}")
        
        await self.shutdown_event.wait()
        self.logger.info("Shutdown signal received. Stopping server...")
        server.close()
        await server.wait_closed()

    async def handle_connection(self, websocket):
        await self.client_handler.add_client(websocket)

    @staticmethod
    def run():
        server = WebSocketServer()
        asyncio.run(server.start())


if __name__ == "__main__":
    WebSocketServer.run()
