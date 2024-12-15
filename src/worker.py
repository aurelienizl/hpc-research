# worker.py

import threading
from typing import Any, Dict, Optional
import queue

from scheduler import Scheduler  # Ensure scheduler.py is in the same directory
from log.LogInterface import (
    LogInterface,
)  # Ensure LogInterface.py is in the same directory


class Worker:
    """
    A global worker thread that processes HPC tasks one at a time.
    """

    def __init__(self, scheduler: Scheduler, log_interface: LogInterface):
        """
        Initialize the Worker with a Scheduler instance.

        Args:
            scheduler (Scheduler): The Scheduler instance to execute tasks.
            log_interface (LogInterface): The logging interface instance.
        """
        self.scheduler = scheduler
        self.task_queue = queue.Queue(maxsize=1)  # Only one task at a time
        self.task_status: Dict[str, str] = {}
        self.lock = threading.Lock()
        self.current_task_id: Optional[str] = None
        self.worker_thread: Optional[threading.Thread] = None
        self.logger = log_interface  # Initialize logger first
        self._start_worker()

    def _start_worker(self):
        """
        Start the worker thread.
        """
        self.worker_thread = threading.Thread(target=self._run, daemon=True)
        self.worker_thread.start()
        self.logger.info("Worker thread has been started.")  # Now logger is available

    def _run(self):
        """
        The main loop of the worker thread that processes tasks from the queue.
        """
        while True:
            task = self.task_queue.get()  # Blocks until a task is available
            if task is None:
                # Sentinel to shut down the worker
                self.logger.info("Worker thread is shutting down.")
                break

            task_id, ps, qs, n_value, nb, instances_num = task
            with self.lock:
                self.current_task_id = task_id
                self.task_status[task_id] = "Running"
                self.logger.info(f"Worker is processing task {task_id}.")

            try:
                self.scheduler.run_hpl_benchmark(
                    instance_id=task_id,
                    ps=ps,
                    qs=qs,
                    n_value=n_value,
                    nb=nb,
                    instances_num=instances_num,
                )
                with self.lock:
                    self.task_status[task_id] = "Completed"
                # Removed the redundant log below
                # self.logger.info(f"Task {task_id} has been completed.")
            except Exception as e:
                with self.lock:
                    self.task_status[task_id] = f"Failed: {str(e)}"
                    self.logger.error(f"Task {task_id} failed: {str(e)}")
            finally:
                with self.lock:
                    self.current_task_id = None
                self.task_queue.task_done()
                self.logger.info(f"Task {task_id} has been marked as completed.")

    def submit_task(
        self, task_id: str, ps: int, qs: int, n_value: int, nb: int, instances_num: int
    ) -> bool:
        """
        Attempt to submit a new task to the worker.

        Args:
            task_id (str): Unique identifier for the task.
            ps (int): Process grid P.
            qs (int): Process grid Q.
            n_value (int): Problem size N.
            nb (int): Block size.
            instances_num (int): Number of HPL instances to run.

        Returns:
            bool: True if the task was successfully enqueued, False otherwise.
        """
        with self.lock:
            if self.current_task_id is not None:
                self.logger.warning(
                    "Resource busy. Another benchmark is currently running."
                )
                return False
            else:
                try:
                    self.task_queue.put_nowait(
                        (task_id, ps, qs, n_value, nb, instances_num)
                    )
                    self.task_status[task_id] = "Pending"
                    self.logger.info(f"Task {task_id} has been submitted.")
                    return True
                except queue.Full:
                    self.logger.error("Task queue is full. Cannot submit a new task.")
                    return False

    def get_status(self, task_id: str) -> Optional[str]:
        """
        Retrieve the status of a given task.

        Args:
            task_id (str): The unique identifier of the task.

        Returns:
            Optional[str]: The current status of the task or None if not found.
        """
        with self.lock:
            return self.task_status.get(task_id, None)

    def shutdown(self):
        """
        Gracefully shut down the worker thread.
        """
        self.logger.info("Shutting down worker thread.")
        self.task_queue.put(None)  # Sentinel to stop the worker
        if self.worker_thread is not None:
            self.worker_thread.join()
        self.logger.info("Worker thread has been shut down.")
