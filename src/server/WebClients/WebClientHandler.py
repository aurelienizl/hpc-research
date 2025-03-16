import asyncio
import json

from Log import LogInterface
from WebClients.WebClient import WebClient
from Benchmarks.benchmarksHandler import BenchmarksHandler

class WebClientHandler:

    def __init__(self, api_key: str, logger: LogInterface):
        self.logger = logger
        self.clients = [] 
        self.api_key = api_key
        
    async def launch_benchmark(self):
        bench_handler = BenchmarksHandler("benchmarks.config", self.clients, self.logger)
        await bench_handler.run_benchmarks()
    
    async def add_client(self, websocket):
        """
        Add a new client to the list of connected clients.
        The client send first a json message :
        {
            "message": "connect",
            "api_key": "123456",
            "hostname": "client_hostname",
            "ip": "client_ip"
        }
        """
        try:
            message = await websocket.recv()
            message = json.loads(message)
            if message["message"] == "connect":
                client_hostname = message["hostname"]
                client_ip = message["ip"]
                client_api_key = message["api_key"]
                if client_api_key == self.api_key:
                    new_client = WebClient(websocket, client_ip, client_hostname)
                    self.clients.append(new_client)
                    self.logger.info(f"Client {client_hostname} connected.")
                    await self.keep_client_alive(new_client)
                else:
                    self.logger.error(f"Client {client_hostname} failed to connect: Invalid API key.")
                
        except Exception as e:
            self.logger.error(f"Error adding client: {e}")
        
    async def keep_client_alive(self, client: WebClient):
        try:
            while True:
                # Send a ping and wait for a pong response
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