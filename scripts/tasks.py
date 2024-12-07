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
        self.scheduler = scheduler
        self.task_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._process_tasks, daemon=True)
        self.worker_thread.start()


        self.scheduler.log_interface.info("TaskManager initialized and worker thread started.")

    def enqueue_task(self, task: Dict[str, Any]):
        """
        Enqueue a new benchmark task.

        Args:
            task (Dict[str, Any]): Task details containing 'config_type' and 'cpu_count'.
        """
        self.task_queue.put(task)
        self.scheduler.log_interface.info(f"Task enqueued: {task}")

    def _process_tasks(self):
        """
        Worker method to continuously process tasks from the queue.
        """
        while True:
            task = self.task_queue.get()  # Blocks until a task is available
            if task is None:
                # Sentinel value to stop the worker
                self.scheduler.log_interface.info("Received shutdown signal. Stopping task processing.")
                break

            instance_type = task.get("config_type")
            cpu_count = task.get("cpu_count")

            self.scheduler.log_interface.info(f"Processing task: {task}")

            self.scheduler.handle_hpl_instance(instance_type, cpu_count)


    def shutdown(self):
        """
        Gracefully shutdown the TaskManager by stopping the worker thread.
        """
        self.task_queue.put(None)  # Sentinel value to stop the worker
        self.worker_thread.join()
        self.scheduler.log_interface.info("TaskManager shutdown completed.")
