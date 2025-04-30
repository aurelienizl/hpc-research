"""
latency.py

Defines a class that generates latency graphs.
It uses the shared graph plotting function from tools.py with
the latency settings (data_index=2, y_label="Latency (usec)").
"""

from tools import plot_config_graph

class LatencyGraph:
    def generate(self, config, base_dir, out_dir):
        """
        Generate a latency graph for the provided configuration.
        Uses column index 2 (the third column) as the latency metric.
        """
        plot_config_graph(config, base_dir, out_dir, data_index=2, y_label="Latency (usec)")
