# scheduler.py

import sys
from pathlib import Path
from multiprocessing import Process
from typing import Dict, Optional

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
        # TODO
        """
        self.log_interface.info("Environment setup completed.")


    def handle_hpl_instance(self, instance_type: str, cpu_count: int, instance_id: int):
        """
        Handle an HPL instance by setting it up, running it, and collecting performance data.

        Args:
            instance_type (str): Type of configuration to use ('cooperative' or 'competitive').
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

        # Determine competitive mode based on instance_type
        comp = instance_type.lower() == "competitive"

        try:
            if comp:
                # For competitive mode, assume ram_percent is set to 85%
                config_path, num_instances = self.hpl_config.get_config_by_cpu_comp(
                    cpu_count=cpu_count,
                    comp=True
                )
            else:
                # For cooperative mode, assume ram_percent is set to 85%
                config_path, num_instances = self.hpl_config.get_config_by_cpu_comp(
                    cpu_count=cpu_count,
                    comp=False
                )
        except ValueError as ve:
            self.log_interface.error(f"Invalid configuration parameters: {ve}")
            return

        if not config_path:
            self.log_interface.error(
                f"No configuration file generated for {instance_type} with {cpu_count} CPUs."
            )
            return

        # Set up the HPL instance(s)
        instances = []
        for i in range(num_instances):
            instance = HPLInstance(
                instance_type=instance_type,
                config_path=config_path,
                result_dir=instance_result_dir,
                process_count=cpu_count,
                instance_id=i + 1  # Assuming instance_id starts at 1
            )
            instances.append(instance)

        # Run the collectl monitoring tool
        collectl_log_path = instance_result_dir / "collectl.log"
        self.collectl_interface.start_collectl(instance_id, collectl_log_path)

        # Run each HPL instance as a separate process
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

        self.log_interface.info(
            f"HPL instances for {instance_type} with {cpu_count} CPUs have completed."
        )

    def handle_custom_hpl_instance(
        self,
        config_name: str,
        cpu_count: int,
        instance_id: int,
        ram_allocation: Optional[int] = None,
        ps: Optional[int] = None,
        qs: Optional[int] = None,
        n_value: Optional[int] = None,
        nb: int = 192,
        custom_params: Optional[Dict[str, str]] = None
    ):
        """
        Handle a custom HPL instance by setting it up, running it, and collecting performance data.

        Args:
            config_name (str): Unique name for the custom configuration.
            cpu_count (int): Number of CPUs to use for the benchmark.
            instance_id (int): Unique identifier for the instance.
            ram_allocation (Optional[int]): RAM allocation in MB. If None, default calculation is used.
            ps (Optional[int]): Process grid P. If None, calculated automatically.
            qs (Optional[int]): Process grid Q. If None, calculated automatically.
            n_value (Optional[int]): Problem size N. If None, calculated based on ram_allocation.
            nb (int): Block size. Default is 192.
            custom_params (Optional[Dict[str, str]]): Additional custom HPL parameters.

        Algorithm:
        1. Create a custom HPL configuration file using the provided parameters.
        2. Set up the process to run the HPL instance.
        3. Launch the HPL instance.
        4. Wait for the HPL instance to finish.
        """

        # Ensure the result directory exists
        instance_result_dir = self.RESULT_DIR / str(instance_id)
        instance_result_dir.mkdir(parents=True, exist_ok=True)

        # Create the custom HPL configuration
        try:
            self.hpl_config.create_custom_config(
                config_name=config_name,
                cpu_count=cpu_count,
                ram_allocation=ram_allocation if ram_allocation else int(self.hpl_config.usable_memory * 0.85),
                ps=ps,
                qs=qs,
                n_value=n_value,
                nb=nb,
                custom_params=custom_params
            )
        except ValueError as ve:
            self.log_interface.error(f"Failed to create custom configuration: {ve}")
            return

        # Retrieve the path to the custom configuration
        custom_configs = self.hpl_config.get_custom_config(config_name)
        if not custom_configs:
            self.log_interface.error(
                f"No custom configuration found with name '{config_name}'."
            )
            return

        config_path = custom_configs[0]
        num_instances = 1  # Assuming custom configurations are single-instance

        # Set up the HPL instance
        instance = HPLInstance(
            instance_type="custom",
            config_path=config_path,
            result_dir=instance_result_dir,
            process_count=cpu_count,
            instance_id=instance_id
        )

        # Run the collectl monitoring tool
        collectl_log_path = instance_result_dir / "collectl.log"
        self.collectl_interface.start_collectl(instance_id, collectl_log_path)

        # Run the HPL instance as a separate process
        process = Process(target=instance.run)
        process.start()
        process.join()

        # Stop the collectl monitoring tool
        self.collectl_interface.stop_collectl(instance_id)

        self.log_interface.info(
            f"Custom HPL instance '{config_name}' with {cpu_count} CPUs has completed."
        )

