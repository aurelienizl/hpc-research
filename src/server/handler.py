#!/usr/bin/env python3
import os
import time
import threading
import subprocess
import argparse

from config_handler import load_cluster_instances
from cmd_builder import CmdBuilder
from benchmark_api import BenchmarkAPI

SECRET_KEY = "mySecret123"


def start_collectl(collectl_id: str, output_file: str):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    log_fd = open(output_file, "w")
    proc = subprocess.Popen(
        ["collectl", "-oT", "-scCdmn", "--export", "lexpr"],
        stdout=log_fd,
        stderr=subprocess.STDOUT,
    )
    print(f"Collectl started with ID {collectl_id} (PID {proc.pid}). Output: {output_file}")
    return proc, log_fd


def stop_collectl(proc, log_fd, collectl_id: str):
    proc.terminate()
    proc.wait()
    log_fd.close()
    print(f"Collectl with ID {collectl_id} stopped.")


def save_results(output_dir, benchmark_id, results):
    bench_out_dir = os.path.join(output_dir, benchmark_id)
    os.makedirs(bench_out_dir, exist_ok=True)
    for entry in results.get("results", []):
        fname = entry["filename"]
        content = entry["content"]
        if not content.strip():
            continue
        dest = os.path.join(bench_out_dir, fname)
        base, ext = os.path.splitext(fname)
        counter = 1
        while os.path.exists(dest):
            dest = os.path.join(bench_out_dir, f"{base}_{counter}{ext}")
            counter += 1
        with open(dest, "w") as f:
            f.write(content)
    print(f"Results saved in {bench_out_dir}")


def init_benchmarks(cluster, run):
    """
    Initialize all benchmarks for this cluster/run.
    Returns a list of dicts: [{ 'benchmark_id', 'node', 'task_id', 'command' }]
    """
    tasks = []
    for bm in cluster.benchmarks:
        cmds = CmdBuilder(bm).build()
        pre_cmd = cmds.get("pre_cmd", "")
        main_cmd = cmds.get("command_line", "")
        for node in bm.target_nodes:
            bid = f"{bm.id}_{node.replace('.', '_')}"
            client_url = f"http://{node}:5000"
            api = BenchmarkAPI(client_url, SECRET_KEY)
            print(f"[{bid}] Initializing on {node}")
            resp = api.init_benchmark(pre_cmd)
            if resp.get("status") != "accepted":
                print(f"[{bid}] Init failed: {resp.get('message')}")
                continue
            tid = resp.get("task_id")
            tasks.append({
                "benchmark_id": bid,
                "node": node,
                "task_id": tid,
                "command": main_cmd
            })
            print(f"[{bid}] Init task_id: {tid}")
    return tasks


def wait_for_ready(tasks):
    """
    Poll each task until its status is 'ready' or 'error'.
    """
    for task in tasks:
        bid = task['benchmark_id']
        node = task['node']
        tid = task['task_id']
        client_url = f"http://{node}:5000"
        api = BenchmarkAPI(client_url, SECRET_KEY)
        while True:
            status = api.get_status(tid).get('status')
            print(f"[{bid}] Init status: {status}")
            if status in ['ready', 'error']:
                task['status'] = status
                break
            time.sleep(2)
        if task['status'] == 'error':
            print(f"[{bid}] Initialization failed.")


def launch_benchmarks(tasks):
    """
    Launch all initialized benchmarks in parallel.
    Updates each dict in tasks with 'status'.
    """
    def _launch(task):
        bid = task['benchmark_id']
        node = task['node']
        tid = task['task_id']
        cmd = task['command']
        client_url = f"http://{node}:5000"
        api = BenchmarkAPI(client_url, SECRET_KEY)
        print(f"[{bid}] Launching on {node}")
        resp = api.launch_benchmark(tid, cmd)
        if resp.get("status") != "accepted":
            print(f"[{bid}] Launch failed: {resp.get('message')}")
            task['status'] = 'error'
        else:
            task['status'] = 'running'
        print(f"[{bid}] Launch response: {task['status']}")

    threads = []
    for task in tasks:
        if task.get('status') != 'ready':
            continue
        t = threading.Thread(target=_launch, args=(task,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()


def retrieve_results(tasks, output_dir):
    """
    Poll all running benchmarks until finished, then fetch and save results.
    """
    for task in tasks:
        bid = task['benchmark_id']
        if task.get('status') != 'running':
            continue
        node = task['node']
        tid = task['task_id']
        client_url = f"http://{node}:5000"
        api = BenchmarkAPI(client_url, SECRET_KEY)
        while True:
            status = api.get_status(tid).get('status')
            print(f"[{bid}] Status: {status}")
            if status in ['finished', 'error']:
                task['status'] = status
                break
            time.sleep(5)
        if task['status'] == 'error':
            print(f"[{bid}] Benchmark failed.")
            continue
        res = api.get_results(tid)
        if res.get('status') != 'finished':
            print(f"[{bid}] Failed to get results: {res.get('message')}")
            continue
        save_results(output_dir, bid, res)


class BenchmarkHandler:
    def __init__(self, config_file: str, output_folder: str):
        self.clusters = load_cluster_instances(config_file)
        self.output_folder = output_folder

    def process_cluster(self, cluster, run):
        cluster_dir = (
            os.path.join(self.output_folder, f"{cluster.name}_{run}")
            if cluster.run_count > 1 else
            os.path.join(self.output_folder, cluster.name)
        )
        os.makedirs(cluster_dir, exist_ok=True)
        print(f"\nProcessing Cluster {cluster.name} run {run} ...")

        collectl_proc, log_fd = start_collectl(
            f"{cluster.name}_run{run}",
            os.path.join(cluster_dir, "collectl.log")
        )

        # 1. init benchmarks
        tasks = init_benchmarks(cluster, run)

        # 1b. wait until all ready
        wait_for_ready(tasks)

        # 2. launch benchmarks
        launch_benchmarks(tasks)

        # 3. retrieve results
        retrieve_results(tasks, cluster_dir)

        stop_collectl(collectl_proc, log_fd, f"{cluster.name}_run{run}")
        print(f"Cluster {cluster.name} run {run} completed.")

    def process_all(self):
        for cluster in self.clusters:
            if cluster.pre_process_cmd:
                print(f"[Cluster {cluster.name}] Pre-process: {cluster.pre_process_cmd}")
                subprocess.run(cluster.pre_process_cmd, shell=True, check=True)
            for run in range(1, cluster.run_count + 1):
                self.process_cluster(cluster, run)
        print("All benchmarks completed.")


def main():
    parser = argparse.ArgumentParser(description="Benchmark Handler Script")
    parser.add_argument("config_folder", help="Folder containing YAML config files.")
    args = parser.parse_args()

    if not os.path.isdir(args.config_folder):
        parser.error(f"{args.config_folder} is not a valid directory.")

    yaml_files = [f for f in os.listdir(args.config_folder)
                  if f.lower().endswith(('.yaml', '.yml'))]
    base = os.getcwd()
    for yf in yaml_files:
        cfg_path = os.path.join(args.config_folder, yf)
        out_dir = os.path.join(base, os.path.splitext(yf)[0])
        os.makedirs(out_dir, exist_ok=True)
        print(f"--> Processing {yf}")
        handler = BenchmarkHandler(cfg_path, out_dir)
        handler.process_all()

if __name__ == "__main__":
    main()
