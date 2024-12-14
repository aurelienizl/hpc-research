# scheduler.py

import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict
import logging
from multiprocessing import Process
from threading import Lock

from hpl.HPLConfig import HPLConfig
from hpl.HPLInstance import HPLInstance
from collectl.CollectlInterface import CollectlInterface
from log.LogInterface import LogInterface


class Scheduler:
    """
    Responsible for installing dependencies, setting up environments,
    and executing HPL instances in single-task mode.
    """

    RESULT_DIR = Path("../results")

    class TaskAlreadyRunningException(Exception):
        """Exception raised when a task is already running."""
        pass

    def __init__(self):
        """
        Initialize the Scheduler.
        """
        self.hpl_config = HPLConfig()
        self.collectl_interface = CollectlInterface()
        self.log_interface = LogInterface()

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Scheduler initialized.")

        # Single task tracking
        self.current_task_id: Optional[str] = None
        self.task_status: Dict[str, str] = {}
        self.status_lock = Lock()

    def install_dependencies(self):
        """
        Install required dependencies: HPL and Collectl.
        Exits the program if installation fails.
        """
        try:
            self.logger.info("Starting dependency installation...")
            self.hpl_config.install_hpl()
            self.collectl_interface.install_collectl()
            self.logger.info("Dependencies installed successfully.")
        except Exception as e:
            self.logger.error(f"Failed to install dependencies: {e}")
            sys.exit(1)

    def setup_environment(self):
        """
        Set up the necessary environment for running benchmarks.
        """
        # Placeholder for environment setup logic
        self.logger.info("Environment setup completed.")

    def run_hpl_benchmark(
        self, instance_id: str, ps: int, qs: int, n_value: int, nb: int, instances_num: int
    ):
        """
        Set up and execute a custom HPL instance.

        Args:
            instance_id (str): Unique identifier for the task.
            ps (int): Process grid P.
            qs (int): Process grid Q.
            n_value (int): Problem size N.
            nb (int): Block size.
            instances_num (int): Number of HPL instances to run.
        """
        with self.status_lock:
            if self.current_task_id is not None:
                raise Scheduler.TaskAlreadyRunningException("Another task is currently running.")
            self.current_task_id = instance_id
            self.task_status[instance_id] = "Running"

        self.RESULT_DIR.mkdir(parents=True, exist_ok=True)
        task_result_dir = self.RESULT_DIR / instance_id
        task_result_dir.mkdir(parents=True, exist_ok=True)

        try:
            config_path = self.hpl_config.generate_hpl_config(
                n=n_value, nb=nb, p=ps, q=qs
            )
        except ValueError as ve:
            self.logger.error(f"Custom configuration error: {ve}")
            with self.status_lock:
                self.task_status[instance_id] = "Configuration Error"
                self.current_task_id = None
            return

        hpl_instances = []
        for i in range(1, instances_num + 1):
            unique_instance_id = f"{instance_id}_{i}"
            hpl_instance = HPLInstance(
                instance_type="custom",
                config_path=config_path,
                result_dir=task_result_dir,
                process_count=ps * qs,
                instance_id=unique_instance_id,  # Unique instance_id
            )
            hpl_instances.append(hpl_instance)

        collectl_log_path = task_result_dir / "collectl.log"
        self.collectl_interface.start_collectl(instance_id, collectl_log_path)

        # Execute HPL instances using multiprocessing.Process
        processes = []
        for instance in hpl_instances:
            process = Process(target=self._run_instance, args=(instance, instance_id))
            process.start()
            processes.append(process)

        # Wait for all processes to complete
        for process in processes:
            process.join()

        # Stop Collectl monitoring
        self.collectl_interface.stop_collectl(instance_id)

        # Update task status
        with self.status_lock:
            self.task_status[instance_id] = "Completed"
            self.current_task_id = None

        self.logger.info(
            f"Custom HPL instance with Task ID {instance_id} has completed."
        )

    def _run_instance(self, instance: HPLInstance, instance_id: str):
        """
        Wrapper to run an HPLInstance and handle exceptions.

        Args:
            instance (HPLInstance): The HPLInstance to run.
            instance_id (str): The associated task ID.
        """
        try:
            instance.run()
        except Exception as e:
            self.logger.error(f"Instance {instance.instance_id} failed: {str(e)}")
            with self.status_lock:
                self.task_status[instance_id] = "Execution Error"
                self.current_task_id = None

    def get_task_status(self, task_id: str) -> Optional[str]:
        """
        Retrieve the status of a specific task.

        Args:
            task_id (str): The unique identifier of the task.

        Returns:
            Optional[str]: The status of the task, or None if not found.
        """
        with self.status_lock:
            return self.task_status.get(task_id, None)

    def shutdown(self):
        """
        Gracefully shut down the scheduler.
        """
        self.logger.info("Shutting down Scheduler...")
        # Implement any necessary cleanup here
