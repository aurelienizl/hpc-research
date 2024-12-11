# server.py

import threading
import sys
import logging
from flask import Flask, request, jsonify
from typing import Any, Dict

from tasks import TaskManager
from scheduler import Scheduler


# Configuration Constants
CONFIGURATIONS_DIR = "HPLConfigurations"
API_HOST = "127.0.0.1"
API_PORT = 5000


def create_app(task_manager: TaskManager) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        task_manager (TaskManager): The TaskManager instance to interact with.

    Returns:
        Flask: Configured Flask app.
    """
    app = Flask(__name__)

    @app.route("/submit_task", methods=["POST"])
    def submit_task():
        """
        Endpoint to submit a new HPL benchmark task.

        Expected JSON payload:
        {
            "config_type": "cooperative" or "competitive",
            "cpu_count": int,
            "memory_usage": int (optional)
        }
        """
        data: Dict[str, Any] = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload."}), 400

        config_type = data.get("config_type")
        cpu_count = data.get("cpu_count")
        memory_usage = data.get("memory_usage")

        # Validate input parameters
        if config_type not in ["cooperative", "competitive"]:
            return (
                jsonify(
                    {
                        "error": "Invalid config_type. Must be 'cooperative' or 'competitive'."
                    }
                ),
                400,
            )

        if not isinstance(cpu_count, int) or cpu_count < 1:
            return (
                jsonify({"error": "Invalid cpu_count. Must be a positive integer."}),
                400,
            )

        task: Dict[str, Any] = {
            "task_type": "hpl",
            "config_type": config_type,
            "cpu_count": cpu_count,
            "memory_usage": memory_usage,
        }

        task_id = task_manager.enqueue_task(task)
        if task_id is None:
            return jsonify({"error": "Task queue is full."}), 503

        return jsonify({"task_id": task_id}), 200

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
            "comp": bool (optional)
        }
        """
        data: Dict[str, Any] = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload."}), 400

        ps = data.get("ps")
        qs = data.get("qs")
        n_value = data.get("n_value")
        nb = data.get("nb")
        comp = data.get("comp", False)

        # Validate input parameters
        if not all(
            isinstance(param, int) and param > 0 for param in [ps, qs, n_value, nb]
        ):
            return (
                jsonify(
                    {
                        "error": "'ps', 'qs', 'n_value', and 'nb' must be positive integers."
                    }
                ),
                400,
            )

        if not isinstance(comp, bool):
            return jsonify({"error": "'comp' must be a boolean value."}), 400

        task: Dict[str, Any] = {
            "task_type": "custom",
            "ps": ps,
            "qs": qs,
            "n_value": n_value,
            "nb": nb,
            "comp": comp,
        }

        task_id = task_manager.enqueue_task(task)
        if task_id is None:
            return jsonify({"error": "Task queue is full."}), 503

        return jsonify({"task_id": task_id}), 200

    @app.route("/tasks/<int:task_id>", methods=["GET"])
    def get_task_status(task_id: int):
        """
        Endpoint to check the status of a specific task.

        Args:
            task_id (int): The task ID to check.

        Returns:
            JSON response with task status or error message.
        """
        status = task_manager.get_task_status(task_id)
        if status:
            return jsonify({"task_id": task_id, "status": status}), 200
        else:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404

    @app.route("/tasks", methods=["GET"])
    def get_all_tasks():
        """
        Endpoint to get the status of all tasks.

        Returns:
            JSON response with queue size and active worker threads.
        """
        queue_size = task_manager.task_queue.qsize()
        active_workers = (
            threading.active_count() - 2
        )  # Subtracting main and worker threads
        return (
            jsonify({"queue_size": queue_size, "active_workers": active_workers}),
            200,
        )

    return app


def main():
    """
    Main function to initialize the Scheduler, TaskManager, and start the Flask API.
    """
    # Configure Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("Main")

    # Initialize Scheduler
    scheduler = Scheduler(config_output_dir=CONFIGURATIONS_DIR)
    scheduler.install_dependencies()
    scheduler.setup_environment()

    # Initialize TaskManager
    task_manager = TaskManager(scheduler=scheduler)

    # Create Flask app
    app = create_app(task_manager)

    # Start Flask app in a separate thread
    flask_thread = threading.Thread(
        target=lambda: app.run(host=API_HOST, port=API_PORT, threaded=True), daemon=True
    )
    flask_thread.start()
    logger.info(f"Flask API server started on {API_HOST}:{API_PORT}")

    # Keep the main thread alive
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down...")
        task_manager.shutdown()
        sys.exit(0)


if __name__ == "__main__":
    main()
