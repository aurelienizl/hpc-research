from flask import Flask, request, jsonify
import argparse
import threading
from menu_handler import MenuHandler

app = Flask(__name__)
menu_handler = MenuHandler()


@app.route("/register", methods=["POST"])
def register():
    node_data = request.json or {}
    ip_address = request.remote_addr
    node_entry = menu_handler.register_node(ip_address, node_data)
    return jsonify({"status": "registered", "node": node_entry}), 200


def run_server(host: str, port: int) -> None:
    server_thread = threading.Thread(
        target=app.run, kwargs={"host": host, "port": port}
    )
    server_thread.daemon = True
    server_thread.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master Server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")

    args = parser.parse_args()
    run_server(args.host, args.port)
    print(f"Server running on http://{args.host}:{args.port}")
    menu_handler.run()
