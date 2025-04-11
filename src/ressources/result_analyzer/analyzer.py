import os
import re
import sys
import glob

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
            # Read and filter out any blank lines (if any exist, they will be skipped)
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
        """
        Container for NPdata objects corresponding to multiple benchmark runs.
        """
        self.benchmarks = []  # List of NPdata instances

    def add_benchmark(self, npdata: NPdata):
        """
        Add an NPdata object to the instance.
        :param npdata: An NPdata instance.
        """
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

class ReportingTool:
    def __init__(self, base_dir: str):
        """
        Entry point class that loads a folder and classifies benchmark data into cluster instances.
        :param base_dir: The directory that contains the benchmark subfolders.
        """
        self.base_dir = base_dir
        # Dictionary with key as cluster id (string) and value as an NPInstance containing relevant NPdata objects.
        self.clusters = {}

    def load_instances(self):
        """
        Traverses the base directory, finds subdirectories matching the naming pattern "cluster_<id>_<runID>",
        recursively searches for all np.out files inside each, and adds the found NPdata objects to the appropriate NPInstance.
        """
        if not os.path.isdir(self.base_dir):
            raise NotADirectoryError(f"{self.base_dir} is not a valid directory.")

        # Look for directories matching cluster_<clusterID>_<runID>
        for entry in os.listdir(self.base_dir):
            full_dir_path = os.path.join(self.base_dir, entry)
            if os.path.isdir(full_dir_path):
                match = re.match(r"cluster_(\d+)_(\d+)$", entry)
                if match:
                    cluster_id = match.group(1)
                    # Search recursively for all np.out files within this folder
                    np_out_files = glob.glob(os.path.join(full_dir_path, "**", "np.out"), recursive=True)
                    if not np_out_files:
                        print(f"Skipping '{full_dir_path}' because no np.out files were found inside it.")
                    for np_out_path in np_out_files:
                        try:
                            np_data = NPdata(file_path=np_out_path)
                        except Exception as e:
                            print(f"Skipping '{np_out_path}' due to error: {e}")
                            continue

                        if cluster_id not in self.clusters:
                            self.clusters[cluster_id] = NPInstance()
                        self.clusters[cluster_id].add_benchmark(np_data)

    def compute_and_store_averages(self):
        """
        For each cluster identified, computes the average NPdata and writes it to the file
        "cluster_<clusterID>_averages.out" in the base directory.
        """
        for cluster_id, np_instance in self.clusters.items():
            try:
                avg_data = np_instance.compute_averages()
                output_path = os.path.join(self.base_dir, f"cluster_{cluster_id}_averages.out")
                avg_data.write(output_path)
                print(f"Wrote average file for cluster {cluster_id} to '{output_path}'")
            except Exception as e:
                print(f"Failed to compute/store averages for cluster {cluster_id}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reporting_tool.py /path/to/base_dir")
        sys.exit(1)

    base_directory = sys.argv[1]
    tool = ReportingTool(base_directory)
    
    # Load NPdata objects from the subdirectories and group them by cluster id.
    tool.load_instances()
    
    # Compute averages for each cluster and write them to output files.
    tool.compute_and_store_averages()
