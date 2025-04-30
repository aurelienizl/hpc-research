import os
import re
import sys
import glob

# ========================= NPdata Classes ============================
class NPdata:
    def __init__(self, file_path: str = None, col1: list = None, col2: list = None, col3: list = None):
        """
        Construct NPdata either by reading a file or by providing the three arrays directly.
        :param file_path: Path to the np.out file to load.
        :param col1: List of values from column 1.
        :param col2: List of values from column 2.
        :param col3: List of values from column 3.
        :raises Exception: if file reading fails or if the provided arrays are not exactly of length 124.
        """
        if file_path is not None:
            self.load_from_file(file_path)
        elif col1 is not None and col2 is not None and col3 is not None:
            if not (len(col1) == 124 and len(col2) == 124 and len(col3) == 124):
                raise ValueError("Provided arrays must have exactly 124 values each.")
            self.col1 = col1
            self.col2 = col2
            self.col3 = col3
        else:
            raise ValueError("Either a valid file path or three arrays must be provided.")
            
    def load_from_file(self, file_path: str):
        """
        Reads the file from the given path, expecting exactly 124 non-empty lines with 3 numeric entries.
        :param file_path: Path to the file.
        :raises Exception: if file does not exist or if the contents are invalid.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, "r") as file:
            # Read and filter out any blank lines
            lines = [line.strip() for line in file if line.strip() != ""]
            
        if len(lines) != 124:
            raise ValueError(f"Invalid file format: {file_path} must contain exactly 124 non-empty lines; found {len(lines)}.")

        self.col1 = []
        self.col2 = []
        self.col3 = []

        for idx, line in enumerate(lines):
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"Line {idx + 1} in file {file_path} does not contain exactly 3 values.")
            try:
                self.col1.append(float(parts[0]))
                self.col2.append(float(parts[1]))
                self.col3.append(float(parts[2]))
            except ValueError:
                raise ValueError(f"Line {idx + 1} in file {file_path} contains non-numeric values.")

    def write(self, file_path: str):
        """
        Writes the NPdata to a file with the format of the original np.out.
        :param file_path: Path where the output file will be written.
        """
        with open(file_path, "w") as f:
            for i in range(124):
                f.write(f"{self.col1[i]} {self.col2[i]} {self.col3[i]}\n")


class NPInstance:
    def __init__(self):
        """Container for NPdata objects (benchmark runs)."""
        self.benchmarks = []  # List of NPdata instances

    def add_benchmark(self, npdata: NPdata):
        """Adds an NPdata object to the instance."""
        self.benchmarks.append(npdata)

    def compute_averages(self) -> NPdata:
        """
        Computes the average for each row (total of 124 rows) across all NPdata objects stored.
        :return: A new NPdata instance containing the average values.
        :raises Exception: if no NPdata objects are available.
        """
        if not self.benchmarks:
            raise ValueError("No NPdata benchmarks to compute averages from.")

        n = len(self.benchmarks)
        avg_col1 = []
        avg_col2 = []
        avg_col3 = []

        for i in range(124):
            sum1 = sum(npdata.col1[i] for npdata in self.benchmarks)
            sum2 = sum(npdata.col2[i] for npdata in self.benchmarks)
            sum3 = sum(npdata.col3[i] for npdata in self.benchmarks)
            avg_col1.append(sum1 / n)
            avg_col2.append(sum2 / n)
            avg_col3.append(sum3 / n)
            
        return NPdata(col1=avg_col1, col2=avg_col2, col3=avg_col3)


# ===================== Collectl Data Classes ==========================
class CollectlData:
    def __init__(self, file_path: str):
        """
        Reads a collectl.log file and stores the line‐by‐line values
        for the two metrics: "cputotals.total" and "meminfo.used".
        :param file_path: Path to the collectl.log file.
        :raises Exception: if file reading fails or if the two metrics are inconsistent.
        """
        self.cputotals = []  # List of values (one per sample)
        self.meminfo_used = []  # List of values (one per sample)
        self.load_from_file(file_path)

    def load_from_file(self, file_path: str):
        """
        Reads the collectl.log file and, for each line that begins with one of our keys,
        appends its numeric value to the appropriate list.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "r") as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) < 2:
                    continue
                key = parts[0]
                try:
                    value = float(parts[1])
                except ValueError:
                    continue
                if key == "cputotals.total":
                    self.cputotals.append(value)
                elif key == "meminfo.used":
                    self.meminfo_used.append(value)
        if len(self.cputotals) != len(self.meminfo_used):
            raise ValueError(f"Mismatch in sample count between cputotals.total and meminfo.used in {file_path}")


