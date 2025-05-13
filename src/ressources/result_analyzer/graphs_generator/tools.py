"""
tools.py

Contains shared classes and methods for:
  - File management (ensuring directories, loading .out files)
  - Data classes (NPdata, NPInstance, etc.)
  - A generic dynamic graph creation function that is used by both performance and latency modules.
"""

import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

def ensure_dir(directory):
    """Ensure that the specified directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_np_file(file_path):
    """
    Loads an output file (e.g., bm.out, kvm.out, proxmox.out).
    Expects exactly 124 non-empty lines with 3 columns each.
    Returns a numpy array of shape (124, 3).

    Raises:
      ValueError if the file does not follow the expected format.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    if len(lines) != 124:
        raise ValueError(f"File {file_path} must contain exactly 124 non-empty lines; found {len(lines)}.")
    
    data = []
    for idx, line in enumerate(lines):
        parts = line.split()
        if len(parts) != 3:
            raise ValueError(f"Line {idx+1} in file {file_path} does not have exactly 3 values.")
        try:
            row = list(map(float, parts))
        except ValueError:
            raise ValueError(f"Line {idx+1} in file {file_path} contains non-numeric values.")
        data.append(row)
    return np.array(data)

# ----------------------------------------------------------------------------
# Shared Data Classes
# ----------------------------------------------------------------------------

class NPdata:
    """
    Represents numerical performance data loaded from a file or provided directly.
    Expect exactly 124 data points (each with 3 values).
    """
    def __init__(self, file_path: str = None, col1: list = None, col2: list = None, col3: list = None):
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
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, "r") as file:
            lines = [line.strip() for line in file if line.strip()]
        if len(lines) != 124:
            raise ValueError(f"Invalid file format: {file_path} must contain exactly 124 non-empty lines; found {len(lines)}.")
        self.col1 = []
        self.col2 = []
        self.col3 = []
        for idx, line in enumerate(lines):
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"Line {idx+1} in file {file_path} does not contain exactly 3 values.")
            try:
                self.col1.append(float(parts[0]))
                self.col2.append(float(parts[1]))
                self.col3.append(float(parts[2]))
            except ValueError:
                raise ValueError(f"Line {idx+1} in file {file_path} contains non-numeric values.")

    def write(self, file_path: str):
        with open(file_path, "w") as f:
            for i in range(124):
                f.write(f"{self.col1[i]} {self.col2[i]} {self.col3[i]}\n")

class NPInstance:
    """
    Represents a collection of NPdata instances and can compute averages.
    """
    def __init__(self):
        self.benchmarks = []  # List of NPdata instances

    def add_benchmark(self, npdata: NPdata):
        self.benchmarks.append(npdata)

    def compute_averages(self) -> NPdata:
        if not self.benchmarks:
            raise ValueError("No NPdata benchmarks to compute averages from.")
        n = len(self.benchmarks)
        avg_col1, avg_col2, avg_col3 = [], [], []
        for i in range(124):
            sum1 = sum(npdata.col1[i] for npdata in self.benchmarks)
            sum2 = sum(npdata.col2[i] for npdata in self.benchmarks)
            sum3 = sum(npdata.col3[i] for npdata in self.benchmarks)
            avg_col1.append(sum1 / n)
            avg_col2.append(sum2 / n)
            avg_col3.append(sum3 / n)
        return NPdata(col1=avg_col1, col2=avg_col2, col3=avg_col3)

class CollectlMetric:
    """
    Reads and stores collectl metrics from a file.
    """
    def __init__(self, file_path: str):
        self.cpu = []
        self.memory = []
        self.load_from_file(file_path)

    def load_from_file(self, file_path: str):
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
                    self.cpu.append(value)
                elif key == "meminfo.used":
                    self.memory.append(value)

# ----------------------------------------------------------------------------
# Generic Graph Creation Function
# ----------------------------------------------------------------------------

