import os
import sys
import uuid
from flask import Flask, request, jsonify
from typing import Any, Dict, List

from worker import Worker
from scheduler import Scheduler
from log.LogInterface import LogInterface
from network.registration_handler import RegistrationHandler

# Server Configuration Constants
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 5000))

# Master Configuration Constants
MASTER_IP = os.getenv("MASTER_IP", "127.0.0.1")
MASTER_PORT = int(os.getenv("MASTER_PORT", 8000))

def safe_endpoint(log_interface):
    """Decorator for generic error handling in Flask endpoints."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_interface.error(f"Unhandled exception in endpoint {func.__name__}: {str(e)}")
                return jsonify({"error": "Internal Server Error"}), 500
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

def create_app(worker: Worker, log_interface: LogInterface) -> Flask:
    app = Flask(__name__)

    @app.route("/submit_custom_task", methods=["POST"])
    @safe_endpoint(log_interface)
    def submit_custom_task():
        data: Dict[str, Any] = request.get_json()
        if not data:
            log_interface.warning("Received invalid JSON payload.")
            return jsonify({"error": "Invalid JSON payload."}), 400

        # Extract and validate parameters
        required_params = ["ps", "qs", "n_value", "nb", "instances_num"]
        for param in required_params:
            if not isinstance(data.get(param), int) or data.get(param) <= 0:
                log_interface.warning(f"Validation failed for parameter: {param}.")
                return jsonify({"error": f"'{param}' must be a positive integer."}), 400

        ps = data["ps"]
        qs = data["qs"]
        n_value = data["n_value"]
        nb = data["nb"]
        instances_num = data["instances_num"]

        task_id = uuid.uuid4().hex
        success = worker.submit_task(task_id, ps, qs, n_value, nb, instances_num)

        if success:
            return jsonify({"task_id": task_id}), 200
        return jsonify({"error": "Resource busy. Another benchmark is currently running."}), 409

    @app.route("/task_status/<task_id>", methods=["GET"])
    @safe_endpoint(log_interface)
    def task_status_endpoint(task_id: str):
        status = worker.scheduler.get_task_status(task_id)
        if status is None:
            log_interface.info(f"Status check failed: Task ID {task_id} not found.")
            return jsonify({"error": "Task ID not found."}), 404
        return jsonify({"task_id": task_id, "status": status}), 200

    @app.route("/get_results/<task_id>", methods=["GET"])
    @safe_endpoint(log_interface)
    def get_results(task_id: str):
        result_dir = worker.scheduler.RESULT_DIR / task_id
        if not result_dir.exists() or not result_dir.is_dir():
            log_interface.info(f"Result retrieval failed: Task ID {task_id} not found.")
            return jsonify({"error": "Results for the given Task ID not found."}), 404

        result_files = list(result_dir.glob("*"))
        if not result_files:
            log_interface.info(f"No result files found for Task ID {task_id}.")
            return jsonify({"error": "No result files found for the given Task ID."}), 404

        results: List[Dict[str, Any]] = []
        for file_path in result_files:
            try:
                content = file_path.read_text()
                results.append({"filename": file_path.name, "content": content})
            except Exception as e:
                log_interface.error(f"Error reading file {file_path}: {str(e)}")
                return jsonify({"error": f"Failed to read file {file_path.name}."}), 500

        return jsonify({"task_id": task_id, "results": results}), 200

    @app.route("/ping", methods=["POST"])
    @safe_endpoint(log_interface)
    def ping():
        return jsonify({"message": "pong"}), 200

    return app

def main():
    print("Environment Variables:")
    print(f"API_HOST: {API_HOST}")
    print(f"API_PORT: {API_PORT}")
    print(f"MASTER_IP: {MASTER_IP}")
    print(f"MASTER_PORT: {MASTER_PORT}")

    log = LogInterface(verbose=True)
    log.log("info", "Starting server...")

    scheduler = Scheduler(log)

    worker = Worker(scheduler, log)
    registration_handler = RegistrationHandler(
        master_ip=MASTER_IP,
        master_port=MASTER_PORT,
        node_port=API_PORT,
        log_interface=log,
        additional_info={
            "operating_system": os.uname().sysname,
            "python_version": sys.version.split()[0],
        },
    )

    if not registration_handler.register_node():
        log.error("Node registration failed. Shutting down the server.")
        sys.exit(1)

    app = create_app(worker, log)

    try:
        app.run(host=API_HOST, port=API_PORT, threaded=True)
    except KeyboardInterrupt:
        worker.scheduler.shutdown()
        log.info("Server shutdown via KeyboardInterrupt.")
        sys.exit(0)
    except Exception as e:
        log.error(f"Server encountered an error: {e}")
        worker.scheduler.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()
