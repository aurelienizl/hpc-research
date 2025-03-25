import json
from websockets import WebSocketClientProtocol


class BenchmarksAPI:
    @staticmethod
    async def start_benchmark(
        websocket: WebSocketClientProtocol,
        task_id: str,
        benchmark: str,
        command_line: str,
        specials_params: dict,
    ) -> bool:
        message = {
            "message": "start_benchmark",
            "task_id": task_id,
            "benchmark": benchmark,
            "command_line": command_line,
            "config_params": specials_params,
        }
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        return json.loads(response)

    @staticmethod
    async def get_benchmark_status(task_id: str, websocket: WebSocketClientProtocol):
        message = {"message": "get_benchmark_status", "task_id": task_id}
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        return json.loads(response)

    @staticmethod
    async def stop_benchmark(websocket: WebSocketClientProtocol, task_id: str):
        message = {"message": "stop_benchmark", "task_id": task_id}
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        return json.loads(response)

    @staticmethod
    async def get_benchmark_results(task_id: str, websocket: WebSocketClientProtocol):
        message = {"message": "get_benchmark_results", "task_id": task_id}
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        return json.loads(response)
