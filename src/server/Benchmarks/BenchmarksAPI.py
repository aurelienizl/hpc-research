import json

from websockets import WebSocketClientProtocol
from Log.LogInterface import LogInterface

class BenchmarksAPI:
    @staticmethod
    async def start_benchmark(
        websocket: WebSocketClientProtocol,
        logger: LogInterface,
        task_id: str,
        benchmark: str,
        command_line: str,
        config_params: dict
    ):
        """Send a request to start a benchmark on the client."""
        message = {
            "message": "start_benchmark",
            "task_id": task_id,
            "benchmark": benchmark,
            "command_line": command_line,
            "config_params": config_params
        }
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        return json.loads(response)

    @staticmethod
    async def get_benchmark_status(
        websocket: WebSocketClientProtocol,
        logger: LogInterface,
        task_id: str
    ):
        """Get the status of a benchmark from the client."""
        message = {"message": "get_benchmark_status", "task_id": task_id}
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        return json.loads(response)
    
    @staticmethod
    async def stop_benchmark(
        websocket: WebSocketClientProtocol,
        logger: LogInterface,
        task_id: str
    ):
        """Request the client to stop a benchmark."""
        message = {"message": "stop_benchmark", "task_id": task_id}
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        return json.loads(response)

    @staticmethod
    async def get_benchmark_results(
        websocket: WebSocketClientProtocol,
        logger: LogInterface,
        task_id: str
    ):
        """Retrieve benchmark results from the client."""
        message = {"message": "get_benchmark_results", "task_id": task_id}
        await websocket.send(json.dumps(message))
        response = await websocket.recv()

        return json.loads(response)

