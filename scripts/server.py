# server.py

import threading
import sys
import logging
import uuid
from flask import Flask, request, jsonify
from typing import Any, Dict, List
from pathlib import Path

from scheduler import Scheduler


# Configuration Constants
API_HOST = "127.0.0.1"
API_PORT = 5000


def create_app(scheduler: Scheduler) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        scheduler (Scheduler): The Scheduler instance to interact with.

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
            return jsonify({"error": "Invalid JSON payload."}), 400

        ps = data.get("ps")
        qs = data.get("qs")
        n_value = data.get("n_value")
        nb = data.get("nb")
        instances_num = data.get("instances_num")

        # Validate input parameters
        if not all(
            isinstance(param, int) and param > 0 for param in [ps, qs, n_value, nb, instances_num]
        ):
            return (
                jsonify(
                    {
                        "error": "'ps', 'qs', 'n_value', and 'nb' must be positive integers."
                    }
                ),
                400,
            )
            
        # Generate a unique identifier for the task
        task_id = uuid.uuid4().hex

        # Submit the task to the scheduler
        try:
            scheduler.run_hpl_benchmark(
                instance_id=task_id,  # Changed to string
                ps=ps,
                qs=qs,
                n_value=n_value,
                nb=nb,
                instances_num=instances_num
            )
            logging.info(f"Task {task_id} submitted successfully.")
        except Scheduler.TaskAlreadyRunningException:
            logging.warning(f"Task submission rejected. Task {task_id} could not be started because another task is running.")
            return jsonify({"error": "Another benchmark is currently running. Please try again later."}), 409
        except Exception as e:
            logging.error(f"Error submitting task {task_id}: {str(e)}")
            return jsonify({"error": "Internal server error."}), 500

        return jsonify({"task_id": task_id}), 200

    @app.route("/task_status/<task_id>", methods=["GET"])
    def task_status(task_id: str):
        """
        Endpoint to check the status of a submitted HPC task.

        Args:
            task_id (str): The unique identifier of the task.

        Returns:
            JSON response with task status.
        """
        status = scheduler.get_task_status(task_id)
        if status is None:
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
        result_dir = scheduler.RESULT_DIR / task_id

        if not result_dir.exists() or not result_dir.is_dir():
            return jsonify({"error": "Results for the given Task ID not found."}), 404

        # List all result files
        result_files = list(result_dir.glob("*"))
        if not result_files:
            return jsonify({"error": "No result files found for the given Task ID."}), 404

        results: List[Dict[str, Any]] = []

        for file_path in result_files:
            try:
                # For collectl.log, enforce a size limit of 10 MB
                if file_path.name == "collectl.log":
                    if file_path.stat().st_size > 10 * 1024 * 1024:
                        return jsonify({"error": "collectl.log exceeds the maximum allowed size of 10 MB."}), 400

                with open(file_path, "r") as file:
                    content = file.read()

                results.append({
                    "filename": file_path.name,
                    "content": content
                })

            except Exception as e:
                logging.error(f"Error reading file {file_path}: {str(e)}")
                return jsonify({"error": f"Failed to read file {file_path.name}."}), 500

        return jsonify({"task_id": task_id, "results": results}), 200

    return app

def main():
    """
    Main function to initialize the Scheduler, create the Flask API, and start the server.
    """
    # Configure Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("Main")

    # Initialize Scheduler
    scheduler = Scheduler()
    try:
        scheduler.install_dependencies()
        scheduler.setup_environment()
    except Exception as e:
        logger.error(f"Failed to initialize Scheduler: {str(e)}")
        sys.exit(1)

    # Create Flask app
    app = create_app(scheduler)

    # Start Flask app in a separate thread
    flask_thread = threading.Thread(
        target=lambda: app.run(host=API_HOST, port=API_PORT, threaded=True),
        daemon=True
    )
    flask_thread.start()
    logger.info(f"Flask API server started on {API_HOST}:{API_PORT}")

    # Keep the main thread alive
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
