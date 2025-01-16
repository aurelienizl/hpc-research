# collectl/CollectlInterface.py

import subprocess
import os
from typing import Optional
from log.LogInterface import LogInterface  # Import LogInterface


class CollectlInterface:

    SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "CollectlManager.sh")

    def __init__(self, log_interface: LogInterface):
        self.log_interface = log_interface
        self.log_interface.info("CollectlManager initialized.")

    def _run_command(
        self, command: str, timeout: int = 60
    ) -> subprocess.CompletedProcess:
        """
        Helper method to run shell commands and handle errors.
        """
        try:
            self.log_interface.info(f"Running command: {command}")
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            result.check_returncode()
            return result
        except subprocess.CalledProcessError as e:
            self.log_interface.error(f"Command failed: {e.stdout}\n{e.stderr}")
            raise RuntimeError(f"Command failed with error: \n{e.stdout}\n{e.stderr}")
        except subprocess.TimeoutExpired:
            self.log_interface.error(f"Command timed out: {command}")
            raise TimeoutError("The command timed out.")

    def start_collectl(
        self,
        id: str,
        output_file: Optional[str] = None,
        custom_command: Optional[str] = None,
    ) -> str:
        """
        Start Collectl with a unique ID and optional custom command.
        """
        if not id:
            self.log_interface.error("ID is required to start Collectl.")
            raise ValueError("ID is required to start Collectl.")

        command = f"{CollectlInterface.SCRIPT_PATH} start -id {id}"
        if output_file:
            command += f" -o {output_file}"
        if custom_command:
            command += f" -cmd '{custom_command}'"

        try:
            self.log_interface.info(f"Starting Collectl with ID: {id}")
            result = self._run_command(command)
            self.log_interface.info(f"Collectl started with ID: {id}")
            return result.stdout
        except Exception as e:
            self.log_interface.error(f"Failed to start Collectl with ID {id}: {e}")
            return str(e)

    def stop_collectl(self, id: str) -> str:
        """
        Stop Collectl using a unique ID.
        """
        if not id:
            self.log_interface.error("ID is required to stop Collectl.")
            raise ValueError("ID is required to stop Collectl.")

        command = f"{CollectlInterface.SCRIPT_PATH} stop -id {id}"
        try:
            self.log_interface.info(f"Stopping Collectl with ID: {id}")
            result = self._run_command(command)
            self.log_interface.info(f"Collectl stopped with ID: {id}")
            return result.stdout
        except Exception as e:
            self.log_interface.error(f"Failed to stop Collectl with ID {id}: {e}")
            return str(e)

    def is_collectl_running(self, id: str) -> bool:
        """
        Check if Collectl is running with a given ID.
        """
        pid_file = os.path.join("/tmp/collectl_pids", f"{id}.pid")
        if os.path.exists(pid_file):
            with open(pid_file, "r") as file:
                pid = int(file.read().strip())
                running = os.path.exists(f"/proc/{pid}")
                if running:
                    self.log_interface.info(f"Collectl is running with ID: {id}")
                else:
                    self.log_interface.info(f"Collectl is not running with ID: {id}")
                return running
        self.log_interface.info(f"PID file not found for ID: {id}")
        return False
