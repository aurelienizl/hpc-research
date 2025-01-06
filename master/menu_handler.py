from typing import List, Dict, Callable
from datetime import datetime
from pathlib import Path
import time
from node_api import NodeAPI


class MenuHandler:
    def __init__(self):
        self.nodes: List[Dict] = []
        self.benchmark_results = {}
        self.commands = {
            "1": ("Display registered nodes", self.display_nodes),
            "2": ("Launch benchmark", self.run_benchmarks),
            "3": ("Exit", lambda: True),
        }

    def register_node(self, ip: str, data: Dict) -> Dict:
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

        print("\nRegistered Nodes:")
        print("-" * 50)
        for idx, node in enumerate(self.nodes, 1):
            print(f"Node {idx}:")
            print(f"IP: {node['ip']}")
            print(f"Registered at: {node['registered_at']}")
            print(f"Data: {node['data']}")
            print("-" * 50)

    def run_benchmarks(self) -> None:
        if not self.nodes:
            print("No nodes registered")
            return

        params = self._get_benchmark_params()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        benchmark_dir = Path(f"benchmarks/benchmark_{timestamp}")
        benchmark_dir.mkdir(parents=True, exist_ok=True)

        print("\nRunning benchmarks...")
        for node in self.nodes:
            self._run_node_benchmark(node, params, benchmark_dir)

    def _get_benchmark_params(self) -> Dict[str, int]:
        return {
            "ps": int(input("Enter ps value: ")),
            "qs": int(input("Enter qs value: ")),
            "n_value": int(input("Enter n value: ")),
            "nb": int(input("Enter nb value: ")),
            "instances_num": int(input("Enter instances number: ")),
        }

    def _run_node_benchmark(self, node: Dict, params: Dict[str, int], benchmark_dir: Path) -> None:
        ip = node["ip"]
        port = node["data"].get("metrics", {}).get("node_port", 5000)
        node_api = NodeAPI(ip, port)
        task_id = node_api.submit_benchmark(**params)
        if not task_id:
            print(f"Failed to submit benchmark for {ip}")
            return
        node_dir = benchmark_dir / ip
        node_dir.mkdir(exist_ok=True)
        print(f"Monitoring benchmark for {ip}...")
        while True:
            time.sleep(5)
            status = node_api.check_status(task_id)
            if not status:
                print(f"Failed to get status for {ip}")
                return
            status = status.lower()
            if status == "completed":
                if node_api.get_results(task_id, node_dir):
                    print(f"Completed benchmark for {ip} - Task ID: {task_id}")
                    self.benchmark_results[ip] = task_id
                return
            elif status == "running":
                print(f"Benchmark still running for {ip}...")
                continue
            else:
                print(f"Unexpected status '{status}' for {ip}")
                return

    def run(self) -> None:
        while True:
            # Clear the screen
            print("\033c", end="")

            print("\nMaster Server Menu:")
            for key, (description, _) in self.commands.items():
                print(f"{key}. {description}")

            choice = input(f"Enter choice (1-{len(self.commands)}): ")

            if choice in self.commands:
                if self.commands[choice][1]():
                    break
                input("Press enter to continue...")
            # Skip simple enter key press
            elif choice == "":
                continue
            else:
                print("Invalid choice")
                input("Press enter to continue...")
