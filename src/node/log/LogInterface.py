# LogInterface.py

import subprocess
import os
from typing import Optional


class LogInterface:
    """
    A Python class to interact with the Log.sh shell script for logging.
    """

    SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "Log.sh")

    def __init__(self, verbose: bool = False, log_file: Optional[str] = None):
        """
        Initializes the LogInterface with verbosity control and log file configuration.

        Args:
            verbose (bool): If True, logs are displayed in real-time.
            log_file (str): Optional log file name. Defaults to log.txt.
        """
        self.verbose = verbose
        self.log_file = log_file or "log.txt"

    def log(self, level: str, message: str):
        """
        Logs a message using the shell script.

        Args:
            level (str): Log level ('info', 'warning', 'error').
            message (str): Log message.
        """
        valid_levels = {"info", "warning", "error"}
        if level not in valid_levels:
            raise ValueError(
                f"Invalid log level: {level}. Valid levels are: {valid_levels}"
            )

        try:
            # If verbose is enabled, do not capture stdout and stderr
            if self.verbose:
                subprocess.run(
                    [LogInterface.SCRIPT_PATH, level, message, self.log_file],
                    check=True,
                )
            else:
                # Capture stdout and stderr when verbose is disabled
                subprocess.run(
                    [LogInterface.SCRIPT_PATH, level, message, self.log_file],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

        except subprocess.CalledProcessError as e:
            print(f"Failed to log message: {e.stderr.strip()}")
        except FileNotFoundError:
            print(f"Shell script not found at {LogInterface.SCRIPT_PATH}")

    def info(self, message: str):
        """Logs an info-level message."""
        self.log("info", message)

    def warning(self, message: str):
        """Logs a warning-level message."""
        self.log("warning", message)

    def error(self, message: str):
        """Logs an error-level message."""
        self.log("error", message)
