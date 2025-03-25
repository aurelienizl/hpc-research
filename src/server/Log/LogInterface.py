import datetime
from typing import Optional


class LogInterface:
    """
    A Python interface for structured logging operations with portable color support.

    This class provides a standardized way to write logs in a format compatible
    with common log analysis tools. It supports multiple log levels and can
    output to both a file and the console with optional colored output.

    The log format follows the pattern: 'timestamp [LEVEL] - message'
    where timestamp is in ISO 8601 format.
    """

    try:
        from colorama import Fore, Style, init as colorama_init

        colorama_init(autoreset=True)
        DEFAULT_COLORS = {
            "info": Fore.GREEN,
            "verbose": Fore.CYAN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "critical": Fore.MAGENTA,
        }
        RESET_COLOR = Style.RESET_ALL
    except ImportError:
        # Fallback to ANSI escape codes if colorama is not available
        DEFAULT_COLORS = {
            "info": "\033[32m",  # Green
            "verbose": "\033[36m",  # Cyan
            "warning": "\033[33m",  # Yellow
            "error": "\033[31m",  # Red
            "critical": "\033[35m",  # Magenta
        }
        RESET_COLOR = "\033[0m"

    def __init__(self, log_verbose: bool = False, log_file: Optional[str] = None):
        """
        Initialize a new LogInterface instance.

        Parameters:
            log_verbose (bool): When True, logs are output to console in addition to file.
            log_file (str, optional): Path to the log file. Defaults to 'log.txt'.
        """
        self.log_verbose = log_verbose
        self.log_file = log_file or "log.txt"
        self.default_colors = self.DEFAULT_COLORS
        self.reset_color = self.RESET_COLOR

    def log(self, level: str, message: str, color: Optional[str] = None):
        """
        Write a log entry with the specified level and message.

        The log is always written to file. If verbose mode is enabled, it is also
        printed to the console. A provided color only affects console output.

        Parameters:
            level (str): The log severity level (e.g., 'info', 'warning', 'error', 'critical', 'verbose').
            message (str): The message to be logged.
            color (str, optional): ANSI color code string for console output.
        """
        timestamp = datetime.datetime.now().isoformat()
        log_line = f"{timestamp} [{level.upper()}] - {message}\n"

        # Write plain log entry to file (without color codes)
        with open(self.log_file, "a") as lf:
            lf.write(log_line)

        # Print to console if verbose mode is enabled
        if self.log_verbose:
            # Use default color if not provided
            if color is None:
                color = self.default_colors.get(level.lower())
            if color:
                print(f"{color}{log_line}{self.reset_color}", end="")
            else:
                print(log_line, end="")

    def verbose(self, message: str, color: Optional[str] = None):
        """
        Log a verbose message. Verbose logs are recorded only when verbose mode is on.

        Parameters:
            message (str): The verbose message to be logged.
            color (str, optional): ANSI color code for colored console output.
        """
        if self.log_verbose:
            self.log("verbose", message, color=color)

    def info(self, message: str, color: Optional[str] = None):
        """
        Log an informational message.

        Parameters:
            message (str): The information to be logged.
            color (str, optional): ANSI color code for colored console output.
        """
        self.log("info", message, color=color)

    def warning(self, message: str, color: Optional[str] = None):
        """
        Log a warning message.

        Parameters:
            message (str): The warning message to be logged.
            color (str, optional): ANSI color code for colored console output.
        """
        self.log("warning", message, color=color)

    def error(self, message: str, color: Optional[str] = None):
        """
        Log an error message.

        Parameters:
            message (str): The error message to be logged.
            color (str, optional): ANSI color code for colored console output.
        """
        self.log("error", message, color=color)

    def critical(self, message: str, color: Optional[str] = None):
        """
        Log a critical message.

        Parameters:
            message (str): The critical message to be logged.
            color (str, optional): ANSI color code for colored console output.
        """
        self.log("critical", message, color=color)

    def close(self):
        """
        Log the closing of the log file.
        """
        self.log("info", "Closing log file...")
