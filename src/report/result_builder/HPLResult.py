# HPLResult.py
import re
from pathlib import Path

class HPLResult:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.time = None
        self.gflops = None
        self.residual = None
        self.N = None
        self.NB = None
        self.P = None
        self.Q = None

        self.parse_file()

    def parse_file(self):
        """Parse the HPL result file to extract metrics and parameters."""
        content = self.file_path.read_text()

        # Extract basic HPL metrics: Time, GFLOPS, and residual
        match = re.search(r"WR.*\s+([\d\.Ee+-]+)\s+([\d\.Ee+-]+)", content)
        if match:
            self.time = float(match.group(1))
            self.gflops = float(match.group(2))

        residual_match = re.search(r"=\s+([\d\.Ee+-]+)\s+\.+ PASSED", content)
        if residual_match:
            self.residual = float(residual_match.group(1))

        param_patterns = {
            "N": r"N\s*:\s*(\d+)",
            "NB": r"NB\s*:\s*(\d+)",
            "P": r"P\s*:\s*(\d+)",
            "Q": r"Q\s*:\s*(\d+)"
        }

        for attr, pattern in param_patterns.items():
            param_match = re.search(pattern, content)
            if param_match:
                setattr(self, attr, int(param_match.group(1)))
