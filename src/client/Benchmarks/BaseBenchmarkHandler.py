import subprocess
import shutil
import uuid

from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional
from Log.LogInterface import LogInterface

class BaseBenchmarkHandler(ABC):
    """
    Abstract base class for benchmark handlers.
    """

    def __init__(self, commandLine: str, task_id: str, logger: LogInterface):
        self.commandLine = commandLine
        self.task_id = task_id
        self.logger = logger
        self.instance_id = uuid.uuid4().hex[:8]
        self.working_dir = self.get_working_directory()

    @abstractmethod
    def get_working_directory(self) -> Path:
        """
        Return the working directory based on the task_id.
        """
        pass

    @abstractmethod
    def prepare_command_line(self):
        """
        Prepare the command line.
        Default implementation: no modifications.
        """
        pass

    def prepare_environment(self):
        """
        Prepare the working environment.
        """
        self.logger.info("Preparing environment")
        self.working_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_environment(self):
        """
        Cleanup the working environment.
        """
        self.logger.info("Cleaning up environment")
        try:
            shutil.rmtree(self.working_dir)
        except Exception as e:
            self.logger.error(f"Error cleaning up environment: {e}")

    def retrieve_data(self):
        """
        Retrieve files from the working directory.
        """
        self.logger.info("Retrieving data")
        try:
            result = list(self.working_dir.iterdir())
            self.logger.info(f"Retrieved files: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error retrieving data: {e}")
            return None

    def run(self) -> Optional[subprocess.Popen]:
        """
        Run the benchmark instance non-blocking.
        """
        self.logger.info(f"Running instance with command: {self.commandLine}")
        try:
            process = subprocess.Popen(
                self.commandLine.split(),
                cwd=self.working_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return process
        except Exception as e:
            self.logger.error(f"Error running instance: {e}")
            return None

    def wait(self, process: subprocess.Popen) -> Optional[int]:
        """
        Wait for the benchmark process to complete.
        """
        try:
            process.wait()
            return process.returncode
        except Exception as e:
            self.logger.error(f"Error waiting for process: {e}")
            return None

    def kill(self, process: subprocess.Popen) -> Optional[int]:
        """
        Kill the running benchmark process.
        """
        try:
            process.kill()
            return process.returncode
        except Exception as e:
            self.logger.error(f"Error killing process: {e}")
            return None
