import os
import re
import numpy as np
from abc import ABC, abstractmethod

# Constants (assuming constant from the problem statement)
N = 5000
NB = 128

# Mapping filenames to architecture and mode
ARCH_MAP = {"bm": "bare-metal", "kvm": "kvm"}
MODE_MAP = {"comp": "comp", "coop": "coop"}

# Regex to identify data lines
# Format: WR11C2R4 5000 128 P Q Time Gflops
data_line_pattern = re.compile(r"WR11C2R4\s+5000\s+128\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)")
dir_line_pattern = re.compile(r"Processing directory:\s+(\d+)")


def parse_file(filepath):
    """
    Parse a single results file, returning a list of tuples:
    [(P, Q, time, gflops), ...]
    """
    data = []
    current_dir = None

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            dir_match = dir_line_pattern.match(line)
            if dir_match:
                current_dir = int(dir_match.group(1))
                continue

            dat_match = data_line_pattern.match(line)
            if dat_match:
                P = int(dat_match.group(1))
                Q = int(dat_match.group(2))
                time_str = dat_match.group(3)
                gflops_str = dat_match.group(4)

                time_val = float(time_str)
                gflops_val = float(gflops_str)

                data.append((P, Q, time_val, gflops_val))
    return data


class BenchmarkData:
    """
    Class to hold all benchmark results for multiple files.
    Data structure:
    results[(arch, mode, P, Q)] = list of (time, gflops) tuples.
    """

    def __init__(self):
        self.results = {}

    def load_files(self, files):
        for fn in files:
            if not os.path.exists(fn):
                print(
                    f"File {fn} not found. Please ensure the file is in the current directory."
                )
                return False

        for fn in files:
            arch, mode = self._identify_arch_mode(fn)
            file_data = parse_file(fn)
            for P, Q, time_val, gflops_val in file_data:
                key = (arch, mode, P, Q)
                if key not in self.results:
                    self.results[key] = []
                self.results[key].append((time_val, gflops_val))
        return True

    def _identify_arch_mode(self, filename):
        base = os.path.basename(filename)
        parts = base.split("_")
        arch_code = parts[0]
        mode_code = parts[1]
        architecture = ARCH_MAP.get(arch_code, arch_code)
        mode = MODE_MAP.get(mode_code, mode_code)
        return architecture, mode

    def get_all_keys(self):
        return list(self.results.keys())

    def get_modes(self):
        modes = set(k[1] for k in self.results.keys())
        return modes

    def get_configurations(self, mode):
        # Return all (arch, P, Q) triplets for a given mode
        configs = []
        for arch, m, p, q in self.results.keys():
            if m == mode:
                configs.append((arch, p, q))
        return sorted(set(configs), key=lambda x: (x[0], x[1], x[2]))

    def get_stats(self, arch, mode, P, Q):
        """
        Return (mean_time, std_time, mean_gflops, std_gflops, count)
        for a given configuration.
        """
        vals = self.results.get((arch, mode, P, Q), [])
        if not vals:
            return None
        times = [v[0] for v in vals]
        gfs = [v[1] for v in vals]
        return (np.mean(times), np.std(times), np.mean(gfs), np.std(gfs), len(vals))

    def get_archs_for_mode(self, mode):
        archs = set()
        for a, m, p, q in self.results.keys():
            if m == mode:
                archs.add(a)
        return archs


class BaseBenchmark(ABC):
    """
    Base class for benchmark reporting.
    """

    def __init__(self, data: BenchmarkData):
        self.data = data

    @abstractmethod
    def report(self):
        pass

    def compare_architectures(self, mode, P, Q):
        # Compare bare-metal and kvm for given mode, P, Q if both exist
        bm_stats = self.data.get_stats("bare-metal", mode, P, Q)
        kvm_stats = self.data.get_stats("kvm", mode, P, Q)
        if bm_stats and kvm_stats:
            # Compute percentage difference in Gflops
            # ((kvm_gflops - bm_gflops)/bm_gflops)*100
            bm_gflops = bm_stats[2]
            kvm_gflops = kvm_stats[2]
            diff_pct = ((kvm_gflops - bm_gflops) / bm_gflops) * 100.0
            return (bm_stats, kvm_stats, diff_pct)
        return (None, None, None)


