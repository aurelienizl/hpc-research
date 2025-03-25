import asyncio
from WebClient.WebClientHandler import WebSocketServer
from Benchmark.BenchmarkHandler import BenchmarkHandler
from Log.LogInterface import LogInterface


async def main():

    logger = LogInterface()

    ws_server = WebSocketServer(api_key="12345678", logger=logger)

    server_task = asyncio.create_task(ws_server.start())

    await asyncio.sleep(5)

    connected_clients = ws_server.client_handler.get_clients()
    logger.info(f"Connected clients: {connected_clients}")

    benchmark_handler = BenchmarkHandler(
        connected_clients, "config.yaml", logger=logger
    )

    await benchmark_handler.run_benchmarks()

    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    asyncio.run(main())
