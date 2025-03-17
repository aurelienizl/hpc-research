#!/usr/bin/env python3
import os
import argparse
import matplotlib.pyplot as plt

def read_output_file(file_path, convert_x=True):
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
                if convert_x:
                    x_vals.append(msg_size / 1024.0)
                else:
                    x_vals.append(msg_size)
                y_vals.append(throughput)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return x_vals, y_vals

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
        x, y = read_output_file(fp)
        if not x or not y:
            continue
        curves.append((x, y))
    if not curves:
        return None, None
    # Use the x-values from the first file as reference.
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

def plot_graphs(base_dir):
    """
    Plot the original graphs with individual curves (4 lines for each hypervisor plus BM)
    for both internal (inside) and external (outside) performance.
    """
    hypervisors = ['kvm', 'proxmox']
    network_types = ['inside', 'outside']
    vm_configs = ['1vm', '2vm', '4vm', '8vm']
    
    # Optimized colors for each VM configuration.
    vm_colors = {
        '1vm': 'tab:blue',
        '2vm': 'tab:orange',
        '4vm': 'tab:green',
        '8vm': 'tab:red'
    }
    hv_linestyles = {'kvm': '-', 'proxmox': '--'}
    
    figs = {}
    axes = {}
    for net in network_types:
        fig, ax = plt.subplots()
        figs[net] = fig
        axes[net] = ax

    # Plot BM reference from bm folder.
    for net in network_types:
        bm_path = os.path.join(base_dir, "bm", net, "output.out")
        if os.path.exists(bm_path):
            x, y = read_output_file(bm_path)
            axes[net].plot(x, y, label="BM", linestyle='-.', linewidth=2, color='black', marker='s')
        else:
            print(f"Warning: BM file not found for {net} at {bm_path}")

    # Plot individual curves for each hypervisor and VM configuration.
    for hv in hypervisors:
        for vm in vm_configs:
            for net in network_types:
                file_path = os.path.join(base_dir, hv, net, vm, "output.out")
                if os.path.exists(file_path):
                    x, y = read_output_file(file_path)
                    label = f"{hv} {vm}"
                    axes[net].plot(x, y,
                                   label=label,
                                   linestyle=hv_linestyles[hv],
                                   marker='o',
                                   color=vm_colors[vm])
                else:
                    print(f"Warning: File not found: {file_path}")

    # Finalize and save the graphs.
    for net in network_types:
        ax = axes[net]
        if net == 'inside':
            ax.set_title("Internal Network Performance")
            out_file = os.path.join(base_dir, "internal_network_performance.png")
        else:
            ax.set_title("External Network Performance")
            out_file = os.path.join(base_dir, "external_network_performance.png")
        ax.set_xlabel("Message Size (KB)")
        ax.set_ylabel("Throughput (MB/s)")
        ax.legend(title="Configuration", loc='best')
        ax.grid(True)
        figs[net].tight_layout()
        figs[net].savefig(out_file)
        print(f"Graph saved as: {out_file}")
    
    plt.show()

def plot_average_graphs(base_dir):
    """
    Plot graphs using the average curves for each hypervisor.
    Each graph (internal and external) will have only 3 lines:
      - BM (from bm folder)
      - kvm average (averaging 1vm, 2vm, 4vm, 8vm)
      - proxmox average (averaging 1vm, 2vm, 4vm, 8vm)
    """
    hypervisors = ['kvm', 'proxmox']
    network_types = ['inside', 'outside']
    vm_configs = ['1vm', '2vm', '4vm', '8vm']
    
    # Define colors for the averaged hypervisors.
    avg_colors = {'kvm': 'tab:blue', 'proxmox': 'tab:orange'}
    
    figs = {}
    axes = {}
    for net in network_types:
        fig, ax = plt.subplots()
        figs[net] = fig
        axes[net] = ax

    # Plot BM reference.
    for net in network_types:
        bm_path = os.path.join(base_dir, "bm", net, "output.out")
        if os.path.exists(bm_path):
            x, y = read_output_file(bm_path)
            axes[net].plot(x, y, label="BM", linestyle='-.', linewidth=2, color='black', marker='s')
        else:
            print(f"Warning: BM file not found for {net} at {bm_path}")

    # For each hypervisor, average over all VM configurations.
    for hv in hypervisors:
        for net in network_types:
            file_paths = []
            for vm in vm_configs:
                file_path = os.path.join(base_dir, hv, net, vm, "output.out")
                if os.path.exists(file_path):
                    file_paths.append(file_path)
                else:
                    print(f"Warning: File not found: {file_path}")
            if file_paths:
                x, avg_y = average_curves(file_paths)
                if x is not None and avg_y is not None:
                    label = f"{hv} avg"
                    axes[net].plot(x, avg_y,
                                   label=label,
                                   linestyle='-',
                                   marker='o',
                                   color=avg_colors[hv],
                                   linewidth=2)
    
    # Finalize and save the average graphs.
    for net in network_types:
        ax = axes[net]
        if net == 'inside':
            ax.set_title("Internal Network Performance (Averages)")
            out_file = os.path.join(base_dir, "internal_network_performance_avg.png")
        else:
            ax.set_title("External Network Performance (Averages)")
            out_file = os.path.join(base_dir, "external_network_performance_avg.png")
        ax.set_xlabel("Message Size (KB)")
        ax.set_ylabel("Throughput (MB/s)")
        ax.legend(title="Configuration", loc='best')
        ax.grid(True)
        figs[net].tight_layout()
        figs[net].savefig(out_file)
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

    # Plot the detailed graphs with individual VM curves.
    plot_graphs(base_dir)
    
    # Plot the average graphs if requested.
    if args.plot_averages:
        plot_average_graphs(base_dir)

if __name__ == "__main__":
    main()
