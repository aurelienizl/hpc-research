import argparse
import threading

from menu_handler import app, menu_handler

def run_server(host: str, port: int) -> None:
    app.run(host=host, port=port, threaded=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master Server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    args = parser.parse_args()

    server_thread = threading.Thread(target=run_server, args=(args.host, args.port), daemon=True)
    server_thread.start()

    print(f"Server running on http://{args.host}:{args.port}")
    menu_handler.run()
