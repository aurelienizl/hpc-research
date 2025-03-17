#!/usr/bin/env python3
import os
import argparse
import matplotlib.pyplot as plt

class BenchmarkData:
    """Provides methods to read and average benchmark curves."""

    @staticmethod
    def read_file(file_path, convert_x=True):
        """
        Reads a benchmark output.out file.
        Each non-empty line is assumed to have at least two columns:
          - first column: message size (in bytes)
          - second column: throughput (MB/s)
        
        Parameters:
          file_path (str): path to the output.out file.
          convert_x (bool): if True, convert message size from bytes to KB.
        
        Returns:
          (list, list): tuple with x-values and throughput values.
        """
        x_vals = []
        y_vals = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 2:
                        continue
                    try:
                        msg_size = int(parts[0])
                        throughput = float(parts[1])
                    except ValueError:
                        continue
                    x_vals.append(msg_size / 1024.0 if convert_x else msg_size)
                    y_vals.append(throughput)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return x_vals, y_vals

    @staticmethod
    def average_curves(file_paths):
        """
        Given a list of file paths, reads each benchmark file and averages
        the throughput values for matching message sizes.
        
        Assumes all files have identical x-values.
        
        Returns:
          (list, list): tuple with x-values and averaged throughput values.
        """
        curves = []
        for fp in file_paths:
            x, y = BenchmarkData.read_file(fp)
            if not x or not y:
                continue
            curves.append((x, y))
        if not curves:
            return None, None
        
        base_x = curves[0][0]
        n = len(base_x)
        sum_y = [0.0] * n
        count = 0
        for (x_vals, y_vals) in curves:
            if len(x_vals) != n or any(abs(x_vals[i] - base_x[i]) > 1e-6 for i in range(n)):
                print("Warning: x values do not match across curves. Skipping averaging for this set.")
                return None, None
            for i in range(n):
                sum_y[i] += y_vals[i]
            count += 1
        avg_y = [val / count for val in sum_y]
        return base_x, avg_y

class GraphPlotter:
    """Handles the plotting of detailed and average benchmark graphs."""
    
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.hypervisors = ['kvm', 'proxmox']
        self.network_types = ['inside', 'outside']
        self.vm_configs = ['1vm', '2vm', '4vm', '8vm']
        
        # Optimized colors for each VM configuration.
        self.vm_colors = {
            '1vm': 'tab:blue',
            '2vm': 'tab:orange',
            '4vm': 'tab:green',
            '8vm': 'tab:red'
        }
        # Linestyles for the hypervisors.
        self.hv_linestyles = {'kvm': '-', 'proxmox': '--'}
        # Colors for averaged curves.
        self.avg_colors = {'kvm': 'tab:blue', 'proxmox': 'tab:orange'}
        # BM (reference) style.
        self.bm_style = {
            'label': 'BM', 'linestyle': '-.', 'linewidth': 2,
            'color': 'black', 'marker': 's'
        }

    def _setup_axis(self, net):
        """Initializes a figure and axis with proper labels and title."""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_xlabel("Message Size (KB)")
        ax.set_ylabel("Throughput (MB/s)")
        title = "Internal Network Performance" if net == 'inside' else "External Network Performance"
        ax.set_title(title)
        return fig, ax

    def _add_legend_outside(self, ax):
        """
        Places the legend just to the right of the plot.
        Adjust the bbox_to_anchor if you want to move it closer/farther.
        """
        ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)

    def plot_detailed(self):
        """Plots detailed graphs with individual curves for each hypervisor/VM configuration plus BM."""
        for net in self.network_types:
            fig, ax = self._setup_axis(net)
            # Plot BM reference.
            bm_path = os.path.join(self.base_dir, "bm", net, "output.out")
            if os.path.exists(bm_path):
                x, y = BenchmarkData.read_file(bm_path)
                ax.plot(x, y, **self.bm_style)
            else:
                print(f"Warning: BM file not found for {net} at {bm_path}")

            # Plot individual curves.
            for hv in self.hypervisors:
                for vm in self.vm_configs:
                    file_path = os.path.join(self.base_dir, hv, net, vm, "output.out")
                    if os.path.exists(file_path):
                        x, y = BenchmarkData.read_file(file_path)
                        label = f"{hv} {vm}"
                        ax.plot(x, y, label=label,
                                linestyle=self.hv_linestyles[hv],
                                marker='o', color=self.vm_colors[vm])
                    else:
                        print(f"Warning: File not found: {file_path}")

            # Place legend outside on the right.
            self._add_legend_outside(ax)
            ax.grid(True)
            
            # Use tight_layout, then save with bbox_inches='tight' to minimize whitespace.
            fig.tight_layout()
            out_file = (os.path.join(self.base_dir, "internal_network_performance.png")
                        if net == "inside"
                        else os.path.join(self.base_dir, "external_network_performance.png"))
            fig.savefig(out_file, bbox_inches='tight')
            print(f"Graph saved as: {out_file}")
        plt.show()

    def plot_average(self):
        """
        Plots graphs using averaged curves for each hypervisor.
        Each graph (internal and external) will have only 3 lines:
          - BM (from bm folder)
          - kvm average
          - proxmox average
        """
        for net in self.network_types:
            fig, ax = self._setup_axis(net)
            # Plot BM reference.
            bm_path = os.path.join(self.base_dir, "bm", net, "output.out")
            if os.path.exists(bm_path):
                x, y = BenchmarkData.read_file(bm_path)
                ax.plot(x, y, **self.bm_style)
            else:
                print(f"Warning: BM file not found for {net} at {bm_path}")

            # Average curves for each hypervisor.
            for hv in self.hypervisors:
                file_paths = []
                for vm in self.vm_configs:
                    file_path = os.path.join(self.base_dir, hv, net, vm, "output.out")
                    if os.path.exists(file_path):
                        file_paths.append(file_path)
                    else:
                        print(f"Warning: File not found: {file_path}")
                if file_paths:
                    x, avg_y = BenchmarkData.average_curves(file_paths)
                    if x is not None and avg_y is not None:
                        label = f"{hv} avg"
                        ax.plot(x, avg_y, label=label, linestyle='-',
                                marker='o', color=self.avg_colors[hv], linewidth=2)

            # Place legend outside on the right.
            self._add_legend_outside(ax)
            ax.grid(True)
            fig.tight_layout()
            out_file = (os.path.join(self.base_dir, "internal_network_performance_avg.png")
                        if net == "inside"
                        else os.path.join(self.base_dir, "external_network_performance_avg.png"))
            fig.savefig(out_file, bbox_inches='tight')
            print(f"Average graph saved as: {out_file}")
        plt.show()

def main():
    parser = argparse.ArgumentParser(
        description="Plot network performance graphs from benchmark output files. "
                    "Generates full-detail graphs and average graphs (with only 3 lines: BM, kvm avg, and proxmox avg)."
    )
    parser.add_argument("--base-dir", default=".", help="Base directory containing bm, kvm, and proxmox folders")
    parser.add_argument("--plot-averages", action="store_true", help="Plot the average graphs (only 3 lines)")
    args = parser.parse_args()

    base_dir = os.path.abspath(args.base_dir)
    print(f"Using base directory: {base_dir}")
    plotter = GraphPlotter(base_dir)

    # Always plot the detailed graphs:
    plotter.plot_detailed()
    # Plot the average graphs if requested:
    if args.plot_averages:
        plotter.plot_average()

if __name__ == "__main__":
    main()
