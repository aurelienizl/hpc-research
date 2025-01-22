import argparse
import threading

from menu_handler import MenuHandler
from server import create_app
import logic


def run_server(host: str, port: int, menu_handler: MenuHandler) -> None:
    app = create_app(menu_handler)
    app.run(host=host, port=port, threaded=True)

if __name__ == "__main__":
    # 1) Generate the SSH key pair if needed
    logic.generate_ssh_key()

    # 2) Parse command-line arguments
    parser = argparse.ArgumentParser(description="Master Server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    args = parser.parse_args()

    # 3) Create the menu handler
    menu_handler = MenuHandler()

    # 4) Start the Flask server in a separate daemon thread
    server_thread = threading.Thread(
        target=run_server, 
        args=(args.host, args.port, menu_handler), 
        daemon=True
    )
    server_thread.start()

    print(f"Server running on http://{args.host}:{args.port}")

    # 5) Run the interactive menu
    menu_handler.run()
