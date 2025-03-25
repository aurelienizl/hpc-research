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
        result = Path(f"/tmp/hpl_instance/{self.task_id}/{self.instance_id}")
        self.logger.info(f"HPL working directory: {result}")
        return result

    def prepare_environment(self, params: dict):
        """
        Prepare environment and move the HPL configuration file.
        """
        n = params.get("n")
        nb = params.get("nb")
        p = params.get("p")
        q = params.get("q")
        self.logger.info(
            f"Preparing environment for HPL with parameters: {n}, {nb}, {p}, {q}"
        )
        if not n or not nb or not p or not q:
            self.logger.error("Invalid parameters for HPL")
            return False
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
            return False
        return True

    def prepare_command_line(self):
        self.logger.info("Preparing command line for HPL")
        self.commandLine = "mpirun " + self.commandLine + " xhpl"