def get_distinct_colors(n):
    """
    Returns a list of n visually distinct colors.
    Uses matplotlib's tab20, tab20b, tab20c, and hsv colormaps for maximum differentiation.
    """
    if n <= 10:
        cmap = plt.get_cmap("tab10")
        return [cmap(i) for i in range(n)]
    elif n <= 20:
        cmap = plt.get_cmap("tab20")
        return [cmap(i) for i in range(n)]
    elif n <= 40:
        # Combine tab20, tab20b, tab20c
        colors = []
        for cmap_name in ["tab20", "tab20b", "tab20c"]:
            cmap = plt.get_cmap(cmap_name)
            colors.extend([cmap(i) for i in range(20)])
        return colors[:n]
    else:
        # Use hsv for large n
        return [matplotlib.colors.hsv_to_rgb((i / n, 0.8, 0.8)) for i in range(n)]

def plot_config_graph(config, base_dir, out_dir, data_index, y_label):
    """
    Creates a dynamic graph for a given configuration folder.

    Scans each subfolder in the configuration and for every file ending with '.out',
    it dynamically creates a mapping for colors and line styles, then plots
    the data. The plotted y-value is selected based on data_index (0-based):
      - data_index=1 for performance (expected units: Mbps)
      - data_index=2 for latency (expected units: usec)

    Each data series gets a unique color for better readability.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    config_path = os.path.join(base_dir, config)
    subfolders = [d for d in os.listdir(config_path) if os.path.isdir(os.path.join(config_path, d))]

    # Collect all data series for consistent color assignment
    all_series = []
    for folder in subfolders:
        folder_path = os.path.join(config_path, folder)
        out_files = [f for f in os.listdir(folder_path)
                     if os.path.isfile(os.path.join(folder_path, f)) and f.endswith(".out")]
        for out_file in out_files:
            file_base = os.path.splitext(out_file)[0]
            if out_file == "result.out":
                label = f"{folder}"
            else:
                label = f"{file_base} {folder}"
            all_series.append(label)

    # Assign distinct colors
    sorted_series = sorted(all_series)
    colors = get_distinct_colors(len(sorted_series))
    color_mapping = {series: colors[i] for i, series in enumerate(sorted_series)}

    plotted = False
    for folder in sorted(subfolders):
        folder_path = os.path.join(config_path, folder)
        out_files = [f for f in os.listdir(folder_path)
                     if os.path.isfile(os.path.join(folder_path, f)) and f.endswith(".out")]
        for out_file in out_files:
            file_path = os.path.join(folder_path, out_file)
            # If there is metrics in the file, skip it
            try:
                data = load_np_file(file_path)
            except Exception as e:
                print(f"Skipping '{file_path}' due to error: {e}")
                continue

            x = data[:, 0]
            y = data[:, data_index]
            file_base = os.path.splitext(out_file)[0]
            if out_file == "result.out":
                label = f"{folder}"
            else:
                label = f"{file_base} {folder}"
            color = color_mapping.get(label, "blue")

            # Plot with lines only, explicitly setting marker to None
            ax.plot(x, y, linewidth=2, 
                    color=color, label=label, alpha=0.9, marker=None)
            plotted = True

    if not plotted:
        print(f"No valid data to plot for configuration '{config}'.")
        return

    ax.set_xlabel("Message Size (bytes)", fontsize=10)
    ax.set_ylabel(y_label, fontsize=10)
    ax.set_title(f"{config} {y_label}", fontsize=12)
    ax.set_xscale('log')
    ax.tick_params(axis='both', which='major', labelsize=8)

    # Sort legend entries alphabetically
    handles, labels = ax.get_legend_handles_labels()
    sorted_pairs = sorted(zip(labels, handles), key=lambda x: x[0])
    if sorted_pairs:
        sorted_labels, sorted_handles = zip(*sorted_pairs)
        ax.legend(sorted_handles, sorted_labels, ncol=2, fontsize=8, frameon=True)
    else:
        ax.legend(ncol=2, fontsize=8, frameon=True)

    plt.tight_layout()

    output_path = os.path.join(out_dir, f"{config}_{y_label.split()[0].lower()}.png")
    plt.savefig(output_path, format='png', dpi=300)
    plt.close()
    print(f"Saved graph for {config} at {output_path}")
