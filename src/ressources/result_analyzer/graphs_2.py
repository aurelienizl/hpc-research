import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
ACCEPTED_FILES = [
    "kvm-metrics.out",
    "proxmox-metrics.out",
    "bare-metal-metrics.out",
]

DISPLAY_MAP = {
    "kvm": "KVM",
    "proxmox": "PROXMOX",
    "bare-metal": "BARE_METAL",
}

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def ensure_dir(directory):
    """Ensure that the output directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)


class CollectlMetric:
    def __init__(self, file_path: str):
        """
        Reads a file and extracts 'cputotals.total' and 'meminfo.used' values.
        """
        self.cpu = []
        self.memory = []
        self._load(file_path)

    def _load(self, file_path: str):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 2:
                    continue
                key, val = parts[0], parts[1]
                try:
                    value = float(val)
                except ValueError:
                    continue
                if key == "cputotals.total":
                    self.cpu.append(value)
                elif key == "meminfo.used":
                    self.memory.append(value)


def process_values(values):
    """
    Generic processing: average and symmetric errors.
    """
    if not values:
        return None, None, None
    avg = np.mean(values)
    err_low = avg - min(values)
    err_high = max(values) - avg
    return avg, err_low, err_high


def process_cpu(values, threshold_factor=0.9):
    """
    Process CPU values by keeping those >= threshold*max.
    """
    if not values:
        return None, None, None
    max_val = max(values)
    cleaned = [v for v in values if v >= threshold_factor * max_val]
    return process_values(cleaned)

# ----------------------------------------------------------------------------
# Graph generation
# ----------------------------------------------------------------------------
def generate_resource_graphs(resources_dir, out_dir):
    # Discover configurations
    configs = sorted([
        d for d in os.listdir(resources_dir)
        if os.path.isdir(os.path.join(resources_dir, d))
    ])

    for cfg in configs:
        cfg_path = os.path.join(resources_dir, cfg)
        vm_dirs = sorted([
            d for d in os.listdir(cfg_path)
            if os.path.isdir(os.path.join(cfg_path, d))
        ])

        # Prepare data containers per VM
        cpu_data = []
        mem_data = []
        labels = []

        for vm in vm_dirs:
            vm_path = os.path.join(cfg_path, vm)
            cpu_dict = {}
            mem_dict = {}
            for fname in ACCEPTED_FILES:
                key = fname.replace("-metrics.out", "")
                file_path = os.path.join(vm_path, fname)
                if os.path.exists(file_path):
                    try:
                        m = CollectlMetric(file_path)
                        cpu_dict[key] = process_cpu(m.cpu)
                        mem_dict[key] = process_values(m.memory)
                    except Exception:
                        cpu_dict[key] = (None, None, None)
                        mem_dict[key] = (None, None, None)
                else:
                    cpu_dict[key] = (None, None, None)
                    mem_dict[key] = (None, None, None)

            cpu_data.append(cpu_dict)
            mem_data.append(mem_dict)
            labels.append(vm)

        # Axis setup
        x = np.arange(len(vm_dirs))
        n_sys = len(ACCEPTED_FILES)
        width = 0.8 / n_sys
        cmap = plt.get_cmap("tab10")

        # --------------------- CPU Graph ---------------------
        fig, ax = plt.subplots(figsize=(10, 6))  # wider for aesthetics
        for i, fname in enumerate(ACCEPTED_FILES):
            key = fname.replace("-metrics.out", "")
            vals = [cpu_data[j][key][0] or 0 for j in range(len(vm_dirs))]
            errs_low = [cpu_data[j][key][1] or 0 for j in range(len(vm_dirs))]
            errs_high = [cpu_data[j][key][2] or 0 for j in range(len(vm_dirs))]
            ax.bar(
                x + i * width,
                vals,
                width,
                yerr=[errs_low, errs_high],
                capsize=5,
                label=DISPLAY_MAP.get(key, key),
                color=cmap(i)
            )
        ax.set_xticks(x + width * (n_sys - 1) / 2)
        ax.set_xticklabels(labels, rotation=45, ha='right')  # rotate labels to prevent overlap
        ax.set_ylabel("CPU Average (%)")
        ax.set_title(f"CPU Metrics for {cfg}")
        ax.yaxis.grid(True)
        # Adjust bottom margin and legend
        fig.subplots_adjust(bottom=0.25)
        ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1), fontsize='small')
        plt.tight_layout(rect=[0, 0, 0.98, 1])
        cpu_out = os.path.join(out_dir, f"{cfg}_cpu.png")
        plt.savefig(cpu_out, dpi=300)
        plt.close()
        print(f"Saved CPU graph: {cpu_out}")

        # --------------------- Memory Graph ---------------------
        fig, ax = plt.subplots(figsize=(10, 6))
        for i, fname in enumerate(ACCEPTED_FILES):
            key = fname.replace("-metrics.out", "")
            vals = [mem_data[j][key][0] or 0 for j in range(len(vm_dirs))]
            errs_low = [mem_data[j][key][1] or 0 for j in range(len(vm_dirs))]
            errs_high = [mem_data[j][key][2] or 0 for j in range(len(vm_dirs))]
            ax.bar(
                x + i * width,
                vals,
                width,
                yerr=[errs_low, errs_high],
                capsize=5,
                label=DISPLAY_MAP.get(key, key),
                color=cmap(i)
            )
        ax.set_xticks(x + width * (n_sys - 1) / 2)
        ax.set_xticklabels(labels, rotation=45, ha='right')  # rotate labels
        ax.set_ylabel("Memory Average")
        ax.set_title(f"Memory Metrics for {cfg}")
        ax.yaxis.grid(True)
        fig.subplots_adjust(bottom=0.25)
        ax.legend(loc='upper left', bbox_to_anchor=(1.00, 1), fontsize='small')
        plt.tight_layout(rect=[0, 0, 0.98, 1])
        mem_out = os.path.join(out_dir, f"{cfg}_memory.png")
        plt.savefig(mem_out, dpi=300)
        plt.close()
        print(f"Saved Memory graph: {mem_out}")

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python resource_graphs.py /path/to/resources_metrics")
        sys.exit(1)

    resources_dir = sys.argv[1]
    out_dir = os.path.join(resources_dir, "graphs")
    ensure_dir(out_dir)
    generate_resource_graphs(resources_dir, out_dir)