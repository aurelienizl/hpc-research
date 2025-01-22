# BenchmarkResult.py
from pathlib import Path
from result_builder.NodeResult import NodeResult
from result_builder.tools.mixins import HPLAggregationsMixin  

class BenchmarkResult(HPLAggregationsMixin):
    def __init__(self, benchmark_folder: Path, collect_keywords: list):
        self.benchmark_folder = benchmark_folder
        self.node_results = []
        self.collect_keywords = collect_keywords
        self.load_nodes()

    def load_nodes(self):
        for node_dir in self.benchmark_folder.iterdir():
            if node_dir.is_dir():
                node_result = NodeResult(node_dir, self.collect_keywords)
                self.node_results.append(node_result)

    def all_hpl_results(self):
        results = []
        for node in self.node_results:
            results.extend(node.hpl_results)
        return results

    @property
    def hpl_total_gflops(self):
        return self._aggregate_hpl('gflops', sum, source='benchmark')

    @property
    def hpl_average_gflops(self):
        return self._aggregate_hpl('gflops', self._average, source='benchmark')

    @property
    def hpl_min_gflops(self):
        return self._aggregate_hpl('gflops', min, source='benchmark')

    @property
    def hpl_max_gflops(self):
        return self._aggregate_hpl('gflops', max, source='benchmark')

    @property
    def hpl_average_time(self):
        return self._aggregate_hpl('time', self._average, source='benchmark')

    @property
    def hpl_total_time(self):
        return self._aggregate_hpl('time', sum, source='benchmark')

    # For per-node properties, we can still delegate to each NodeResult
    @property
    def hpl_total_gflops_per_node(self):
        return [(node.ip_address, node.hpl_total_gflops) for node in self.node_results]
        
    @property
    def hpl_average_gflops_per_node(self):
        return [(node.ip_address, node.hpl_average_gflops) for node in self.node_results]

    @property 
    def hpl_average_time_per_node(self):
        return [(node.ip_address, node.hpl_average_time) for node in self.node_results]
    
    def __str__(self):
        # Customize the string representation for a benchmark result
        config_summary = ""
        if self.node_results and self.node_results[0].hpl_results:
            first_hpl = self.node_results[0].hpl_results[0]
            config_summary = f"(N={first_hpl.N}, NB={first_hpl.NB}, P={first_hpl.P}, Q={first_hpl.Q})"
        return (f"Benchmark on Nodes: {[node.ip_address for node in self.node_results]} "
                f"Config: {config_summary} - Total GFLOPS: {self.hpl_total_gflops}, "
                f"Avg GFLOPS/node: {self.hpl_average_gflops_per_node}")

