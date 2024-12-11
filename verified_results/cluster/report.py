import os
import re
import numpy as np

# Files we want to process
FILES = [
    "kvm-cluster-1.txt",
    "kvm-cluster-2.txt",
    "kvm-cluster-4.txt",
    "kvm-cluster-8.txt",
]

# Regex patterns
dir_pattern = re.compile(r"Processing directory:\s+(\d+)")
data_line_pattern = re.compile(r"WR11C2R4\s+5000\s+128\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)")
vm_header_pattern = re.compile(r"^### VM (\d+) ###")


def parse_cluster_file(filepath):
    """
    Parse a cluster file.
    Returns a data structure:
    data[vm_id][(P,Q)] = list of (time, gflops) tuples
    """
    data = {}
    current_vm = None

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()

            # Check for VM header
            vm_match = vm_header_pattern.match(line)
            if vm_match:
                current_vm = int(vm_match.group(1))
                if current_vm not in data:
                    data[current_vm] = {}
                continue

            # If no VM header found yet, we might still be reading VM 1 (some files start directly)
            # If file starts without a VM header, assume VM=1 until a header is found.
            if current_vm is None:
                current_vm = 1
                if current_vm not in data:
                    data[current_vm] = {}

            # Parse result lines
            dat_match = data_line_pattern.match(line)
            if dat_match:
                P = int(dat_match.group(1))
                Q = int(dat_match.group(2))
                time_val = float(dat_match.group(3))
                gflops_val = float(dat_match.group(4))
                key = (P, Q)
                if key not in data[current_vm]:
                    data[current_vm][key] = []
                data[current_vm][key].append((time_val, gflops_val))

    return data


def aggregate_scenario_data(scenario_data):
    """
    Given scenario_data of the form:
    scenario_data[vm_id][(P,Q)] = list of (time, gflops)
    Compute average Gflops and Time across all VMs for each (P,Q).
    Returns:
    agg[(P,Q)] = (mean_time, std_time, mean_gflops, std_gflops, count)
    aggregated over all runs and VMs.
    """
    combined = {}
    for vm_id, vm_data in scenario_data.items():
        for (P, Q), vals in vm_data.items():
            if (P, Q) not in combined:
                combined[(P, Q)] = []
            combined[(P, Q)].extend(vals)

    results = {}
    for (P, Q), vals in combined.items():
        times = [v[0] for v in vals]
        gfs = [v[1] for v in vals]
        results[(P, Q)] = (
            np.mean(times),
            np.std(times),
            np.mean(gfs),
            np.std(gfs),
            len(vals),
        )

    return results


def main():
    # Check that all files exist
    for fn in FILES:
        if not os.path.exists(fn):
            print(f"File {fn} not found.")
            return

    scenario_results = {}  # scenario_results[num_vms] = aggregated results
    # num_vms derived from filename (kvm-cluster-N.txt)
    for fn in FILES:
        base = os.path.basename(fn)
        # Extract the number of VMs from the filename
        # filename pattern: kvm-cluster-N.txt
        parts = base.split("-")
        # parts = ["kvm","cluster","N.txt"]
        num_vms_str = parts[-1].replace(".txt", "")
        num_vms = int(num_vms_str)
        scenario_data = parse_cluster_file(fn)
        agg = aggregate_scenario_data(scenario_data)
        scenario_results[num_vms] = agg

    # Now we have scenario_results with aggregated performance for each number of VMs.
    # Let's print a summary comparing performance at different VM counts for each (P,Q).

    # Gather all (P,Q) pairs encountered
    all_configs = set()
    for v in scenario_results.values():
        all_configs.update(v.keys())
    all_configs = sorted(all_configs)

    print("Comparison of Performance as # of VMs Increases")
    print("=" * 60)
    print(
        "Format: For each (P,Q), show mean Gflops at 1,2,4,8 VMs and relative changes"
    )

    # Sorted scenarios by VM count
    scenarios = sorted(scenario_results.keys())

    for P, Q in all_configs:
        print(f"\n(P={P}, Q={Q}):")
        baseline_gflops = None
        scenario_values = []
        for vm_count in scenarios:
            if (P, Q) in scenario_results[vm_count]:
                mean_t, std_t, mean_g, std_g, count = scenario_results[vm_count][(P, Q)]
                scenario_values.append((vm_count, mean_t, mean_g))
            else:
                scenario_values.append((vm_count, None, None))

        # Print results
        for vm_count, mean_t, mean_g in scenario_values:
            if mean_g is not None:
                if baseline_gflops is None:
                    baseline_gflops = mean_g
                diff_pct = (
                    ((mean_g - baseline_gflops) / baseline_gflops * 100.0)
                    if baseline_gflops
                    else 0.0
                )
                print(
                    f"  {vm_count} VM(s): {mean_g:.2f} Gflops (Time={mean_t:.2f}s) | Diff from 1-VM: {diff_pct:.2f}%"
                )
            else:
                print(f"  {vm_count} VM(s): No data")

    # We can add more advanced comparisons or statistical tests as needed.


if __name__ == "__main__":
    main()
