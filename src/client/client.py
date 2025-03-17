import asyncio
from Websocket.websocket import BenchmarkWebSocketClient


async def main():
    uri = "ws://127.0.0.1:8765"
    client = BenchmarkWebSocketClient(uri, api_key="12345678", verbose=True)
    await client.connect()

if __name__ == "__main__":
    asyncio.run(main())
