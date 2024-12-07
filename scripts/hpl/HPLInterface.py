from pathlib import Path
from typing import Optional, List

from hpl.HPLConfig import HPLConfig
from hpl.HPLInstance import HPLInstance


class HPLInterface:
    """
    Interface to manage HPL benchmark tasks, including configuration generation, installation, and execution.
    """

    def __init__(self, config_output_dir: str = "Configurations"):
        """
        Initialize the HPLInterface.

        Args:
            config_output_dir (str): Directory to save generated HPL configurations.
        """
        self.config_output_dir = config_output_dir
        self.hpl_config = HPLConfig(output_dir=self.config_output_dir)
        print("HPLInterface initialized.")

    def generate_hpl_configs(self, cooperative: bool = True, competitive: bool = True):
        """
        Generate HPL configurations for benchmarking.

        Args:
            cooperative (bool): Generate cooperative benchmark configurations.
            competitive (bool): Generate competitive benchmark configurations.
        """
        print("Generating HPL configurations...")
        if cooperative:
            self.hpl_config.create_cooperative_configs()
        if competitive:
            self.hpl_config.create_competitive_configs()
        print(f"HPL configurations generated in {self.config_output_dir}.")

    def setup_hpl_instance(
        self, instance_type: str, config_path: str, cpu_count: int, instance_id: int
    ) -> HPLInstance:
        """
        Set up an HPL instance.

        Args:
            instance_type (str): Type of the HPL instance ('cooperative' or 'competitive').
            config_path (str): Path to the HPL configuration file.
            cpu_count (int): Number of processes to use for the benchmark.
            instance_id (int): Unique identifier for the instance.

        Returns:
            HPLInstance: Configured HPLInstance object.
        """
        try:
            instance = HPLInstance(
                instance_type=instance_type,
                config_path=config_path,
                process_count=cpu_count,
                instance_id=instance_id,
            )
            return instance
        except Exception as e:
            raise

    def launch_hpl_instance(self, instance: HPLInstance):
        """
        Launch an HPL instance.

        Args:
            instance (HPLInstance): The HPLInstance object to run.
        """
        print(f"Launching HPL instance with ID {instance.instance_id}...")
        try:
            instance.run()
            print(f"HPL instance {instance.instance_id} launched successfully.")
        except RuntimeError as e:
            raise

    def get_hpl_config(self, config_type: str, cpu_count: int) -> List[str]:
        """
        Retrieve the configuration file paths based on the specified type and CPU count.

        Args:
            config_type (str): Type of configuration ('cooperative' or 'competitive').
            cpu_count (int): Number of CPUs for the configuration.

        Returns:
            List[str]: List of configuration file paths. Empty list if no configurations found.
        """
        print(
            f"Retrieving HPL configurations for type '{config_type}' and CPU count {cpu_count}..."
        )
        try:
            config_paths = self.hpl_config.get_config_paths(config_type, cpu_count)
            if config_paths:
                print(
                    f"Found {len(config_paths)} configuration(s) for type '{config_type}' with {cpu_count} CPUs."
                )
            else:
                print(
                    f"No configurations found for type '{config_type}' with {cpu_count} CPUs."
                )
            return config_paths
        except Exception as e:
            print(f"Error retrieving HPL configurations: {e}")
            return []
