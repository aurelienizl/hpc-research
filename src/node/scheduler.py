# scheduler.py

import sys
from pathlib import Path
from typing import Optional, Dict
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

    def __init__(self, log_interface: LogInterface):
        """
        Initialize the Scheduler.
        """
        self.hpl_config = HPLConfig()
        self.collectl_interface = CollectlInterface(log_interface)  # Pass LogInterface
        self.log_interface = log_interface

        # Single task tracking
        self.current_task_id: Optional[str] = None
        self.task_status: Dict[str, str] = {}
        self.status_lock = Lock()

    def run_cooperative_hpl_benchmark(
        self,
        instance_id: str,
        ps: int,
        qs: int,
        n_value: int,
        nb: int,
        # Dictionary of node IP addresses and slots
        node_slots: Dict[str, int],
    ):
        """
        Set up and execute a cooperative HPL instance.
        
        Args:
            instance_id (str): Unique identifier for the task.
            ps (int): Process grid P.
            qs (int): Process grid Q.
            n_value (int): Problem size N.
            nb (int): Block size.
            node_slots (Dict[str, int]): Dictionary of node IP addresses and slots.
        """

        with self.status_lock:
            self.task_status[instance_id] = "Running"

        self.RESULT_DIR.mkdir(parents=True, exist_ok=True)
        task_result_dir = self.RESULT_DIR / instance_id
        task_result_dir.mkdir(parents=True, exist_ok=True)

        try:
            config_path = self.hpl_config.generate_hpl_config(
                n=n_value, nb=nb, p=ps, q=qs
            )
            hosts_path = self.hpl_config.generate_hosts_file(node_slots)
        except ValueError as ve:
            self.log_interface.error(f"Configuration error: {str(ve)}")
            with self.status_lock:
                self.task_status[instance_id] = "Configuration Error"
                self.current_task_id = None
            return
        
        hpl_instance = HPLInstance(
            config_path=config_path,
            result_dir=task_result_dir,
            process_count=ps * qs,
            instance_id=instance_id,
            log_interface=self.log_interface,
            custom_files=[hosts_path],
            custom_params=f"-hostfile hosts.txt --mca plm_rsh_agent \"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null\"",
        )

        collectl_log_path = task_result_dir / "collectl.log"
        self.collectl_interface.start_collectl(instance_id, collectl_log_path)

        process = Process(target=self._run_instance, args=(hpl_instance, instance_id))
        process.start()
        process.join()

        self.collectl_interface.stop_collectl(instance_id)

        with self.status_lock:
            self.task_status[instance_id] = "Completed"
            self.current_task_id = None

        self.log_interface.info(f"Task {instance_id} has been completed.")

    def run_competitive_hpl_benchmark(
        self,
        instance_id: str,
        ps: int,
        qs: int,
        n_value: int,
        nb: int,
        instances_num: int,
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
        # Assume Worker has set current_task_id. Just update status.
            self.task_status[instance_id] = "Running"

        self.RESULT_DIR.mkdir(parents=True, exist_ok=True)
        task_result_dir = self.RESULT_DIR / instance_id
        task_result_dir.mkdir(parents=True, exist_ok=True)

        try:
            config_path = self.hpl_config.generate_hpl_config(
                n=n_value, nb=nb, p=ps, q=qs
            )
        except ValueError as ve:
            self.log_interface.error(f"Configuration error: {str(ve)}")
            with self.status_lock:
                self.task_status[instance_id] = "Configuration Error"
                self.current_task_id = None
            return

        hpl_instances = []
        for i in range(1, instances_num + 1):
            unique_instance_id = f"{instance_id}_{i}"
            hpl_instance = HPLInstance(
                config_path=config_path,
                result_dir=task_result_dir,
                process_count=ps * qs,
                instance_id=unique_instance_id,  # Unique instance_id
                log_interface=self.log_interface,  # Pass LogInterface
                custom_files=None,
                custom_params=f"--bind-to socket",
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

        self.log_interface.info(f"Task {instance_id} has been completed.")

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
            self.log_interface.error(
                f"Execution error for instance {instance_id}: {str(e)}"
            )
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
        self.log_interface.info("Shutting down the scheduler.")
        # Implement any necessary cleanup here
