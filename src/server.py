# server.py

import os
import sys
import uuid
import requests
from flask import Flask, request, jsonify
from typing import Any, Dict, List

from worker import Worker
from scheduler import Scheduler
from log.LogInterface import LogInterface

# Server Configuration Constants
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", 5000))
API_KEY = os.getenv("API_KEY", "")

# Master Configuration Constants
MASTER_IP = os.getenv("MASTER_IP", "")
MASTER_PORT = int(os.getenv("MASTER_PORT", 5000))
MASTER_API_KEY = os.getenv("MASTER_API_KEY", "")

REGISTER_ENDPOINT = f"http://{MASTER_IP}:{MASTER_PORT}/register"


def register_node(log_interface: LogInterface) -> bool:
    """
    Registers the node with the master node by sending a POST request to the /register endpoint.

    Args:
        log_interface (LogInterface): The logging interface instance.

    Returns:
        bool: True if registration was successful, False otherwise.
    """
    node_ip = API_HOST

    payload = {
        "api_key": MASTER_API_KEY,
        "node_ip": node_ip,
        "node_port": API_PORT
    }

    try:
        log_interface.info(
            f"Attempting to register node with master at {REGISTER_ENDPOINT}..."
        )
        response = requests.post(REGISTER_ENDPOINT, json=payload, timeout=10)

        if response.status_code == 200:
            log_interface.info("Node successfully registered with the master node.")
            return True
        else:
            log_interface.error(
                f"Failed to register node. Status Code: {response.status_code}, Response: {response.text}"
            )
            return False

    except requests.exceptions.RequestException as e:
        log_interface.error(f"Exception during node registration: {e}")
        return False


def create_app(worker: Worker, log_interface: LogInterface) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        worker (Worker): The Worker instance to interact with.
        log_interface (LogInterface): The logging interface instance.

    Returns:
        Flask: Configured Flask app.
    """
    app = Flask(__name__)

    @app.before_request
    def limit_remote_addr():
        if request.remote_addr != MASTER_IP:
            return "Unauthorized", 403

    @app.route("/submit_custom_task", methods=["POST"])
    def submit_custom_task():
        """
        Endpoint to submit a new custom HPC task.

        Expected JSON payload:
        {
            "ps": int,
            "qs": int,
            "n_value": int,
            "nb": int,
            "instances_num": int
        }
        """
        data: Dict[str, Any] = request.get_json()
        if not data:
            log_interface.warning("Received invalid JSON payload.")
            return jsonify({"error": "Invalid JSON payload."}), 400

        if "api_key" not in data or data["api_key"] != API_KEY:
            log_interface.warning("API key is missing or incorrect.")
            return jsonify({"error": "API key is missing or incorrect."}), 401

        ps = data.get("ps")
        qs = data.get("qs")
        n_value = data.get("n_value")
        nb = data.get("nb")
        instances_num = data.get("instances_num")

        # Validate input parameters
        if not all(
            isinstance(param, int) and param > 0
            for param in [ps, qs, n_value, nb, instances_num]
        ):
            log_interface.warning("Validation failed for input parameters.")
            return (
                jsonify(
                    {
                        "error": "'ps', 'qs', 'n_value', 'nb', and 'instances_num' must be positive integers."
                    }
                ),
                400,
            )

        # Generate a unique identifier for the task
        task_id = uuid.uuid4().hex

        # Attempt to submit the task to the worker
        success = worker.submit_task(task_id, ps, qs, n_value, nb, instances_num)
        if success:
            return jsonify({"task_id": task_id}), 200
        else:
            return (
                jsonify(
                    {"error": "Resource busy. Another benchmark is currently running."}
                ),
                409,
            )

    @app.route("/task_status/<task_id>", methods=["GET"])
    def task_status_endpoint(task_id: str):
        """
        Endpoint to check the status of a submitted HPC task.

        Args:
            task_id (str): The unique identifier of the task.

        Returns:
            JSON response with task status.
        """
        status = worker.get_status(task_id)
        if status is None:
            log_interface.info(f"Status check failed: Task ID {task_id} not found.")
            return jsonify({"error": "Task ID not found."}), 404

        return jsonify({"task_id": task_id, "status": status}), 200

    @app.route("/get_results/<task_id>", methods=["GET"])
    def get_results(task_id: str):
        """
        Endpoint to retrieve the results of a completed HPC task.

        Args:
            task_id (str): The unique identifier of the task.

        Returns:
            JSON response containing the contents of result files.
        """
        result_dir = worker.scheduler.RESULT_DIR / task_id

        if not result_dir.exists() or not result_dir.is_dir():
            log_interface.info(f"Result retrieval failed: Task ID {task_id} not found.")
            return jsonify({"error": "Results for the given Task ID not found."}), 404

        # List all result files
        result_files = list(result_dir.glob("*"))
        if not result_files:
            log_interface.info(f"No result files found for Task ID {task_id}.")
            return (
                jsonify({"error": "No result files found for the given Task ID."}),
                404,
            )

        results: List[Dict[str, Any]] = []

        for file_path in result_files:
            try:
                with open(file_path, "r") as file:
                    content = file.read()

                results.append({"filename": file_path.name, "content": content})

            except Exception as e:
                log_interface.error(f"Error reading file {file_path}: {str(e)}")
                return jsonify({"error": f"Failed to read file {file_path.name}."}), 500

        return jsonify({"task_id": task_id, "results": results}), 200

    return app

def main():
    """
    Main function to initialize the Scheduler, Worker, create the Flask API, and start the server.
    """

    # Print all environment variables
    print("Environment Variables:")
    print(f"API_HOST: {API_HOST}")
    print(f"API_PORT: {API_PORT}")
    print(f"API_KEY: {API_KEY}")
    print(f"MASTER_IP: {MASTER_IP}")
    print(f"MASTER_PORT: {MASTER_PORT}")
    print(f"MASTER_API_KEY: {MASTER_API_KEY}")

    # Initialize logging
    log = LogInterface(verbose=True)

    log.log("info", "Starting server...")

    # Initialize Scheduler
    scheduler = Scheduler(log)

    try:
        scheduler.install_dependencies()
        scheduler.setup_environment()
    except Exception as e:
        log.error(f"Scheduler initialization failed: {e}")
        sys.exit(1)

    # Initialize Worker
    worker = Worker(scheduler, log)

    # Register node with master
    registration_success = register_node(log)
    if not registration_success:
        log.error("Node registration failed. Shutting down the server.")
        sys.exit(1)

    # Create Flask app
    app = create_app(worker, log)  # Pass log to create_app

    # Start Flask app in the main thread
    try:
        app.run(host=API_HOST, port=API_PORT, threaded=True)
    except KeyboardInterrupt:
        worker.shutdown()
        log.info("Server shutdown via KeyboardInterrupt.")
        sys.exit(0)
    except Exception as e:
        log.error(f"Server encountered an error: {e}")
        worker.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()
