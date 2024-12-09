# scheduler.py

import sys
from pathlib import Path
from multiprocessing import Process

from hpl.HPLConfig import HPLConfig
from hpl.HPLInstance import HPLInstance
from collectl.CollectlInterface import CollectlInterface
from log.LogInterface import LogInterface


class Scheduler:
    """
    Scheduler class responsible for:
    - Installing dependencies (HPL, Collectl).
    - Setting up the environment (generating HPL configs).
    - Running HPL instances (either cooperative or competitive).
    """

    RESULT_DIR = Path("../results")

    def __init__(self, config_output_dir: str = "../HPLConfigurations"):
        """
        Initialize the Scheduler.

        Args:
            config_output_dir (str): Directory to save generated HPL configurations.
        """
        self.config_output_dir = config_output_dir
        self.hpl_config = HPLConfig(output_dir=self.config_output_dir)
        self.collectl_interface = CollectlInterface()
        self.log_interface = LogInterface(verbose=True)

        self.log_interface.info("Scheduler initialized.")

    def install_dependencies(self):
        """
        Install all required dependencies: HPL and Collectl.
        If any installation fails, the script exits with code 1.
        """
        try:
            self.log_interface.info("Starting dependency installation...")
            self.hpl_config.install_hpl()
            self.collectl_interface.install_collectl()
            self.log_interface.info("Dependencies installed successfully.")
        except Exception as e:
            self.log_interface.error(f"Failed to install dependencies: {e}")
            sys.exit(1)

    def setup_environment(self):
        """
        Set up the environment by generating both cooperative and competitive HPL configurations.
        If setup fails, the script exits with code 1.
        """
        try:
            self.log_interface.info("Generating HPL configurations...")
            self.hpl_config.generate_configs()
            self.log_interface.info("Environment setup completed.")
        except Exception as e:
            self.log_interface.error(f"Failed to set up environment: {e}")
            sys.exit(1)

    def handle_hpl_instance(self, instance_type: str, cpu_count: int, instance_id: int):
        """
        Handle an HPL instance by setting it up, running it, and collecting performance data.

        Args:
            instance_type (str): Type of configuration to use (cooperative or competitive).
            config_type (str): Type of configuration to use (cooperative or competitive).
            cpu_count (int): Number of CPUs to use for the benchmark.
            instance_id (int): Unique identifier for the instance.

        Algorithm:
        1. Get the HPL configuration file for the configuration type and CPU count.
        2. Set up the process to run the HPL instance.
        3. Launch the HPL instance.
        4. Wait for the HPL instance to finish.
        """

        # Ensure the result directory exists
        instance_result_dir = self.RESULT_DIR / str(instance_id)
        instance_result_dir.mkdir(parents=True, exist_ok=True)

        # Get the HPL configuration file for the configuration type and CPU count
        configurations = self.hpl_config.get_config_paths(instance_type, cpu_count)
        if not configurations:
            self.log_interface.error(
                f"No configurations found for {instance_type} and {cpu_count} CPUs."
            )
            return

        # Set up the HPL instance
        instances = []
        for config_path in configurations:
            instance = HPLInstance(
                instance_type=instance_type,
                config_path=config_path,
                result_dir=instance_result_dir,
                process_count=cpu_count,
                instance_id=len(instances),
            )
            instances.append(instance)

        # Run the collectl monitoring tool
        self.collectl_interface.start_collectl(
            instance_id, instance_result_dir / "collectl.log"
        )

        # Run each HPL instance
        processes = []
        for instance in instances:
            process = Process(target=instance.run)
            process.start()
            processes.append(process)

        # Wait for all processes to finish
        for process in processes:
            process.join()

        # Stop the collectl monitoring tool
        self.collectl_interface.stop_collectl(instance_id)
