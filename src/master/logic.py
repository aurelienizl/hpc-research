import time
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict

from node_api import NodeAPI

def setup_benchmark_environment() -> Path:
    """
    Create a new directory named with the current timestamp to store benchmark results.
    """
    benchmark_dir = Path(
        f"benchmarks/benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    return benchmark_dir

def launch_and_monitor_competitive(menu_handler, params: Dict[str, int], benchmark_dir: Path) -> None:
    """
    For each registered node, submit a benchmark task and monitor progress.
    Once completed, fetch results and store them in the appropriate directory.
    """
    active_tasks = {}

    # Submit benchmarks to each node.
    for node in menu_handler.nodes:
        ip = node["ip"]
        port = node["data"].get("metrics", {}).get("node_port", 5000)
        node_api = NodeAPI(ip, port)
        task_id = node_api.submit_competitive_benchmark(params)

        if task_id:
            node_dir = benchmark_dir / ip
            node_dir.mkdir(exist_ok=True)
            active_tasks[ip] = {
                "task_id": task_id,
                "api": node_api,
                "dir": node_dir,
            }
            print(f"Started benchmark for {ip} - Task ID: {task_id}")
        else:
            print(f"Failed to submit benchmark for {ip}")

    # Monitor benchmarks until all tasks complete.
    print("\nMonitoring benchmarks...")
    while active_tasks:
        time.sleep(5)
        completed = []

        for ip, task_info in active_tasks.items():
            status = task_info["api"].check_status(task_info["task_id"])

            if not status:
                print(f"Status fetch failed for {ip}")
                completed.append(ip)
            elif status.lower() == "completed":
                # Retrieve results
                success = task_info["api"].get_results(task_info["task_id"], task_info["dir"])
                if success:
                    print(f"Completed benchmark for {ip} - Task ID: {task_info['task_id']}")
                    menu_handler.benchmark_results[ip] = task_info["task_id"]
                completed.append(ip)
            elif status.lower() == "running":
                print(f"Benchmark still running for {ip}...")
            else:
                print(f"Unexpected status '{status}' for {ip}")
                completed.append(ip)

        # Remove completed tasks from the active_tasks dictionary.
        for ip in completed:
            active_tasks.pop(ip, None)

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