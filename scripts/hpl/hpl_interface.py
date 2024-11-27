import os
import shutil
from pathlib import Path
import subprocess


class HPLInstance:
    """
    A simplified class to execute HPL benchmarks.
    """

    def __init__(self, config_path: str, process_count: int):
        """
        Initialize an HPL instance.

        Args:
            config_path (str): Path to the HPL configuration file (HPL.dat).
            process_count (int): Number of processes to run with mpirun.
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        self.process_count = process_count
        if self.process_count <= 0:
            raise ValueError("Process count must be greater than 0.")

        self.working_dir = Path("/tmp/hpl_instance")
        self.hpl_binary = "/usr/local/hpl/bin/xhpl"  # Path to HPL binary

    def _prepare_environment(self):
        """Prepare the environment for HPL execution."""
        print(f"Preparing environment for HPL instance. Working directory: {self.working_dir}")
        self.working_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.hpl_binary, self.working_dir)
        shutil.copy(self.config_path, self.working_dir / "HPL.dat")

    def _cleanup_environment(self):
        """Cleanup the working environment."""
        print(f"Cleaning up working directory: {self.working_dir}")
        shutil.rmtree(self.working_dir, ignore_errors=True)

    def run(self):
        """
        Execute the HPL benchmark.

        Raises:
            RuntimeError: If execution fails.
        """
        try:
            self._prepare_environment()

            # Construct and run the HPL command
            hpl_command = f"mpirun -np {self.process_count} ./xhpl"
            print(f"Executing HPL benchmark. Command: {hpl_command}")
            subprocess.run(hpl_command, shell=True, check=True, cwd=self.working_dir)

            print("HPL benchmark completed successfully.")

        except subprocess.CalledProcessError as e:
            print(f"Error during HPL execution: {e}")
            raise
        finally:
            self._cleanup_environment()
