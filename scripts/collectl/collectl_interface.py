import subprocess
import os
from typing import Optional
from log.log_interface import ShellLogger  # Import the ShellLogger class from the new location

# Global Variables
SCRIPT_PATH = "collectl/collectl_manager.sh"
PID_DIR = "/tmp/collectl_pids"


class CollectlManager:
    def __init__(self, script_path: str = SCRIPT_PATH, logger: Optional[ShellLogger] = None):
        self.script_path = script_path
        self.logger = logger or ShellLogger()  # Use provided logger or create a default one

    def run_command(self, command: str, timeout: int = 60) -> subprocess.CompletedProcess:
        """
        Helper method to run shell commands and handle errors.
        """
        try:
            self.logger.info(f"Running command: {command}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
            result.check_returncode()
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {e.stdout}\n{e.stderr}")
            raise RuntimeError(f"Command failed with error: \n{e.stdout}\n{e.stderr}")
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {command}")
            raise TimeoutError("The command timed out.")

    def install_collectl(self) -> str:
        """
        Install Collectl using the shell script.
        """
        try:
            self.logger.info("Installing Collectl.")
            result = self.run_command(f"{self.script_path} install", timeout=120)
            self.logger.info("Collectl installation completed.")
            return result.stdout
        except Exception as e:
            self.logger.error(f"Failed to install Collectl: {e}")
            return str(e)

    def start_collectl(self, id: str, output_file: Optional[str] = None, custom_command: Optional[str] = None) -> str:
        """
        Start Collectl with a unique ID and optional custom command.
        """
        if not id:
            self.logger.error("ID is required to start Collectl.")
            raise ValueError("ID is required to start Collectl.")

        command = f"{self.script_path} start -id {id}"
        if output_file:
            command += f" -o {output_file}"
        if custom_command:
            command += f" -cmd '{custom_command}'"

        try:
            self.logger.info(f"Starting Collectl with ID: {id}")
            result = self.run_command(command)
            self.logger.info(f"Collectl started with ID: {id}")
            return result.stdout
        except Exception as e:
            self.logger.error(f"Failed to start Collectl with ID {id}: {e}")
            return str(e)

    def stop_collectl(self, id: str) -> str:
        """
        Stop Collectl using a unique ID.
        """
        if not id:
            self.logger.error("ID is required to stop Collectl.")
            raise ValueError("ID is required to stop Collectl.")

        command = f"{self.script_path} stop -id {id}"
        try:
            self.logger.info(f"Stopping Collectl with ID: {id}")
            result = self.run_command(command)
            self.logger.info(f"Collectl stopped with ID: {id}")
            return result.stdout
        except Exception as e:
            self.logger.error(f"Failed to stop Collectl with ID {id}: {e}")
            return str(e)

    def is_collectl_running(self, id: str) -> bool:
        """
        Check if Collectl is running with a given ID.
        """
        pid_file = os.path.join(PID_DIR, f"{id}.pid")
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as file:
                pid = int(file.read().strip())
                running = os.path.exists(f"/proc/{pid}")
                if running:
                    self.logger.info(f"Collectl is running with ID: {id}")
                else:
                    self.logger.error(f"Collectl is not running with ID: {id}")
                return running
        self.logger.info(f"PID file not found for ID: {id}")
        return False
