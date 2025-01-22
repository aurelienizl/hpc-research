# MultiBenchmarkResult.py
from statistics import mean, stdev, variance
from typing import Dict, Any
from pathlib import Path
from result_builder.BenchmarkResult import BenchmarkResult


class MultiBenchmarkResult: 
    def __init__(self, root_folder: Path, collect_keywords: list):
        """
        Initializes the MultiBenchmarkResult by scanning the root_folder for benchmarks.
        Benchmarks are grouped by similar node sets and HPL configuration parameters.
        """
        self.root_folder = root_folder
        self.collect_keywords = collect_keywords
        # Groups: dictionary where key = (node_ips, config) and value = list of BenchmarkResult instances
        self.groups = {}    
        self.load_all_benchmarks()

    def load_all_benchmarks(self):
        """
        Scans subdirectories of root_folder to load BenchmarkResults and groups similar ones.
        """
        for folder in self.root_folder.iterdir():
            if folder.is_dir():
                # Load a single benchmark from the directory
                benchmark = BenchmarkResult(folder, self.collect_keywords)
                # Skip empty benchmark results
                if not benchmark.node_results:
                    continue
                
                # Use the first node and its first HPL result as representative for grouping
                first_node = benchmark.node_results[0]
                # Ensure there's at least one HPL result to extract configuration
                if not first_node.hpl_results:
                    continue

                first_hpl = first_node.hpl_results[0]
                # Create a sorted tuple of node IPs present in this benchmark
                node_ips = tuple(sorted(node.ip_address for node in benchmark.node_results))
                # Use HPL parameters from the first HPL result as a configuration signature
                config = (first_hpl.N, first_hpl.NB, first_hpl.P, first_hpl.Q)
                # Group by a combined signature of node_ips and configuration parameters
                key = (node_ips, config)
                if key not in self.groups:
                    self.groups[key] = []
                self.groups[key].append(benchmark)

    @property
    def group_summary(self) -> Dict[Any, Dict[str, float]]:
        """
        Summarize key metrics for each group of benchmarks with added statistical measures.
        """
        summary = {}
        for group_key, benchmarks in self.groups.items():
            # Collect metrics across all benchmarks in this group
            total_gflops_list = [b.hpl_total_gflops for b in benchmarks if b.hpl_total_gflops is not None]
            avg_gflops_list = [b.hpl_average_gflops for b in benchmarks if b.hpl_average_gflops is not None]
            min_gflops_list = [b.hpl_min_gflops for b in benchmarks if b.hpl_min_gflops is not None]
            max_gflops_list = [b.hpl_max_gflops for b in benchmarks if b.hpl_max_gflops is not None]
            avg_time_list    = [b.hpl_average_time for b in benchmarks if b.hpl_average_time is not None]
            total_time_list  = [b.hpl_total_time for b in benchmarks if b.hpl_total_time is not None]

            # Compute aggregated statistics
            group_stats = {
                "mean_total_gflops": mean(total_gflops_list) if total_gflops_list else None,
                "stdev_total_gflops": stdev(total_gflops_list) if len(total_gflops_list) > 1 else 0.0,
                "var_total_gflops": variance(total_gflops_list) if len(total_gflops_list) > 1 else 0.0,
                
                "mean_avg_gflops": mean(avg_gflops_list) if avg_gflops_list else None,
                "stdev_avg_gflops": stdev(avg_gflops_list) if len(avg_gflops_list) > 1 else 0.0,
                "var_avg_gflops": variance(avg_gflops_list) if len(avg_gflops_list) > 1 else 0.0,
                
                "min_of_min_gflops": min(min_gflops_list) if min_gflops_list else None,
                "max_of_max_gflops": max(max_gflops_list) if max_gflops_list else None,
                
                "mean_avg_time": mean(avg_time_list) if avg_time_list else None,
                "stdev_avg_time": stdev(avg_time_list) if len(avg_time_list) > 1 else 0.0,
                "var_avg_time": variance(avg_time_list) if len(avg_time_list) > 1 else 0.0,
                
                "mean_total_time": mean(total_time_list) if total_time_list else None,
                "stdev_total_time": stdev(total_time_list) if len(total_time_list) > 1 else 0.0,
                "var_total_time": variance(total_time_list) if len(total_time_list) > 1 else 0.0,
                
                "runs_count": len(benchmarks)
            }

            summary[group_key] = group_stats

        return summary

    @property
    def overall_summary(self) -> Dict[str, float]:
        """
        Provides an overall summary across all benchmarks, including statistical measures.
        """
        all_total_gflops = []
        all_avg_gflops = []
        all_avg_times = []
        all_total_times = []

        for benchmarks in self.groups.values():
            for b in benchmarks:
                if b.hpl_total_gflops is not None:
                    all_total_gflops.append(b.hpl_total_gflops)
                if b.hpl_average_gflops is not None:
                    all_avg_gflops.append(b.hpl_average_gflops)
                if b.hpl_average_time is not None:
                    all_avg_times.append(b.hpl_average_time)
                if b.hpl_total_time is not None:
                    all_total_times.append(b.hpl_total_time)

        return {
            "overall_mean_total_gflops": mean(all_total_gflops) if all_total_gflops else None,
            "overall_stdev_total_gflops": stdev(all_total_gflops) if len(all_total_gflops) > 1 else 0.0,
            "overall_var_total_gflops": variance(all_total_gflops) if len(all_total_gflops) > 1 else 0.0,
            
            "overall_mean_avg_gflops": mean(all_avg_gflops) if all_avg_gflops else None,
            "overall_stdev_avg_gflops": stdev(all_avg_gflops) if len(all_avg_gflops) > 1 else 0.0,
            "overall_var_avg_gflops": variance(all_avg_gflops) if len(all_avg_gflops) > 1 else 0.0,
            
            "overall_mean_avg_time": mean(all_avg_times) if all_avg_times else None,
            "overall_stdev_avg_time": stdev(all_avg_times) if len(all_avg_times) > 1 else 0.0,
            "overall_var_avg_time": variance(all_avg_times) if len(all_avg_times) > 1 else 0.0,
            
            "overall_mean_total_time": mean(all_total_times) if all_total_times else None,
            "overall_stdev_total_time": stdev(all_total_times) if len(all_total_times) > 1 else 0.0,
            "overall_var_total_time": variance(all_total_times) if len(all_total_times) > 1 else 0.0,
            
            "total_runs": sum(len(benchmarks) for benchmarks in self.groups.values())
        }

