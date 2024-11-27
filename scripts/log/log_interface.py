import subprocess


class ShellLogger:
    """
    A Python class to interact with the log.sh shell script for logging.
    """
    def __init__(self, script_path: str = "./log/log.sh", verbose: bool = False):
        """
        Initializes the ShellLogger with the path to the shell script and verbosity control.

        Args:
            script_path (str): Path to the shell script for logging.
            verbose (bool): If True, logs are displayed in real-time.
        """
        self.script_path = script_path
        self.verbose = verbose

    def log(self, level: str, message: str):
        """
        Logs a message using the shell script.

        Args:
            level (str): Log level ('info', 'warning', 'error').
            message (str): Log message.
        """
        valid_levels = {"info", "warning", "error"}
        if level not in valid_levels:
            raise ValueError(f"Invalid log level: {level}. Valid levels are: {valid_levels}")

        try:
            # If verbose is enabled, do not capture stdout and stderr
            if self.verbose:
                subprocess.run(
                    [self.script_path, level, message],
                    check=True
                )
            else:
                # Capture stdout and stderr when verbose is disabled
                subprocess.run(
                    [self.script_path, level, message],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

        except subprocess.CalledProcessError as e:
            print(f"Failed to log message: {e.stderr.strip()}")
        except FileNotFoundError:
            print(f"Shell script not found at {self.script_path}")

    def info(self, message: str):
        """Logs an info-level message."""
        self.log("info", message)

    def warning(self, message: str):
        """Logs a warning-level message."""
        self.log("warning", message)

    def error(self, message: str):
        """Logs an error-level message."""
        self.log("error", message)
