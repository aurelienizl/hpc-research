import asyncio
import websockets
import json
import socket

from Log.LogInterface import LogInterface
from Benchmarks.BaseBenchmarkInterface import BaseBenchmarkInterface

class BenchmarkWebSocketClient:
    def __init__(self, uri, api_key, verbose=False):
        self.uri = uri
        self.logger = LogInterface(verbose=verbose)
        self.interface = BaseBenchmarkInterface(self.logger)
        self.websocket = None
        self.api_key = api_key

    async def handle_message(self, message):
        """Handle incoming messages from the server."""
        data = json.loads(message)
        self.logger.info(f"Received message...")
        if data["message"] == "start_benchmark":
            self.logger.info(f"Starting benchmark: {data["message"]}")
            task_id = data["task_id"]
            benchmark = data["benchmark"]
            command_line = data["command_line"]
            config_params = data["config_params"]
            success = self.interface.start_benchmark(benchmark, task_id, command_line, **config_params)
            return json.dumps(success)
        elif data["message"] == "get_benchmark_status":
            self.logger.info(f"Getting benchmark status of task: {data["task_id"]}")
            task_id = data["task_id"]
            status = self.interface.get_benchmark_status(task_id)
            return json.dumps(status)
        elif data["message"] == "get_benchmark_results":
            self.logger.info(f"Getting benchmark results of task: {data["task_id"]}")
            task_id = data["task_id"]
            results = self.interface.get_benchmark_results(task_id)
            return json.dumps(results)
        elif data["message"] == "stop_benchmark":
            self.logger.info(f"Stopping benchmark: {data["task_id"]}")
            task_id = data["task_id"]
            success = self.interface.stop_benchmark(task_id)
            return json.dumps(success)
        else:
            return json.dumps("Invalid message")
        
    async def register(self):
        """Register the client with the server
        The client sends a json message:
        {
            "message": "connect",
            "api_key": "12345678",  
            "hostname": "client_hostname",
            "ip": "127.0.0.1"
        }
        """
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        
        message = {
            "message": "connect",
            "api_key": self.api_key,
            "hostname": hostname,
            "ip": ip_address
        }
        
        await self.websocket.send(json.dumps(message))
        self.logger.info(f"Registered with server: {message}")
        

    async def connect(self):
        """Establish and maintain a connection to the server with reconnection."""
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    self.websocket = websocket
                    self.logger.info(f"Connected to server at {self.uri}")
                    await self.register()
                    while True:
                        try:
                            message = await websocket.recv()
                            response = await self.handle_message(message)
                            await websocket.send(response)
                        except websockets.exceptions.ConnectionClosed:
                            self.logger.error("Connection closed by server.")
                            break
                        except Exception as e:
                            self.logger.error(f"Error handling message: {str(e)}")
                            break
            except Exception as e:
                self.logger.error(f"Connection failed: {str(e)}")
                self.logger.info("Attempting to reconnect in 5 seconds...")
                await asyncio.sleep(5)

