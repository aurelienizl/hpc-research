# MultiHPLGraphBuilder.py
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Any

class MultiHPLGraphBuilder:
    def __init__(self, multi_benchmark_result):
        """
        Initialize the graph builder with a MultiBenchmarkResult object.
        """
        self.multi_benchmark = multi_benchmark_result
        # Optionally set a style for better visuals
        sns.set(style="whitegrid")
    
    def _generate_labels(self, group_keys):
        """
        Generate simplified labels for each group showing number of nodes and configuration.
        """
        labels = []
        for key in group_keys:
            node_ips, config = key
            num_nodes = len(node_ips)
            N, NB, P, Q = config
            label = f"{num_nodes} nodes | N={N}, NB={NB}, P={P}, Q={Q}"
            labels.append(label)
        return labels

    def plot_mean_total_gflops_per_group(self):
        """
        Plot a horizontal bar chart of mean total GFLOPS per group.
        """
        summary = self.multi_benchmark.group_summary
        groups = list(summary.keys())
        mean_total_gflops = [group_stats['mean_total_gflops'] for group_stats in summary.values()]
        
        # Use simplified labels: number of nodes and configuration
        labels = self._generate_labels(groups)
        
        plt.figure(figsize=(12, 8))
        # Create a horizontal bar chart
        sns.barplot(x=mean_total_gflops, y=labels, palette="Blues_d")
        plt.xlabel('Mean Total GFLOPS')
        plt.ylabel('Benchmark Group')
        plt.title('Mean Total GFLOPS per Benchmark Group')
        plt.tight_layout()
        plt.show()
    
    def plot_mean_average_gflops_per_group(self):
        """
        Plot a horizontal bar chart of mean average GFLOPS per group.
        """
        summary = self.multi_benchmark.group_summary
        groups = list(summary.keys())
        mean_avg_gflops = [group_stats['mean_avg_gflops'] for group_stats in summary.values()]
        
        labels = self._generate_labels(groups)
        
        plt.figure(figsize=(12, 8))
        sns.barplot(x=mean_avg_gflops, y=labels, palette="Greens_d")
        plt.xlabel('Mean Average GFLOPS')
        plt.ylabel('Benchmark Group')
        plt.title('Mean Average GFLOPS per Benchmark Group')
        plt.tight_layout()
        plt.show()
    
    def plot_gflops_variance_per_group(self):
        """
        Plot a horizontal bar chart of GFLOPS variance per group.
        """
        summary = self.multi_benchmark.group_summary
        groups = list(summary.keys())
        var_total_gflops = [group_stats['var_total_gflops'] for group_stats in summary.values()]
        
        labels = self._generate_labels(groups)
        
        plt.figure(figsize=(12, 8))
        sns.barplot(x=var_total_gflops, y=labels, palette="Oranges_d")
        plt.xlabel('Variance of Total GFLOPS')
        plt.ylabel('Benchmark Group')
        plt.title('GFLOPS Variance per Benchmark Group')
        plt.tight_layout()
        plt.show()
    
    def plot_overall_gflops_distribution(self):
        """
        Plot a histogram of all total GFLOPS across all benchmarks.
        """
        all_total_gflops = []
        
        for group in self.multi_benchmark.groups.values():
            for benchmark in group:
                if benchmark.hpl_total_gflops is not None:
                    all_total_gflops.append(benchmark.hpl_total_gflops)
        
        plt.figure(figsize=(10, 6))
        sns.histplot(all_total_gflops, bins=30, kde=True, color='mediumpurple')
        plt.xlabel('Total GFLOPS')
        plt.ylabel('Frequency')
        plt.title('Overall Distribution of Total GFLOPS Across All Benchmarks')
        plt.tight_layout()
        plt.show()
    
    def plot_overall_summary(self):
        """
        Plot key overall summary metrics in a single figure.
        """
        overall = self.multi_benchmark.overall_summary
        metrics = {
            'Mean Total GFLOPS': overall.get('overall_mean_total_gflops', 0),
            'Std Dev Total GFLOPS': overall.get('overall_stdev_total_gflops', 0),
            'Mean Avg GFLOPS': overall.get('overall_mean_avg_gflops', 0),
            'Std Dev Avg GFLOPS': overall.get('overall_stdev_avg_gflops', 0),
            'Mean Avg Time (s)': overall.get('overall_mean_avg_time', 0),
            'Std Dev Avg Time (s)': overall.get('overall_stdev_avg_time', 0),
            'Mean Total Time (s)': overall.get('overall_mean_total_time', 0),
            'Std Dev Total Time (s)': overall.get('overall_stdev_total_time', 0),
        }
        
        labels = list(metrics.keys())
        values = list(metrics.values())
        
        plt.figure(figsize=(12, 6))
        sns.barplot(x=labels, y=values, palette="viridis")
        plt.xlabel('Metric')
        plt.ylabel('Value')
        plt.title('Overall Summary Metrics')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()
    
    def save_plot(self, filename: str, dpi=300):
        """
        Save the current plot to a file.
        """
        plt.savefig(filename, dpi=dpi)
        plt.close()
    
    def generate_all_plots(self):
        """
        Generate all available plots.
        """
        self.plot_mean_total_gflops_per_group()
        self.plot_mean_average_gflops_per_group()
        self.plot_gflops_variance_per_group()
        self.plot_overall_gflops_distribution()
        self.plot_overall_summary()
