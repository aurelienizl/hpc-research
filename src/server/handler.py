#!/usr/bin/env python3
import sys
import os
import time
import threading
import argparse

from config_handler import load_cluster_instances
from cmd_builder import CmdBuilder
from benchmark_api import BenchmarkAPI

# Reuse the secret key as defined on the client.
SECRET_KEY = "mySecret123"

def save_results(output_dir, benchmark_id, results):
    """
    Saves result files for a given benchmark instance into an output folder.
    If a file already exists, a suffix is appended to the filename.
    If the content of the file is empty (or contains only whitespace/newline), it is not written.
    """
    bench_out_dir = os.path.join(output_dir, benchmark_id)
    os.makedirs(bench_out_dir, exist_ok=True)
    
    for file_entry in results.get("results", []):
        fname = file_entry["filename"]
        content = file_entry["content"]
        # Skip writing if content is empty or contains only whitespace/newline.
        if not content.strip():
            continue
        dest_file = os.path.join(bench_out_dir, fname)
        counter = 1
        base, ext = os.path.splitext(fname)
        while os.path.exists(dest_file):
            dest_file = os.path.join(bench_out_dir, f"{base}_{counter}{ext}")
            counter += 1
        with open(dest_file, "w") as f:
            f.write(content)
    print(f"Results saved in {bench_out_dir}")

def process_benchmark(benchmark, cluster_dir):
    """
    Worker function that:
      1. Determines the client URL from the benchmark target node.
      2. Builds the commands using CmdBuilder.
      3. Launches the benchmark via BenchmarkAPI.
      4. Polls until the benchmark is finished.
      5. Retrieves and saves the results.
    """
    # Determine the client URL from the first target node.
    target_node = benchmark.target_nodes[0]
    client_url = f"http://{target_node}:5000"
    api = BenchmarkAPI(client_url, SECRET_KEY)
    
    # Build command lines.
    builder = CmdBuilder(benchmark)
    cmds = builder.build()
    pre_cmd = cmds.get("pre_cmd", "")
    main_cmd = cmds.get("command_line", "")
    post_cmd = cmds.get("post_cmd", "")
    
    print(f"[{benchmark.id}] Launching on {client_url}")
    launch_resp = api.launch_benchmark(main_cmd, pre_cmd_exec=pre_cmd, post_cmd_exec=post_cmd)
    if launch_resp.get("status") != "accepted":
        print(f"[{benchmark.id}] Error launching: {launch_resp.get('message')}")
        return

    task_id = launch_resp.get("task_id")
    print(f"[{benchmark.id}] Launched with task_id: {task_id}")
    
    time.sleep(10)  # Give some time for the task to start.
    # Poll the benchmark status until it is finished or encounters an error.
    while True:
        status_resp = api.get_status(task_id)
        status = status_resp.get("status")
        print(f"[{benchmark.id}] Status: {status}")
        if status in ["finished", "error"]:
            break
        time.sleep(10)  # Poll every 10 seconds.
    
    if status == "error":
        print(f"[{benchmark.id}] Benchmark failed with error: {status_resp.get('message')}")
        return

    # Retrieve results.
    results = api.get_results(task_id)
    if results.get("status") != "finished":
        print(f"[{benchmark.id}] Error retrieving results: {results.get('message')}")
        return
    save_results(cluster_dir, benchmark.id, results)

class BenchmarkHandler:
    """
    Processes ClusterInstances sequentially. Within each cluster, all BenchmarkInstances
    are launched simultaneously and processed in parallel.
    """
    def __init__(self, config_file: str, output_folder: str):
        self.config_file = config_file
        self.output_folder = output_folder
        self.clusters = load_cluster_instances(config_file)
    
    def process_cluster(self, cluster):
        """
        Processes all BenchmarkInstances for a single ClusterInstance concurrently.
        """
        cluster_dir = os.path.join(self.output_folder, f"cluster_{cluster.id}")
        os.makedirs(cluster_dir, exist_ok=True)
        print(f"\nProcessing Cluster {cluster.id} ...")
        
        threads = []
        # Create all threads for benchmarks first.
        for benchmark in cluster.benchmarks:
            t = threading.Thread(target=process_benchmark, args=(benchmark, cluster_dir))
            threads.append(t)
        
        # Launch all threads.
        for t in threads:
            t.start()
        
        # Wait for all benchmarks in this cluster to complete.
        for t in threads:
            t.join()
        
        print(f"Cluster {cluster.id} processing completed.")
    
    def process_all(self):
        """
        Processes each ClusterInstance sequentially.
        """
        for cluster in self.clusters:
            self.process_cluster(cluster)
        print("All benchmarks completed.")

def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Handler Script: Launch benchmarks for clusters and save results."
    )
    parser.add_argument("config_file", help="Path to the YAML configuration file.")
    parser.add_argument("output_folder", nargs="?", help="Folder to store benchmark results.")
    parser.add_argument("--check-config-file", action="store_true", 
                        help="Only load and print the configuration file to check for errors.")
    args = parser.parse_args()
    
    # If --check-config-file is provided, load and print the config file.
    if args.check_config_file:
        try:
            clusters = load_cluster_instances(args.config_file)
            print("Configuration file loaded successfully. Details:")
            for cluster in clusters:
                print(cluster)
        except Exception as e:
            print(f"Error loading configuration file: {e}")
        return

    # For normal benchmark execution, ensure output_folder is provided.
    if not args.output_folder:
        parser.error("output_folder is required when not using --check-config-file")
    
    os.makedirs(args.output_folder, exist_ok=True)
    
    handler = BenchmarkHandler(args.config_file, args.output_folder)
    handler.process_all()

if __name__ == "__main__":
    main()
