from pathlib import Path
from Benchmarks.BaseBenchmarkHandler import BaseBenchmarkHandler


class NETPipeHandler(BaseBenchmarkHandler):
    """
    Handler for the NETPipe benchmark.
    """

    def get_working_directory(self) -> Path:
        result = Path(f"/tmp/netpipe_instance/{self.task_id}/{self.instance_id}")
        self.logger.info(f"NETPipe working directory: {result}")
        return result

    def prepare_command_line(self):
        self.logger.info("Preparing command line for NETPipe")
        self.commandLine = "mpirun " + self.commandLine + " NPmpi"
