"""
main.py

Entry point for generating graphs. This script:
  - Reads the base directory (which should contain the configuration folders)
  - Creates an output folder (output) for saving the resulting graphs
  - Iterates through each configuration folder and generates both performance
    and latency graphs by calling the classes in performance.py and latency.py.
Usage:
    python main.py /path/to/processed
"""

import os
import sys
from tools import ensure_dir
from performance import PerformanceGraph
from latency import LatencyGraph

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py /path/to/processed")
        sys.exit(1)
    
    base_dir = sys.argv[1]
    if not os.path.isdir(base_dir):
        print(f"Provided base directory does not exist: {base_dir}")
        sys.exit(1)
    
    out_dir = os.path.join("output")
    ensure_dir(out_dir)

    # List configuration directories in base_dir (exclude any system directories if needed)
    configs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    # Optionally, exclude specific folders (e.g., "graphs") here if needed.
    if "graphs" in configs:
        configs.remove("graphs")
    
    for config in configs:
        print(f"Processing configuration: {config}")
        perf_graph = PerformanceGraph()
        perf_graph.generate(config, base_dir, out_dir)
        
        latency_graph = LatencyGraph()
        latency_graph.generate(config, base_dir, out_dir)

if __name__ == "__main__":
    main()
