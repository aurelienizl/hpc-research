# tasks.py

import threading
import queue
from typing import Optional, Dict, Any
import logging

from scheduler import Scheduler


class TaskManager:
    """
    Manages a queue of benchmark tasks, processing them sequentially
    and executing HPL instances using the Scheduler.
    """

    def __init__(self, scheduler: Scheduler, max_queue_size: int = 10):
        """
        Initialize the TaskManager.

        Args:
            scheduler (Scheduler): The Scheduler instance to execute tasks.
            max_queue_size (int): Maximum number of tasks allowed in the queue.
        """
        self.scheduler = scheduler
        self.task_queue = queue.Queue(maxsize=max_queue_size)
        self.max_queue_size = max_queue_size

        self.task_id_counter = 0
        self.task_id_lock = threading.Lock()
        self.task_status: Dict[int, str] = {}

        self.worker_thread = threading.Thread(target=self._process_tasks, daemon=True)
        self.worker_thread.start()

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("TaskManager initialized and worker thread started.")

    def enqueue_task(self, task: Dict[str, Any]) -> Optional[int]:
        """
        Enqueue a new benchmark task.

        Args:
            task (Dict[str, Any]): Task details containing 'task_type' and other task-specific parameters.

        Returns:
            Optional[int]: The assigned task ID if enqueued successfully, else None.
        """
        if self.task_queue.full():
            self.logger.error("Task queue is full. Cannot enqueue new task.")
            return None

        with self.task_id_lock:
            self.task_id_counter += 1
            task_id = self.task_id_counter
            task["task_id"] = task_id

        self.task_status[task_id] = "queued"

        try:
            self.task_queue.put(task, block=False)
            self.logger.info(f"Task enqueued: {task} with task_id: {task_id}")
            return task_id
        except queue.Full:
            self.logger.error("Failed to enqueue task; queue is full.")
            return None

    def _process_tasks(self):
        """
        Worker method to continuously process tasks from the queue.
        """
        while True:
            task = self.task_queue.get()
            if task is None:
                self.logger.info("Shutdown signal received. Stopping task processing.")
                break

            task_id = task.get("task_id")
            self.task_status[task_id] = "processing"

            task_type = task.get("task_type", "hpl")
            self.logger.info(f"Processing task_id: {task_id} of type: {task_type}")

            try:
                if task_type == "hpl":
                    self._handle_hpl_task(task)
                elif task_type == "custom":
                    self._handle_custom_task(task)
                else:
                    self.logger.error(
                        f"Unknown task type: {task_type} for task_id: {task_id}"
                    )
            except Exception as e:
                self.logger.error(f"Error processing task_id: {task_id} - {e}")
                self.task_status[task_id] = "failed"
                continue

            self.task_status[task_id] = "completed"
            self.logger.info(f"Task completed: task_id: {task_id}")

    def _handle_hpl_task(self, task: Dict[str, Any]):
        """
        Handle execution of an HPL task.

        Args:
            task (Dict[str, Any]): Task details.
        """
        instance_type = task.get("config_type")
        cpu_count = task.get("cpu_count")
        memory_usage = task.get("memory_usage")
        task_id = task.get("task_id")

        self.scheduler.handle_hpl_instance(
            instance_type=instance_type,
            cpu_count=cpu_count,
            memory_usage=memory_usage,
            instance_id=task_id,
        )

    def _handle_custom_task(self, task: Dict[str, Any]):
        """
        Handle execution of a custom HPC task.

        Args:
            task (Dict[str, Any]): Task details.
        """
        task_id = task.get("task_id")
        ps = task.get("ps")
        qs = task.get("qs")
        n_value = task.get("n_value")
        nb = task.get("nb")
        comp = task.get("comp", False)

        self.scheduler.handle_custom_hpl_instance(
            instance_id=task_id, ps=ps, qs=qs, n_value=n_value, nb=nb, comp=comp
        )

    def get_task_status(self, task_id: int) -> Optional[str]:
        """
        Get the status of a specific task.

        Args:
            task_id (int): The task ID to check.

        Returns:
            Optional[str]: Task status if found, else None.
        """
        return self.task_status.get(task_id)

    def shutdown(self):
        """
        Gracefully shutdown the TaskManager by stopping the worker thread.
        """
        self.task_queue.put(None)
        self.worker_thread.join()
        self.logger.info("TaskManager shutdown completed.")
