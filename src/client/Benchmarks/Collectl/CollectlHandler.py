from pathlib import Path
from Benchmarks.BaseBenchmarkHandler import BaseBenchmarkHandler
from Log.LogInterface import LogInterface


class CollectlHandler(BaseBenchmarkHandler):
    """
    Handler for the Collectl benchmark.
    Requires the '-P -oz -f output_file' options to be passed in the command line.
    """

    def get_working_directory(self) -> Path:
        result = Path(f"/tmp/collectl_instance/{self.task_id}/{self.instance_id}")
        self.logger.info(f"Collectl working directory: {result}")
        return result

    def prepare_command_line(self):
        self.logger.info("Preparing command line for Collectl")
        self.commandLine = "collectl " + self.commandLine
