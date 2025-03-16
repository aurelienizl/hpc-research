import datetime

from typing import Optional

class LogInterface:
    """
    A Python interface for structured logging operations.
    
    This class provides a standardized way to write logs in a format compatible
    with common log analysis tools. It supports multiple log levels and can
    output to both file and console.

    The log format follows the pattern: 'timestamp [LEVEL] - message'
    where timestamp is in ISO 8601 format.
    """

    def __init__(self, verbose: bool = False, log_file: Optional[str] = None):
        """
        Initialize a new LogInterface instance.

        Parameters:
            verbose (bool): When True, logs are output to console in addition to file.
            log_file (str, optional): Path to the log file. Defaults to 'log.txt'.
        """
        self.verbose = verbose
        self.log_file = log_file or "log.txt"

    def log(self, level: str, message: str):
        """
        Write a log entry with the specified level and message.

        Parameters:
            level (str): The log severity level ('info', 'warning', 'error', 'critical').
            message (str): The message to be logged.

        Note:
            Log entries are always written to file, and to console if verbose=True.
        """
        timestamp = datetime.datetime.now().isoformat()
        log_line = f"{timestamp} [{level.upper()}] - {message}\n"

        with open(self.log_file, "a") as lf:
            lf.write(log_line)

        if self.verbose:
            print(log_line, end="")

    def info(self, message: str):
        """
        Log an informational message.

        Parameters:
            message (str): The information to be logged.
        """
        self.log("info", message)

    def warning(self, message: str):
        """
        Log a warning message.

        Parameters:
            message (str): The warning to be logged.
        """
        self.log("warning", message)

    def error(self, message: str):
        """
        Log an error message.

        Parameters:
            message (str): The error to be logged.
        """
        self.log("error", message)

    def critical(self, message: str):
        """
        Log a critical message.

        Parameters:
            message (str): The critical message to be logged.
        """
        self.log("critical", message)

    def close(self):
        """
        Close the log file.
        """
        self.log("info", "Closing log file...")