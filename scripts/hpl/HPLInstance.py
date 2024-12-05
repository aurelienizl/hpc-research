import os
import shutil
from pathlib import Path
import subprocess


class HPLInstance:
    """
    A class to execute HPL benchmarks, with support for multiple instances.
    Each instance is assigned a unique identifier to ensure separate directories.
    """

    _active_instances = set()

    def __init__(self, config_path: str, process_count: int, instance_id: int):
        """
        Initialize an HPL instance with a unique identifier.

        Args:
            config_path (str): Path to the HPL configuration file (HPL.dat).
            process_count (int): Number of processes to run with mpirun.
            instance_id (int): Unique identifier for the HPL instance.
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        self.process_count = process_count
        if self.process_count <= 0:
            raise ValueError("Process count must be greater than 0.")

        self.instance_id = instance_id
        self.working_dir = Path(f"/tmp/hpl_instance/{self.instance_id}")
        self.hpl_binary = "/usr/local/hpl/bin/xhpl"  # Path to HPL binary

        if self.instance_id in HPLInstance._active_instances:
            raise RuntimeError(f"An HPL instance with ID {self.instance_id} is already active.")
        HPLInstance._active_instances.add(self.instance_id)

        print(f"Initializing HPL instance with ID {self.instance_id}")
        self._prepare_environment()

    def _prepare_environment(self):
        """Prepare the environment for HPL execution."""
        if self.working_dir.exists():
            raise RuntimeError(f"Working directory already exists for instance ID {self.instance_id}: {self.working_dir}")

        print(f"Preparing environment for HPL instance. Working directory: {self.working_dir}")
        self.working_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.hpl_binary, self.working_dir)
        shutil.copy(self.config_path, self.working_dir / "HPL.dat")

    def _cleanup_environment(self):
        """Cleanup the working environment."""
        print(f"Cleaning up working directory: {self.working_dir}")
        shutil.rmtree(self.working_dir, ignore_errors=True)
        HPLInstance._active_instances.discard(self.instance_id)

    def run(self):
        """
        Execute the HPL benchmark and save the output to a .result file.

        Raises:
            RuntimeError: If execution fails.
        """
        try:
            # Construct result file path
            result_file = self.config_path.with_suffix(".result")

            # Construct and run the HPL command
            hpl_command = f"mpirun --allow-run-as-root -np {self.process_count} ./xhpl"
            print(f"Executing HPL benchmark. Command: {hpl_command}")
            with open(result_file, "w") as result:
                subprocess.run(hpl_command, shell=True, check=True, cwd=self.working_dir, stdout=result, stderr=result)

            print(f"HPL benchmark completed successfully. Results saved to {result_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error during HPL execution: {e}")
            raise
        finally:
            self._cleanup_environment()