class CollectlInstance:
    def __init__(self):
        """Container for CollectlData objects (runs)."""
        self.collectl_data_list = []
    
    def add_collectl_data(self, cdata: CollectlData):
        """Adds a CollectlData object to the instance."""
        self.collectl_data_list.append(cdata)
    
    def compute_line_by_line_averages(self):
        """
        Computes line-by-line averages for both metrics across all runs.
        Uses the minimum sample count among the files to avoid index errors.
        :return: Two lists: (avg_cputotals, avg_meminfo)
        """
        if not self.collectl_data_list:
            return None, None

        # Use the minimum number of samples across all files
        num_samples = min(len(cd.cputotals) for cd in self.collectl_data_list)
        avg_cputotals = []
        avg_meminfo = []
        for i in range(num_samples):
            avg_total = sum(cd.cputotals[i] for cd in self.collectl_data_list) / len(self.collectl_data_list)
            avg_mem = sum(cd.meminfo_used[i] for cd in self.collectl_data_list) / len(self.collectl_data_list)
            avg_cputotals.append(avg_total)
            avg_meminfo.append(avg_mem)
        return avg_cputotals, avg_meminfo


# ======================= Folder Processing Function ======================
def process_folder(base_dir: str):
    print(f"\nProcessing base directory: {base_dir}")

    # Recursively search for np.out files within the base folder
    np_files = glob.glob(os.path.join(base_dir, "**", "np.out"), recursive=True)
    if not np_files:
        print("No np.out files found in", base_dir)
    else:
        np_instance = NPInstance()
        for np_file in np_files:
            try:
                np_data = NPdata(file_path=np_file)
                np_instance.add_benchmark(np_data)
            except Exception as e:
                print(f"Skipping '{np_file}' due to error: {e}")
        try:
            avg_np_data = np_instance.compute_averages()
            np_output_path = os.path.join(base_dir, "np-averages.out")
            avg_np_data.write(np_output_path)
            print(f"Wrote NP averages to '{np_output_path}'")
        except Exception as e:
            print(f"Failed to compute/store NP averages for {base_dir}: {e}")

    # Recursively search for collectl.log files within the base folder
    collectl_files = glob.glob(os.path.join(base_dir, "**", "collectl.log"), recursive=True)
    if not collectl_files:
        print("No collectl.log files found in", base_dir)
    else:
        collectl_instance = CollectlInstance()
        for cl_file in collectl_files:
            try:
                cl_data = CollectlData(cl_file)
                collectl_instance.add_collectl_data(cl_data)
            except Exception as e:
                print(f"Skipping '{cl_file}' due to error: {e}")
        avg_cputotals, avg_meminfo = collectl_instance.compute_line_by_line_averages()
        if avg_cputotals is None or avg_meminfo is None:
            print("Failed to compute averages for collectl data in", base_dir)
        else:
            collectl_output_path = os.path.join(base_dir, "collectl-averages.out")
            try:
                with open(collectl_output_path, "w") as f:
                    for i in range(len(avg_cputotals)):
                        f.write(f"cputotals.total {avg_cputotals[i]}\n")
                        f.write(f"meminfo.used {avg_meminfo[i]}\n")
                print(f"Wrote collectl averages to '{collectl_output_path}'")
            except Exception as e:
                print(f"Failed to write collectl averages for {base_dir}: {e}")


# ======================= New Main Routine =============================
def main():
    if len(sys.argv) < 2:
        print("Usage: python reporting_tool.py <glob_pattern> [additional_patterns ...]")
        sys.exit(1)

    # If multiple arguments are given, they may be pre-expanded by the shell.
    # We iterate over all provided arguments.
    base_dirs = []
    for arg in sys.argv[1:]:
        if os.path.isdir(arg):
            base_dirs.append(arg)
        else:
            # Try to expand if not a directory already
            base_dirs.extend(glob.glob(arg))
    
    if not base_dirs:
        print("No directories matched the given pattern(s).")
        sys.exit(1)

    for base_dir in base_dirs:
        if not os.path.isdir(base_dir):
            print(f"Skipping '{base_dir}' because it is not a directory.")
            continue
        process_folder(base_dir)

if __name__ == "__main__":
    main()
