#!/usr/bin/env python3
import sys
import os
import time
import threading
import argparse
import subprocess

from config_handler import load_cluster_instances
from cmd_builder import CmdBuilder
from benchmark_api import BenchmarkAPI

# Reuse the secret key as defined on the client.
SECRET_KEY = "mySecret123"


def start_collectl(collectl_id: str, output_file: str):
    """
    Starts collectl with default parameters.
    The output is written to 'output_file'. Returns the process handle and the log file descriptor.
    """
    # Ensure the directory for the output file exists.
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
    proc.terminate()  # Send SIGTERM to collectl.
    proc.wait()  # Wait for process termination.
    log_fd.close()  # Close the file descriptor.
    print(f"Collectl with ID {collectl_id} stopped.")


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


def process_benchmark_on_target(benchmark, cluster_dir, target_node):
    """
    Worker function that:
      1. Uses the provided target node to create a client URL.
      2. Builds the commands using CmdBuilder.
      3. Launches the benchmark via BenchmarkAPI on that target node.
      4. Polls until the benchmark is finished.
      5. Retrieves and saves the results.
    """
    client_url = f"http://{target_node}:5000"
    api = BenchmarkAPI(client_url, SECRET_KEY)

    # Build command lines.
    builder = CmdBuilder(benchmark)
    cmds = builder.build()
    pre_cmd = cmds.get("pre_cmd", "")
    main_cmd = cmds.get("command_line", "")
    post_cmd = cmds.get("post_cmd", "")

    # Append target node info to benchmark id for result separation.
    benchmark_id = f"{benchmark.id}_{target_node.replace('.', '_')}"
    print(f"[{benchmark_id}] Launching on {client_url}")
    launch_resp = api.launch_benchmark(main_cmd, pre_cmd_exec=pre_cmd, post_cmd_exec=post_cmd)
    if launch_resp.get("status") != "accepted":
        print(f"[{benchmark_id}] Error launching: {launch_resp.get('message')}")
        return

    task_id = launch_resp.get("task_id")
    print(f"[{benchmark_id}] Launched with task_id: {task_id}")

    time.sleep(90)  # Give some time for the task to start.
    # Poll the benchmark status until it is finished or encounters an error.
    while True:
        status_resp = api.get_status(task_id)
        status = status_resp.get("status")
        print(f"[{benchmark_id}] Status: {status}")
        if status in ["finished", "error"]:
            break
        time.sleep(60)  # Poll every 60 seconds.

    if status == "error":
        print(f"[{benchmark_id}] Benchmark failed with error: {status_resp.get('message')}")
        return

    # Retrieve results.
    results = api.get_results(task_id)
    if results.get("status") != "finished":
        print(f"[{benchmark_id}] Error retrieving results: {results.get('message')}")
        return
    save_results(cluster_dir, benchmark_id, results)


class BenchmarkHandler:
    """
    Processes ClusterInstances sequentially. Within each cluster, all BenchmarkInstances
    are launched simultaneously and processed in parallel.
    """

    def __init__(self, config_file: str, output_folder: str):
        self.config_file = config_file
        self.output_folder = output_folder
        self.clusters = load_cluster_instances(config_file)

    def process_cluster(self, cluster, run):
        """
        Processes all BenchmarkInstances for a single ClusterInstance concurrently.
        Executes cluster-level pre_process_cmd before launching benchmarks
        and post_process_cmd after all benchmarks are finished.
        """
        # If run_count > 1, append the run suffix.
        if cluster.run_count > 1:
            cluster_dir = os.path.join(self.output_folder, f"cluster_{cluster.id}_{run}")
        else:
            cluster_dir = os.path.join(self.output_folder, f"cluster_{cluster.id}")
        os.makedirs(cluster_dir, exist_ok=True)
        print(f"\nProcessing Cluster {cluster.id} run {run} ...")

        # Start collectl monitoring for this cluster run.
        collectl_id = f"cluster_{cluster.id}_run{run}"
        collectl_log = os.path.join(cluster_dir, "collectl.log")
        collectl_proc, log_fd = start_collectl(collectl_id, collectl_log)

        threads = []
        # For each benchmark, launch one thread per target node.
        for benchmark in cluster.benchmarks:
            for target_node in benchmark.target_nodes:
                t = threading.Thread(target=process_benchmark_on_target, args=(benchmark, cluster_dir, target_node))
                threads.append(t)

        # Start all threads.
        for t in threads:
            t.start()

        # Wait for all benchmarks to complete.
        for t in threads:
            t.join()

        # Stop collectl monitoring.
        stop_collectl(collectl_proc, log_fd, collectl_id)

        print(f"Cluster {cluster.id} run {run} processing completed.")

    def process_all(self):
        """
        Processes each ClusterInstance sequentially.
        """
        for cluster in self.clusters:
            self._execute_cmd(cluster.id, cluster.pre_process_cmd, "pre_process_cmd")

            for run in range(1, cluster.run_count + 1):
                self.process_cluster(cluster, run)

            self._execute_cmd(cluster.id, cluster.post_process_cmd, "post_process_cmd")

        print("All benchmarks completed.")

    def _execute_cmd(self, cluster_id, cmd, cmd_type):
        """
        Executes a given command (pre_process_cmd or post_process_cmd) for a cluster.
        """
        if cmd:
            print(f"[Cluster {cluster_id}] Executing {cmd_type}: {cmd}")
            result = subprocess.run(cmd, shell=True)
            if result.returncode != 0:
                print(f"[Cluster {cluster_id}] {cmd_type} failed with return code {result.returncode}")
                raise Exception(f"{cmd_type} failed with return code {result.returncode}")


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