class CoopBenchmark(BaseBenchmark):
    """
    Reporting class for 'coop' mode.
    We show average performance for each configuration and compare BM vs KVM.
    """

    def report(self):
        print("\n=== COOP MODE REPORT ===")
        configs = self.data.get_configurations("coop")

        # Group by (P,Q) to display comparisons
        pq_set = sorted(set((p, q) for (a, p, q) in configs))
        for p, q in pq_set:
            print(f"\nAverage coop with N={N} NB={NB} P={p} Q={q}:")
            bm_stats, kvm_stats, diff_pct = self.compare_architectures("coop", p, q)
            if bm_stats and kvm_stats:
                # bm_stats = (mean_t, std_t, mean_gf, std_gf, count)
                print(f"  KVM: time={kvm_stats[0]:.2f}s gflops={kvm_stats[2]:.2f}")
                print(f"  BM : time={bm_stats[0]:.2f}s gflops={bm_stats[2]:.2f}")
                print(f"  % Gflops diff (KVM vs BM) = {diff_pct:.2f}%")
            else:
                # If we don't have both archs, just print what we have
                for arch in ["bare-metal", "kvm"]:
                    stats = self.data.get_stats(arch, "coop", p, q)
                    if stats:
                        print(f"  {arch}: time={stats[0]:.2f}s gflops={stats[2]:.2f}")


class CompBenchmark(BaseBenchmark):
    """
    Reporting class for 'comp' mode.
    For comp mode, the user requested:
    - Show average perf or total for all instances?
    The user mentioned:
      "Average perf for all instances KVM {total time sum of all instances, sum of all gflops}"
    We'll interpret this as:
      For each configuration, sum up all runs' times and gflops to represent total parallel performance.
    Then compare KVM and BM and show percentage difference in Gflops.
    """

    def report(self):
        print("\n=== COMP MODE REPORT ===")
        configs = self.data.get_configurations("comp")
        pq_set = sorted(set((p, q) for (a, p, q) in configs))

        for p, q in pq_set:
            print(f"\nComp mode with N={N} NB={NB} P={p} Q={q}:")
            # We'll sum times and gflops
            bm_values = self.data.results.get(("bare-metal", "comp", p, q), [])
            kvm_values = self.data.results.get(("kvm", "comp", p, q), [])

            bm_total_time = sum([x[0] for x in bm_values])
            bm_total_gflops = sum([x[1] for x in bm_values])
            kvm_total_time = sum([x[0] for x in kvm_values])
            kvm_total_gflops = sum([x[1] for x in kvm_values])

            # Print results if any
            if bm_values:
                print(
                    f"  BM : total_time={bm_total_time:.2f}s total_gflops={bm_total_gflops:.2f}"
                )
            if kvm_values:
                print(
                    f"  KVM: total_time={kvm_total_time:.2f}s total_gflops={kvm_total_gflops:.2f}"
                )

            if bm_values and kvm_values and bm_total_gflops != 0:
                diff_pct = (
                    (kvm_total_gflops - bm_total_gflops) / bm_total_gflops
                ) * 100.0
                print(f"  % Gflops diff (KVM vs BM) = {diff_pct:.2f}%")


def main():
    # List of files to process
    files = [
        "bm_comp_res.txt",
        "bm_coop_res.txt",
        "kvm_comp_res.txt",
        "kvm_coop_res.txt",
    ]

    data = BenchmarkData()
    if not data.load_files(files):
        return

    # Create reporters
    coop_reporter = CoopBenchmark(data)
    comp_reporter = CompBenchmark(data)

    # Print a general performance comparison report (like original)
    print("Performance Comparison Report")
    print("=" * 50)
    print("Format: (Architecture, Mode, P, Q) - Mean Gflops ± StdDev (Count)")
    print("=" * 50)

    # Sorted keys for a brief summary
    sorted_keys = sorted(data.get_all_keys(), key=lambda x: (x[0], x[1], x[2], x[3]))
    for key in sorted_keys:
        (arch, mode, P, Q) = key
        stats = data.get_stats(arch, mode, P, Q)
        if stats:
            mean_t, std_t, mean_g, std_g, count = stats
            print(f"{key}: {mean_g:.2f} ± {std_g:.2f} Gflops (n={count})")

    # Detailed reports
    coop_reporter.report()
    comp_reporter.report()


if __name__ == "__main__":
    main()
