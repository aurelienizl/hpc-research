# server.py

import threading
import sys
from flask import Flask, request, jsonify
from tasks import TaskManager
from scheduler import Scheduler


# Configuration
CONFIGURATIONS_DIR = "HPLConfigurations"
API_HOST = "127.0.0.1"
API_PORT = 5000


def create_app(task_manager: TaskManager) -> Flask:
    """
    Create and configure the Flask app.

    Args:
        task_manager (TaskManager): The TaskManager instance to interact with.

    Returns:
        Flask: The configured Flask app.
    """
    app = Flask(__name__)

    @app.route("/submit_task", methods=["POST"])
    def submit_task():
        """
        Endpoint to submit a new benchmark task.

        Expected JSON payload:
        {
            "config_type": "cooperative" or "competitive",
            "cpu_count": integer
        }
        """
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload."}), 400

        config_type = data.get("config_type")
        cpu_count = data.get("cpu_count")

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

        task = {"config_type": config_type, "cpu_count": cpu_count, "task_id": None}

        task_id = task_manager.enqueue_task(task)
        return jsonify({"task_id": task_id}), 200

    @app.route("/tasks/<int:task_id>", methods=["GET"])
    def task_status(task_id: int):
        """
        Endpoint to check the status of a specific task.

        Args:
            task_id (int): The task ID to check.

        Returns:
            - Task details if the task is found.
            - Error message if the task is not found.
        """
        task_status = task_manager.get_task_status(task_id)

        if task_status:
            return jsonify({"task_id": task_id, "status": task_status}), 200
        else:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404

    @app.route("/tasks", methods=["GET"])
    def status():
        """
        Endpoint to check the scheduler's status.

        Returns:
            - Number of tasks in the queue.
            - Number of active worker threads.
        """
        queue_size = task_manager.task_queue.qsize()
        active_workers = (
            threading.active_count()
        )  # Includes main thread and worker thread
        return (
            jsonify({"queue_size": queue_size, "active_workers": active_workers}),
            200,
        )

    return app


def main():
    """
    Main function to initialize the Scheduler, TaskManager, and start the Flask API.
    """
    # Initialize Scheduler
    scheduler = Scheduler(config_output_dir=CONFIGURATIONS_DIR)

    # Install dependencies
    scheduler.install_dependencies()

    # Set up the environment
    scheduler.setup_environment()

    # Initialize TaskManager
    task_manager = TaskManager(scheduler=scheduler)

    # Create Flask app
    app = create_app(task_manager)

    # Start Flask app in a separate thread to prevent blocking
    flask_thread = threading.Thread(
        target=lambda: app.run(host=API_HOST, port=API_PORT, threaded=True), daemon=True
    )
    flask_thread.start()
    scheduler.log_interface.info(f"Flask API server started on {API_HOST}:{API_PORT}")

    # Keep the main thread alive to allow worker and Flask threads to run
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        scheduler.log_interface.info("Received KeyboardInterrupt. Shutting down...")
        task_manager.shutdown()
        sys.exit(0)


if __name__ == "__main__":
    main()
