# CollectResult.py
from pathlib import Path
from collections import defaultdict

class CollectResult:
    def __init__(self, file_path: Path, keywords: list):
        self.file_path = file_path
        # Initialize a dictionary to store arrays for each keyword
        self.metrics = {key: [] for key in keywords}
        self.keywords = keywords
        self.parse_file()

    def parse_file(self):
        """Parse collectl file to gather values for specified keywords over time."""
        with self.file_path.open() as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                # Split into key and value
                try:
                    key, value = line.split(maxsplit=1)
                    # If the key is one we're interested in, store the value
                    if key in self.metrics:
                        try:
                            self.metrics[key].append(float(value))
                        except ValueError:
                            self.metrics[key].append(value)
                except ValueError:
                    continue
