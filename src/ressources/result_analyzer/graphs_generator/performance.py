"""
performance.py

Defines a class that generates performance graphs.
It uses the shared graph plotting function from tools.py with
the performance settings (data_index=1, y_label="Performance (Mbps)").
"""

from tools import plot_config_graph

class PerformanceGraph:
    def generate(self, config, base_dir, out_dir):
        """
        Generate a performance graph for the provided configuration.
        Uses column index 1 (the second column) as the performance metric.
        """
        plot_config_graph(config, base_dir, out_dir, data_index=1, y_label="Bandwidth (Mbps)")
