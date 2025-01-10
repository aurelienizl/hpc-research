import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, request, jsonify
from node_api import NodeAPI

class MenuHandler:
    def __init__(self):
        self.nodes: List[Dict[str, Any]] = []
        self.benchmark_results: Dict[str, str] = {}
        self.commands = {
            "1": ("Display registered nodes", self.display_nodes),
            "2": ("Launch benchmark", self.run_benchmarks),
            "3": ("Launch automatic benchmark", self.run_automatic_benchmarks),
            "4": ("Exit", self.exit_menu),
        }

    def register_node(self, ip: str, data: Dict[str, Any]) -> Dict[str, Any]:
        node_entry = {
            "ip": ip,
            "data": data,
            "registered_at": datetime.now().isoformat(),
        }
        self.nodes.append(node_entry)
        return node_entry

    def display_nodes(self) -> None:
        if not self.nodes:
            print("No nodes registered")
            return
        print("\nRegistered Nodes:\n" + "-" * 50)
        for idx, node in enumerate(self.nodes, 1):
            print(
                f"Node {idx}:\nIP: {node['ip']}\nRegistered at: {node['registered_at']}\nData: {node['data']}\n"
                + "-" * 50
            )

    def prompt_for_params(self, param_names: List[str]) -> Dict[str, int]:
        params = {}
        for param in param_names:
            while True:
                try:
                    params[param] = int(input(f"Enter {param} value: "))
                    break
                except ValueError:
                    print(f"Invalid input. Please enter a number for {param}.")
        return params

    def _setup_benchmark_environment(self) -> Path:
        benchmark_dir = Path(
            f"benchmarks/benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        benchmark_dir.mkdir(parents=True, exist_ok=True)
        return benchmark_dir

    def _launch_and_monitor(self, params: Dict[str, int], benchmark_dir: Path) -> None:
        active_tasks = {}
        for node in self.nodes:
            ip = node["ip"]
            port = node["data"].get("metrics", {}).get("node_port", 5000)
            node_api = NodeAPI(ip, port)
            task_id = node_api.submit_benchmark(params)
            if task_id:
                node_dir = benchmark_dir / ip
                node_dir.mkdir(exist_ok=True)
                active_tasks[ip] = {"task_id": task_id, "api": node_api, "dir": node_dir}
                print(f"Started benchmark for {ip} - Task ID: {task_id}")
            else:
                print(f"Failed to submit benchmark for {ip}")

        print("\nMonitoring benchmarks...")
        while active_tasks:
            time.sleep(5)
            completed = []
            for ip, task in active_tasks.items():
                status = task["api"].check_status(task["task_id"])
                if not status:
                    print(f"Status fetch failed for {ip}")
                    completed.append(ip)
                elif status.lower() == "completed":
                    if task["api"].get_results(task["task_id"], task["dir"]):
                        print(f"Completed benchmark for {ip} - Task ID: {task['task_id']}")
                        self.benchmark_results[ip] = task["task_id"]
                    completed.append(ip)
                elif status.lower() == "running":
                    print(f"Benchmark still running for {ip}...")
                else:
                    print(f"Unexpected status '{status}' for {ip}")
                    completed.append(ip)
            for ip in completed:
                active_tasks.pop(ip, None)

    def run_benchmarks(self) -> None:
        if not self.nodes:
            print("No nodes registered")
            return
        params = self.prompt_for_params(["ps", "qs", "n_value", "nb", "instances_num"])
        benchmark_dir = self._setup_benchmark_environment()
        self._launch_and_monitor(params, benchmark_dir)
        print("\nAll benchmarks completed!")
        input("Press enter to continue...")

    def run_automatic_benchmarks(self) -> None:
        if not self.nodes:
            print("No nodes registered")
            return
        while True:
            try:
                iterations = int(input("Enter number of benchmark iterations: "))
                if iterations > 0:
                    break
                print("Please enter a positive number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        common_params = self.prompt_for_params(["ps", "qs", "n_value", "nb", "instances_num"])
        for i in range(iterations):
            print(f"\nStarting benchmark iteration {i + 1}/{iterations}")
            if i > 0:
                print("Waiting for nodes to be ready...")
                time.sleep(15)
            benchmark_dir = self._setup_benchmark_environment()
            self._launch_and_monitor(common_params, benchmark_dir)
            if i < iterations - 1:
                print("\nIteration completed. Waiting before next run...")
                time.sleep(10)
        print(f"\nCompleted {iterations} benchmark iterations!")
        input("Press enter to continue...")

    def clear_screen(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')

    def exit_menu(self) -> bool:
        return True

    def run(self) -> None:
        while True:
            self.clear_screen()
            print("\nMaster Server Menu:")
            for key, (desc, _) in self.commands.items():
                print(f"{key}. {desc}")
            choice = input(f"Enter choice (1-{len(self.commands)}): ").strip()
            action = self.commands.get(choice, (None, None))[1]
            if action:
                if action():
                    break
            else:
                print("Invalid choice")
            input("\nPress enter to continue...")

# Flask server setup for node registration
app = Flask(__name__)
menu_handler = MenuHandler()

@app.route("/register", methods=["POST"])
def register():
    node_data = request.get_json() or {}
    node_ip = request.remote_addr  # Directly obtain the client's IP
    print(node_ip)
    node_entry = menu_handler.register_node(node_ip, node_data)
    return jsonify({"status": "registered", "node": node_entry}), 200
