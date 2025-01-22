# main.py
import sys
from pathlib import Path

from result_builder.MultiBenchmarkResult import MultiBenchmarkResult

""" from report_graph.CollectlGraphBuilder import CollectlGraphBuilder
from report_graph.HPLGraphBuilder import HPLGraphBuilder """

def main():

    collectl_keywords = ["cpuload.avg1", "cpuload.avg5", "cpuload.avg15"]

    benchmark_path = Path(sys.argv[1])
    benchmak_results = MultiBenchmarkResult(benchmark_path, collectl_keywords)

        # Access group-wise summary.
    for group_key, stats in benchmak_results.group_summary.items():
        print(f"Group: {group_key}, Stats: {stats}")

    # Access overall summary across all benchmarks.
    print("Overall Summary:", benchmak_results.overall_summary)
        

if __name__ == "__main__":
    main()
