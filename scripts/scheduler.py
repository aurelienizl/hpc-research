# scheduler.py

import sys
import subprocess
from pathlib import Path
from typing import Tuple, Optional
import logging
from multiprocessing import Process

from hpl.HPLConfig import HPLConfig
from hpl.HPLInstance import HPLInstance
from collectl.CollectlInterface import CollectlInterface
from log.LogInterface import LogInterface


class Scheduler:
    """
    Responsible for installing dependencies, setting up environments,
    and executing HPL instances in both cooperative and competitive modes.
    """

    RESULT_DIR = Path("../results")

    def __init__(self, config_output_dir: str = "../HPLConfigurations"):
        """
        Initialize the Scheduler.

        Args:
            config_output_dir (str): Directory to save generated HPL configurations.
        """
        self.config_output_dir = Path(config_output_dir)
        self.hpl_config = HPLConfig(output_dir=self.config_output_dir)
        self.collectl_interface = CollectlInterface()
        self.log_interface = LogInterface(verbose=True)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Scheduler initialized.")

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

    def handle_hpl_instance(
        self,
        instance_type: str,
        cpu_count: int,
        memory_usage: Optional[int],
        instance_id: int,
    ):
        """
        Set up and execute an HPL instance.

        Args:
            instance_type (str): Type of configuration ('cooperative' or 'competitive').
            cpu_count (int): Number of CPUs to allocate.
            memory_usage (Optional[int]): Memory usage in MB.
            instance_id (int): Unique identifier for the instance.
        """
        self.RESULT_DIR.mkdir(parents=True, exist_ok=True)
        instance_result_dir = self.RESULT_DIR / str(instance_id)
        instance_result_dir.mkdir(parents=True, exist_ok=True)

        comp_mode = instance_type.lower() == "competitive"
        ram_percent = (
            memory_usage if memory_usage else HPLConfig.DEFAULT_RAM_USAGE_PERCENT
        )

        try:
            config_path, num_instances = self.hpl_config.get_config(
                cpu_count=cpu_count, ram_percent=ram_percent, competitive=comp_mode
            )
        except ValueError as ve:
            self.logger.error(f"Configuration error: {ve}")
            return

        if not config_path:
            self.logger.error(
                f"No configuration generated for {instance_type} with {cpu_count} CPUs."
            )
            return

        # Initialize HPL instances
        hpl_instances = [
            HPLInstance(
                instance_type=instance_type,
                config_path=config_path,
                result_dir=instance_result_dir,
                process_count=cpu_count,
                instance_id=i,
            )
            for i in range(num_instances)
        ]

        # Start Collectl monitoring
        collectl_log_path = instance_result_dir / "collectl.log"
        self.collectl_interface.start_collectl(instance_id, collectl_log_path)

        # Execute HPL instances using multiprocessing.Process
        processes = []
        for instance in hpl_instances:
            process = Process(target=instance.run)
            process.start()
            processes.append(process)

        # Wait for all processes to complete
        for process in processes:
            process.join()

        # Stop Collectl monitoring
        self.collectl_interface.stop_collectl(instance_id)

        self.logger.info(
            f"HPL instances for {instance_type} with {cpu_count} CPUs have completed."
        )

    def handle_custom_hpl_instance(
        self, instance_id: int, ps: int, qs: int, n_value: int, nb: int, comp: bool
    ):
        """
        Set up and execute a custom HPL instance.

        Args:
            instance_id (int): Unique identifier for the instance.
            ps (int): Process grid P.
            qs (int): Process grid Q.
            n_value (int): Problem size N.
            nb (int): Block size.
            comp (bool): Competitive mode flag.
        """
        self.RESULT_DIR.mkdir(parents=True, exist_ok=True)
        instance_result_dir = self.RESULT_DIR / str(instance_id)
        instance_result_dir.mkdir(parents=True, exist_ok=True)

        try:
            config_path, num_instances = self.hpl_config.get_custom_config(
                n=n_value, nb=nb, p=ps, q=qs, competitive=comp
            )
        except ValueError as ve:
            self.logger.error(f"Custom configuration error: {ve}")
            return

        hpl_instances = [
            HPLInstance(
                instance_type="custom",
                config_path=config_path,
                result_dir=instance_result_dir,
                process_count=ps * qs,
                instance_id=i,
            )
            for i in range(num_instances)
        ]

        collectl_log_path = instance_result_dir / "collectl.log"
        self.collectl_interface.start_collectl(instance_id, collectl_log_path)

        # Execute HPL instances using multiprocessing.Process
        processes = []
        for instance in hpl_instances:
            process = Process(target=instance.run)
            process.start()
            processes.append(process)

        # Wait for all processes to complete
        for process in processes:
            process.join()

        # Stop Collectl monitoring
        self.collectl_interface.stop_collectl(instance_id)

        self.logger.info(
            f"Custom HPL instances with N={n_value}, P={ps}, Q={qs} have completed."
        )
