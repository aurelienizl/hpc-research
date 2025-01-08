import threading
from typing import Optional

from scheduler import Scheduler
from log.LogInterface import LogInterface

class Worker:
    """
    Simplified Worker that directly uses the Scheduler to run tasks one at a time.
    """

    def __init__(self, scheduler: Scheduler, log_interface: LogInterface):
        """
        Initialize the Worker with a Scheduler instance.
        """
        self.scheduler = scheduler
        self.logger = log_interface

    def submit_task(
        self, task_id: str, ps: int, qs: int, n_value: int, nb: int, instances_num: int
    ) -> bool:
        """
        Attempt to submit a new task to the worker. Directly starts the task if no other is running.
        """
        # Use scheduler's own mechanism to ensure one task at a time.
        with self.scheduler.status_lock:
            if self.scheduler.current_task_id is not None:
                self.logger.warning("Resource busy. Another benchmark is currently running.")
                return False
            # Mark this task as the current one.
            self.scheduler.current_task_id = task_id
            self.scheduler.task_status[task_id] = "Running"

        # Start the benchmark in a separate thread to avoid blocking.
        thread = threading.Thread(
            target=self._run_task,
            args=(task_id, ps, qs, n_value, nb, instances_num),
            daemon=True
        )
        thread.start()
        self.logger.info(f"Task {task_id} has been submitted.")
        return True

    def _run_task(self, task_id: str, ps: int, qs: int, n_value: int, nb: int, instances_num: int):
        """
        Wrapper to run the scheduler's benchmark execution and handle completion.
        """
        try:
            self.scheduler.run_hpl_benchmark(task_id, ps, qs, n_value, nb, instances_num)
        except Exception as e:
            self.logger.error(f"Error while executing task {task_id}: {e}")
        finally:
            # Ensure the scheduler clears the current task regardless of outcome.
            with self.scheduler.status_lock:
                self.scheduler.current_task_id = None
