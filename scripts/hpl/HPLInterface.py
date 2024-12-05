import os
import subprocess
from pathlib import Path
from hpl.HPLConfig import HPLConfig
from hpl.HPLInstance import HPLInstance

class HPLInterface:
    """
    Interface to manage HPL benchmark tasks, including configuration generation, installation, and execution.
    """

    SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "HPLInstall.sh")


    def __init__(self, config_output_dir="Configurations"):
        """
        Initialize the HPLInterface.

        Args:
            config_output_dir (str): Directory to save generated HPL configurations.
        """
        self.config_output_dir = config_output_dir
        self.hpl_config = HPLConfig(output_dir=self.config_output_dir)
        print("HPLInterface initialized.")

    @staticmethod
    def install_hpl():
        """
        Install HPL and its dependencies using a script.
        """
        print("Starting HPL installation...")
        if not Path(HPLInterface.SCRIPT_PATH).exists():
            raise FileNotFoundError(f"Installation script not found: {HPLInterface.SCRIPT_PATH}")
        try:
            subprocess.run(["bash", HPLInterface.SCRIPT_PATH], check=True)
            print("HPL installation completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error during HPL installation: {e}")
            raise

    def generate_hpl_configs(self, cooperative=True, competitive=True):
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

    def setup_hpl_instance(self, config_path, process_count, instance_id):
        """
        Set up an HPL instance.

        Args:
            config_path (str): Path to the HPL configuration file.
            process_count (int): Number of processes to use for the benchmark.
            instance_id (int): Unique identifier for the instance.

        Returns:
            HPLInstance: Configured HPLInstance object.
        """
        print(f"Setting up HPL instance with ID {instance_id}...")
        try:
            instance = HPLInstance(config_path=config_path, process_count=process_count, instance_id=instance_id)
            print(f"HPL instance {instance_id} set up successfully.")
            return instance
        except Exception as e:
            print(f"Error setting up HPL instance {instance_id}: {e}")
            raise

    def launch_hpl_instance(self, instance):
        """
        Launch an HPL instance.

        Args:
            instance (HPLInstance): The HPLInstance object to run.
        """
        print(f"Launching HPL instance with ID {instance.instance_id}...")
        try:
            instance.run()
            print(f"HPL instance {instance.instance_id} completed successfully.")
        except RuntimeError as e:
            print(f"Error during HPL benchmark for instance {instance.instance_id}: {e}")
            raise


