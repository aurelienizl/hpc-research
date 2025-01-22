import datetime
from typing import Optional

class LogInterface:
    """
    A Python class to interact with the Log.sh shell script for logging.
    Uses a simple logging format that can be parsed by many external tools.
    """

    def __init__(self, verbose: bool = False, log_file: Optional[str] = None):
        """
        Initializes the LogInterface with verbosity control and log file configuration.

        Args:
            verbose (bool): If True, logs are displayed in real-time.
            log_file (str): Optional log file name. Defaults to 'log.txt'.
        """
        self.verbose = verbose
        self.log_file = log_file or "log.txt"

    def log(self, level: str, message: str):
        """
        Logs a message.

        Args:
            level (str): Log level ('info', 'warning', 'error', 'critical').
            message (str): Log message.
        """
        # Create a timestamp in ISO 8601 format (e.g. 2025-01-16T10:45:00)
        timestamp = datetime.datetime.now().isoformat()

        # Use a common log format: timestamp, level, and message
        log_line = f"{timestamp} [{level.upper()}] - {message}\n"

        # Write the log line to the specified file
        with open(self.log_file, "a") as lf:
            lf.write(log_line)

        # Print to console if verbose is True
        if self.verbose:
            print(log_line, end="")

    def info(self, message: str):
        """Logs an info-level message."""
        self.log("info", message)

    def warning(self, message: str):
        """Logs a warning-level message."""
        self.log("warning", message)

    def error(self, message: str):
        """Logs an error-level message."""
        self.log("error", message)

    def critical(self, message: str):
        """Logs a critical-level message."""
        self.log("critical", message)
