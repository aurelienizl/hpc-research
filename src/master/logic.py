import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from node_api import NodeAPI

def wait_benchmark_completion(active_tasks: Dict[str, Dict[str, any]]) -> None:
    while active_tasks:
        for ip, task in list(active_tasks.items()):
            task_id = task["task_id"]
            api = task["api"]
            task_dir = task["dir"]

            status = api.get_task_status(task_id)
            # Could be Error, Running, Completed, or None
            print(f"Task {task_id} on {ip} - Status: {status}")
            if status == "Completed":
                active_tasks.pop(ip)
                print(f"Task {task_id} on {ip} has completed.")
                task_dir.mkdir(exist_ok=True)
                api.get_benchmark_results(task_id, task_dir)
            elif status == "Error":
                active_tasks.pop(ip)
                print(f"Task {task_id} on {ip} has encountered an error.")
            elif status == "Running":
                print(f"Task {task_id} on {ip} is still running.")
            elif status is None:
                active_tasks.pop(ip)
                print(f"Task {task_id} on {ip} is not found.")
        if active_tasks:
            print("Waiting for tasks to complete...")
            time.sleep(10)

def setup_benchmark_environment() -> Path:
    """
    Create a new directory named with the current timestamp to store benchmark results.
    """
    benchmark_dir = Path(
        f"benchmarks/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    )
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    return benchmark_dir

def launch_competitive_benchmark(NodeList: List[Dict[str, Any]], benchmark_params: Dict[str, int]) -> None:
    print("Launching competitive benchmark...")
    # Create a dedicated benchmark results directory
    benchmark_environment = setup_benchmark_environment()

    # Start the master collectl process:
    collectl_log_path = benchmark_environment / "master_collectl.log"
    log_file = open(collectl_log_path, "w")
    print("Starting collectl on master.")
    collectl_proc = subprocess.Popen(
        ["collectl", "-oT", "-scCdmn", "--export", "lexpr"],
        stdout=log_file,
        stderr=subprocess.STDOUT
    )

    try:
        active_tasks = {}
        # Submit benchmark requests to all registered nodes
        for node in NodeList:
            ip = node["ip"]
            port = node["data"].get("metrics", {}).get("node_port", 5000)
            node_api = NodeAPI(ip, port)
            task_id = node_api.submit_competitive_benchmark(
                ps=benchmark_params["ps"],
                qs=benchmark_params["qs"],
                n_value=benchmark_params["n"],
                nb=benchmark_params["nb"],
                instances_num=benchmark_params["instances_num"]
            )

            if task_id:
                node_dir = benchmark_environment / ip
                node_dir.mkdir(exist_ok=True)
                active_tasks[ip] = {
                    "task_id": task_id,
                    "api": node_api,
                    "dir": node_dir,
                }
                print(f"Started benchmark for {ip} - Task ID: {task_id}")
            else:
                print(f"Failed to submit benchmark for {ip}")

        # Wait for all tasks to complete
        wait_benchmark_completion(active_tasks)
    finally:
        # Stop the collectl process as soon as the benchmark run is done
        print("Stopping collectl on master.")
        collectl_proc.terminate()
        collectl_proc.wait()
        log_file.close()

def launch_cooperative_benchmark(NodeList: List[Dict[str, Any]], benchmark_params: Dict[str, int]) -> None:
    print("Launching cooperative benchmark...")
    benchmark_environment = setup_benchmark_environment()

    # Start the master collectl process:
    collectl_log_path = benchmark_environment / "master_collectl.log"
    log_file = open(collectl_log_path, "w")
    print("Starting collectl on master.")
    collectl_proc = subprocess.Popen(
        ["collectl", "-oT", "-scCdmn", "--export", "lexpr"],
        stdout=log_file,
        stderr=subprocess.STDOUT
    )

    try:
        active_tasks = {}

        first_node = NodeList[0]
        ip = first_node["ip"]
        port = first_node["data"].get("metrics", {}).get("node_port", 5000)
        node_slots = {node["ip"]: benchmark_params["node_slots"] for node in NodeList}
        node_api = NodeAPI(ip, port)
        task_id = node_api.submit_cooperative_benchmark(
                ps=benchmark_params["ps"],
                qs=benchmark_params["qs"],
                n_value=benchmark_params["n_value"],
                nb=benchmark_params["nb"],
                node_slots=node_slots
            )

        if task_id:
            active_tasks[ip] = {
                "task_id": task_id,
                "api": node_api,
                "dir": benchmark_environment / ip,
            }
            print(f"Started cooperative benchmark on {ip} - Task ID: {task_id}")
            print("Connected nodes : ", node_slots)

        # Wait for the benchmark to complete
        wait_benchmark_completion(active_tasks)
    finally:
        # Stop the collectl process after the benchmark run
        print("Stopping collectl on master.")
        collectl_proc.terminate()
        collectl_proc.wait()
        log_file.close()

def generate_ssh_key() -> None:
    """
    Generate an SSH key pair at ~/.ssh/id_rsa (private) and ~/.ssh/id_rsa.pub (public),
    if they do not already exist. This mimics the behavior of running `ssh-keygen`
    with default prompts (no passphrase).
    """
    home_dir = os.path.expanduser("~")
    ssh_dir = os.path.join(home_dir, ".ssh")
    private_key_path = os.path.join(ssh_dir, "id_rsa")
    public_key_path = private_key_path + ".pub"

    # Ensure the ~/.ssh directory exists with proper permissions (0700)
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir, mode=0o700)
    else:
        os.chmod(ssh_dir, 0o700)

    # Check if the key already exists to avoid overwriting
    if os.path.exists(private_key_path) or os.path.exists(public_key_path):
        return  # Skip if keys exist

    subprocess.run(
        [
            "ssh-keygen",
            "-t", "rsa",
            "-b", "2048",
            "-f", private_key_path,
            "-N", "",  # No passphrase
            "-q"       # Quiet mode
        ],
        check=True
    )
