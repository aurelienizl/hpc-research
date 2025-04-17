#!/usr/bin/env python3
import sys
import os
import time
import threading
import argparse
import subprocess
import argparse

from config_handler import load_cluster_instances
from cmd_builder import CmdBuilder
from benchmark_api import BenchmarkAPI

# Reuse the secret key as defined on the client.
SECRET_KEY = "mySecret123"

def start_collectl(collectl_id: str, output_file: str):
    """
    Starts collectl with default parameters.
    The output is written to 'output_file'.
    """
    log_dir = os.path.dirname(output_file)
    os.makedirs(log_dir, exist_ok=True)
    log_fd = open(output_file, "w")
    proc = subprocess.Popen(
        ["collectl", "-oT", "-scCdmn", "--export", "lexpr"],
        stdout=log_fd,
        stderr=subprocess.STDOUT,
    )
    print(f"Collectl started with ID {collectl_id} (PID {proc.pid}). Output: {output_file}")
    return proc, log_fd

def stop_collectl(proc, log_fd, collectl_id: str):
    """
    Stops the running collectl process.
    """
    proc.terminate()
    proc.wait()
    log_fd.close()
    print(f"Collectl with ID {collectl_id} stopped.")

def save_results(output_dir, benchmark_id, results):
    """
    Saves result files for a given benchmark instance into an output folder.
    """
    bench_out_dir = os.path.join(output_dir, benchmark_id)
    os.makedirs(bench_out_dir, exist_ok=True)

    for file_entry in results.get("results", []):
        fname = file_entry["filename"]
        content = file_entry["content"]
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

def process_benchmark_on_target(benchmark, cluster_dir, target_node):
    """
    Worker function that:
      1. Creates a client URL for the given target node.
      2. Builds and launches the benchmark using BenchmarkAPI.
      3. Polls until the benchmark is finished.
      4. Retrieves and saves the results.
    """
    client_url = f"http://{target_node}:5000"
    api = BenchmarkAPI(client_url, SECRET_KEY)

    builder = CmdBuilder(benchmark)
    cmds = builder.build()
    pre_cmd = cmds.get("pre_cmd", "")
    main_cmd = cmds.get("command_line", "")
    post_cmd = cmds.get("post_cmd", "")

    # Append target node info to benchmark id to separate result files.
    benchmark_id = f"{benchmark.id}_{target_node.replace('.', '_')}"
    print(f"[{benchmark_id}] Launching on {client_url}")
    launch_resp = api.launch_benchmark(main_cmd, pre_cmd_exec=pre_cmd, post_cmd_exec=post_cmd)
    if launch_resp.get("status") != "accepted":
        print(f"[{benchmark_id}] Error launching: {launch_resp.get('message')}")
        return

    task_id = launch_resp.get("task_id")
    print(f"[{benchmark_id}] Launched with task_id: {task_id}")
    time.sleep(60) # Wait for the task to be accepted
    while True:
        status_resp = api.get_status(task_id)
        status = status_resp.get("status")
        print(f"[{benchmark_id}] Status: {status}")
        if status in ["finished", "error"]:
            break
        time.sleep(5)  

    if status == "error":
        print(f"[{benchmark_id}] Benchmark failed with error: {status_resp.get('message')}")
        return

    results = api.get_results(task_id)
    if results.get("status") != "finished":
        print(f"[{benchmark_id}] Error retrieving results: {results.get('message')}")
        return
    save_results(cluster_dir, benchmark_id, results)

class BenchmarkHandler:
    """
    Processes ClusterInstances sequentially. For each cluster, launches all BenchmarkInstances
    concurrently and processes each run in parallel.
    """

    def __init__(self, config_file: str, output_folder: str):
        self.config_file = config_file
        self.output_folder = output_folder
        self.clusters = load_cluster_instances(config_file)

    def process_cluster(self, cluster, run):
        """
        Processes a ClusterInstance for a given run.
        The output folder is named using the cluster's name.
        """
        if cluster.run_count > 1:
            cluster_dir = os.path.join(self.output_folder, f"{cluster.name}_{run}")
        else:
            cluster_dir = os.path.join(self.output_folder, f"{cluster.name}")
        os.makedirs(cluster_dir, exist_ok=True)
        print(f"\nProcessing Cluster {cluster.name} run {run} ...")

        collectl_id = f"{cluster.name}_run{run}"
        collectl_log = os.path.join(cluster_dir, "collectl.log")
        collectl_proc, log_fd = start_collectl(collectl_id, collectl_log)

        threads = []
        for benchmark in cluster.benchmarks:
            for target_node in benchmark.target_nodes:
                t = threading.Thread(target=process_benchmark_on_target, args=(benchmark, cluster_dir, target_node))
                threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stop_collectl(collectl_proc, log_fd, collectl_id)
        print(f"Cluster {cluster.name} run {run} processing completed.")

    def process_all(self):
        """
        Processes each ClusterInstance sequentially.
        """
        for cluster in self.clusters:
            self._execute_cmd(cluster.name, cluster.pre_process_cmd, "pre_process_cmd")
            for run in range(1, cluster.run_count + 1):
                self.process_cluster(cluster, run)
            self._execute_cmd(cluster.name, cluster.post_process_cmd, "post_process_cmd")
        print("All benchmarks completed.")

    def _execute_cmd(self, cluster_name, cmd, cmd_type):
        """
        Executes a given command (pre_process_cmd or post_process_cmd) for a cluster.
        """
        if cmd:
            print(f"[Cluster {cluster_name}] Executing {cmd_type}: {cmd}")
            result = subprocess.run(cmd, shell=True)
            if result.returncode != 0:
                print(f"[Cluster {cluster_name}] {cmd_type} failed with return code {result.returncode}")
                raise Exception(f"{cmd_type} failed with return code {result.returncode}")

def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Handler Script: Launch benchmarks for all YAML configs in a folder and save results."
    )
    parser.add_argument("config_folder", help="Folder containing YAML configuration files.")
    parser.add_argument("--check-config-files", action="store_true",
                        help="Only load and print all configuration files to check for errors.")
    args = parser.parse_args()

    config_folder = args.config_folder
    if not os.path.isdir(config_folder):
        parser.error(f"{config_folder} is not a valid directory.")

    yaml_files = [f for f in os.listdir(config_folder)
                  if f.lower().endswith(('.yaml', '.yml')) and os.path.isfile(os.path.join(config_folder, f))]
    if not yaml_files:
        print(f"No YAML configuration files found in {config_folder}.")
        return

    if args.check_config_files:
        for yaml_file in yaml_files:
            config_path = os.path.join(config_folder, yaml_file)
            print(f"\nChecking {yaml_file}:")
            try:
                clusters = load_cluster_instances(config_path)
                print("  Loaded successfully. Details:")
                for cluster in clusters:
                    print(f"    {cluster}")
            except Exception as e:
                print(f"  Error loading configuration file: {e}")
        return

    output_folder = config_folder  # Use the config folder itself as output folder

    for yaml_file in yaml_files:
        config_path = os.path.join(config_folder, yaml_file)
        print(f"\nProcessing config: {yaml_file}")
        try:
            handler = BenchmarkHandler(config_path, output_folder)
            handler.process_all()
        except Exception as e:
            print(f"Error processing {yaml_file}: {e}")

if __name__ == "__main__":
    main()
