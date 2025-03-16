import shutil

from pathlib import Path
from Benchmarks.HPL.HPLConfig import HPLConfig
from Benchmarks.BaseBenchmarkHandler import BaseBenchmarkHandler
from Log.LogInterface import LogInterface

class HPLHandler(BaseBenchmarkHandler):
    """
    Handler for the HPL benchmark.
    """
    
    def get_working_directory(self) -> Path:
        result =  Path(f"/tmp/hpl_instance/{self.task_id}/{self.instance_id}")
        self.logger.info(f"HPL working directory: {result}")
        return result

    def prepare_environment(self, n, nb, p, q):
        """
        Prepare environment and move the HPL configuration file.
        """
        self.logger.info("Generating HPL configuration file")
        # Generate the HPL configuration file.
        config = HPLConfig(n, nb, p, q)
        config.write_config(f"{self.instance_id}HPL.dat")

        # Call the base method to create the working directory.
        super().prepare_environment()
        self.logger.info("Moving configuration file for HPL")
        try:
            shutil.move(f"{self.instance_id}HPL.dat", self.working_dir / "HPL.dat")
        except Exception as e:
            self.logger.error(f"Error moving config file: {e}")

    def prepare_command_line(self):
        self.logger.info("Preparing command line for HPL")
        self.commandLine = "mpirun " + self.commandLine + " xhpl"
