import threading
from typing import Optional
from typing import Dict

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

    def _submit_task(self, task_id: str, scheduler_method, *args) -> bool:
        """
        Generic method to submit any HPL benchmark task, ensuring only one task runs at a time.
        """
        # Lock to ensure only one task at a time
        with self.scheduler.status_lock:
            if self.scheduler.current_task_id is not None:
                self.logger.warning("Resource busy. Another benchmark is currently running.")
                return False
            # Mark this task as the current one
            self.scheduler.current_task_id = task_id
            self.scheduler.task_status[task_id] = "Running"

        def _run_task_wrapper():
            try:
                scheduler_method(task_id, *args)
            except Exception as e:
                self.logger.error(f"Error while executing task {task_id}: {e}")
            finally:
                # Clear the current task after completion
                with self.scheduler.status_lock:
                    self.scheduler.current_task_id = None

        # Start the benchmark in a separate thread
        thread = threading.Thread(target=_run_task_wrapper, daemon=True)
        thread.start()

        self.logger.info(f"Task {task_id} has been submitted.")
        return True

    def submit_competitive_hpl_task(
        self,
        task_id: str,
        ps: int,
        qs: int,
        n_value: int,
        nb: int,
        instances_num: int
    ) -> bool:
        """
        Submits a Competitive HPL benchmark using the unified _submit_task.
        """
        return self._submit_task(
            task_id,
            self.scheduler.run_competitive_hpl_benchmark,
            ps,
            qs,
            n_value,
            nb,
            instances_num
        )

    def submit_cooperative_hpl_task(
        self,
        task_id: str,
        ps: int,
        qs: int,
        n_value: int,
        nb: int,
        node_slots: Dict[str, int]
    ) -> bool:
        """
        Submits a Cooperative HPL benchmark using the unified _submit_task.
        """
        return self._submit_task(
            task_id,
            self.scheduler.run_cooperative_hpl_benchmark,
            ps,
            qs,
            n_value,
            nb,
            node_slots
        )
