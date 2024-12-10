# tasks.py

import threading
import queue
from multiprocessing import Process
from typing import Optional, Dict, Any

from scheduler import Scheduler


class TaskManager:
    """
    TaskManager class responsible for:
    - Managing a queue of benchmark tasks.
    - Processing tasks one by one to ensure proper queuing.
    - Running HPL instances using the Scheduler.
    """

    def __init__(self, scheduler: Scheduler):
        """
        Initialize the TaskManager.

        Args:
            scheduler (Scheduler): The Scheduler instance to execute tasks.
        """
        # Reference to the Scheduler instance
        self.scheduler = scheduler

        # Use a queue to store benchmark tasks, 10 tasks max
        self.task_queue = queue.Queue()
        self.task_queue_size = 10

        # Start a worker thread to process tasks
        self.worker_thread = threading.Thread(target=self._process_tasks, daemon=True)
        self.worker_thread.start()

        # Use task id mechanism to track tasks
        self.task_id = 0
        self.task_id_lock = threading.Lock()

        # Dictionary to store task status
        self.task_status = {}

        self.scheduler.log_interface.info(
            "TaskManager initialized and worker thread started."
        )

    def enqueue_task(self, task: Dict[str, Any]):
        """
        Enqueue a new benchmark task.

        Args:
            task (Dict[str, Any]): Task details containing 'config_type', 'cpu_count' and task-specific parameters.
        """

        # Check if task queue is full
        if len(self.task_status) >= self.task_queue_size:
            self.scheduler.log_interface.error(
                "Task queue is full. Cannot enqueue new task."
            )
            return None

        # Lock, increment, assign and put task in queue
        with self.task_id_lock:
            self.task_id += 1
            task["task_id"] = self.task_id

        # Assign status as 'queued' now and update later
        self.task_status[task["task_id"]] = "queued"

        # Put task in queue
        self.task_queue.put(task)

        self.scheduler.log_interface.info(
            f"Task enqueued: {task} with task_id: {self.task_id}"
        )
        return self.task_id

    def _process_tasks(self):
        """
        Worker method to continuously process tasks from the queue.
        """
        while True:
            task = self.task_queue.get()  # Blocks until a task is available
            if task is None:
                # Sentinel value to stop the worker
                self.scheduler.log_interface.info(
                    "Received shutdown signal. Stopping task processing."
                )
                break

            # Update task status to 'processing'
            task_id = task.get("task_id")
            self.task_status[task_id] = "processing"

            instance_type = task.get("config_type")
            cpu_count = task.get("cpu_count")
            memory_usage = task.get("memory_usage")

            self.scheduler.log_interface.info(
                f"Processing task: {task}" + f" with task_id: {task_id}"
            )

            self.scheduler.handle_hpl_instance(instance_type, cpu_count, memory_usage, task_id)

            self.scheduler.log_interface.info(
                f"Task completed: {task}" + f" with task_id: {task_id}"
            )

            # Update task status to 'completed'
            self.task_status[task_id] = "completed"

    def get_task_status(self, task_id: int) -> Optional[str]:
        """
        Get the status of a specific task.

        Args:
            task_id (int): The task ID to check.

        Returns:
            - Task status if the task is found.
            - None if the task is not found.
        """
        return self.task_status.get(task_id)

    def shutdown(self):
        """
        Gracefully shutdown the TaskManager by stopping the worker thread.
        """
        self.task_queue.put(None)  # Sentinel value to stop the worker
        self.worker_thread.join()
        self.scheduler.log_interface.info("TaskManager shutdown completed.")
