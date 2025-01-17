# hpl/HPLInstance.py

import os
import math
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from log.LogInterface import LogInterface  # Import LogInterface


class HPLInstance:
    """
    Represents an HPL benchmark instance, handling its setup and execution.
    """

    DEFAULT_HPL_BINARY = "/usr/local/hpl/bin/xhpl"  # Path to HPL binary

    def __init__(
        self,
        config_path: Path,
        result_dir: Path,
        process_count: int,
        instance_id: str,  # Unique per instance
        log_interface: LogInterface,  # Add LogInterface as a parameter
        custom_files: Optional[Path] = None,
        custom_params: str = "",
    ):
        """
        Initialize an HPL instance.

        Args:
            config_path (Path): Path to the HPL configuration file (HPL.dat).
            result_dir (Path): Directory to save the result files.
            process_count (int): Number of processes to run with mpirun.
            instance_id (str): Unique identifier for the HPL instance.
            log_interface (LogInterface): Logging interface instance.
        """
        self.config_path = config_path
        self.result_dir = result_dir
        self.process_count = process_count
        self.instance_id = instance_id
        self.custom_files = custom_files
        self.custom_params = custom_params

        self.result_file = (
            self.result_dir / f"hpl_{self.process_count}_{self.instance_id}.result"
        )
        self.working_dir = Path(f"/tmp/hpl_instance/{self.instance_id}")
        self.hpl_binary = Path(self.DEFAULT_HPL_BINARY)

        self.logger = log_interface  # Use LogInterface for logging
        self.logger.info(f"Initializing HPL instance ID {self.instance_id}")

        self._prepare_environment()

    def _prepare_environment(self):
        """
        Prepare the working environment for HPL execution.
        """
        if self.working_dir.exists():
            self.logger.warning(
                f"Working directory already exists for instance ID {self.instance_id}. Cleaning up."
            )
            shutil.rmtree(self.working_dir, ignore_errors=True)

        self.logger.info(f"Creating working directory at {self.working_dir}")
        self.working_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.hpl_binary, self.working_dir)
        shutil.copy(self.config_path, self.working_dir / "HPL.dat")
        # For each custom file, copy it to the working directory
        if self.custom_files:
            for file in self.custom_files:
                shutil.copy(file, self.working_dir)

    def run_command(self) -> str:
        """
        Generate the command to execute the HPL benchmark.

        Returns:
            str: The command to run the HPL benchmark.
        """

        hpl_command = f"mpirun --bind-to socket --allow-run-as-root -np {self.process_count} {self.custom_params} {self.hpl_binary}"
        
        self.logger.info(f"HPL command: {hpl_command}")
        return hpl_command

    def run(self):
        """
        Execute the HPL benchmark and save the output to a result file.
        """
        try:
            self.logger.info(
                f"Starting HPL execution for instance ID {self.instance_id}"
            )
            cmd = self.run_command()
            with open(self.result_file, "w") as result:
                subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    cwd=self.working_dir,
                    stdout=result,
                    stderr=subprocess.STDOUT,
                )
            self.logger.info(
                f"HPL execution completed. Results saved to {self.result_file}"
            )
        except subprocess.CalledProcessError as e:
            self.logger.error(
                f"HPL execution failed for instance ID {self.instance_id}: {e}"
            )
            raise  # Re-raise exception to be handled by Scheduler
        finally:
            self._cleanup_environment()

    def _cleanup_environment(self):
        """
        Clean up the working environment after execution.
        """
        self.logger.info(f"Cleaning up working directory: {self.working_dir}")
        shutil.rmtree(self.working_dir, ignore_errors=True)
