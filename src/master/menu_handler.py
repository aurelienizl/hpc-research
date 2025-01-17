# menu_handler.py

import os
import time
from datetime import datetime
from typing import Any, Dict, List

import logic
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
            # New menu entry for cooperative benchmark:
            "5": ("Launch cooperative benchmark", self.run_cooperative_benchmarks),
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
        for idx, node in enumerate(self.nodes, start=1):
            print(
                f"Node {idx}:\n"
                f"IP: {node['ip']}\n"
                f"Registered at: {node['registered_at']}\n"
                f"Data: {node['data']}\n"
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

    def run_benchmarks(self) -> None:
        if not self.nodes:
            print("No nodes registered")
            return
        params = self.prompt_for_params(["ps", "qs", "n_value", "nb", "instances_num"])
        benchmark_dir = logic.setup_benchmark_environment()
        logic.launch_and_monitor(self, params, benchmark_dir)
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
            benchmark_dir = logic.setup_benchmark_environment()
            logic.launch_and_monitor(self, common_params, benchmark_dir)
            if i < iterations - 1:
                print("\nIteration completed. Waiting before next run...")
                time.sleep(10)
        print(f"\nCompleted {iterations} benchmark iterations!")
        input("Press enter to continue...")

    def run_cooperative_benchmarks(self) -> None:
        """
        Launch a new cooperative benchmark using the first registered node.
        """
        if not self.nodes:
            print("No nodes registered")
            return

        # 1) Prompt for standard parameters
        params = self.prompt_for_params(["ps", "qs", "n_value", "nb"])

        # 2) Prompt for the node slot (only one input for all)
        while True:
            try:
                node_slot_value = int(input("Enter the node slot to reserve on the first node: "))
                break
            except ValueError:
                print("Invalid input. Please enter a number for the node slot.")

        # 3) Select the first node
        first_node = self.nodes[0]
        ip = first_node["ip"]
        port = first_node["data"].get("metrics", {}).get("node_port", 5000)

        # 4) Prepare node_slots with just the first node
        node_slots = {ip: node_slot_value}

        # 5) Submit the cooperative benchmark
        node_api = NodeAPI(ip, port)
        task_id = node_api.submit_cooperative_benchmark(
            ps=params["ps"],
            qs=params["qs"],
            n_value=params["n_value"],
            nb=params["nb"],
            node_slots=node_slots
        )

        if task_id:
            print(f"Cooperative benchmark started for node {ip} - Task ID: {task_id}")

            # We can choose to monitor the task similarly to other benchmarks:
            benchmark_dir = logic.setup_benchmark_environment()
            node_dir = benchmark_dir / ip
            node_dir.mkdir(exist_ok=True)

            # Prepare a small "active_tasks" structure for a single node
            active_tasks = {
                ip: {
                    "task_id": task_id,
                    "api": node_api,
                    "dir": node_dir
                }
            }

            print("\nMonitoring cooperative benchmark...")
            while active_tasks:
                time.sleep(5)
                completed = []

                for node_ip, task_info in active_tasks.items():
                    status = task_info["api"].check_status(task_info["task_id"])
                    if not status:
                        print(f"Status fetch failed for {node_ip}")
                        completed.append(node_ip)
                    elif status.lower() == "completed":
                        # Retrieve results
                        success = task_info["api"].get_results(task_info["task_id"], task_info["dir"])
                        if success:
                            print(f"Completed cooperative benchmark for {node_ip} - Task ID: {task_info['task_id']}")
                            self.benchmark_results[node_ip] = task_info["task_id"]
                        completed.append(node_ip)
                    elif status.lower() == "running":
                        print(f"Benchmark still running for {node_ip}...")
                    else:
                        print(f"Unexpected status '{status}' for {node_ip}")
                        completed.append(node_ip)

                for node_ip in completed:
                    active_tasks.pop(node_ip, None)

            print("Cooperative benchmark completed!")
        else:
            print(f"Failed to submit cooperative benchmark for node {ip}")

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
