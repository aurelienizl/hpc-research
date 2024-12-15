# server.py

import sys
import uuid
from flask import Flask, request, jsonify
from typing import Any, Dict, List

from worker import Worker
from scheduler import Scheduler
from log.LogInterface import LogInterface

# Configuration Constants
API_HOST = "127.0.0.1"
API_PORT = 5000


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
    # Initialize logging
    log = LogInterface(verbose=True)

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
