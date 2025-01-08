from typing import List, Dict, Callable, Optional
from datetime import datetime
from pathlib import Path
import time
from node_api import NodeAPI
import os

class MenuHandler:
    def __init__(self):
        self.nodes: List[Dict] = []
        self.benchmark_results: Dict[str, str] = {}  # ip -> task_id mapping
        self._initialize_commands()

    def _initialize_commands(self) -> None:
        """Initialize the available commands in the menu"""
        self.commands = {
            "1": ("Display registered nodes", self.display_nodes),
            "2": ("Launch benchmark", self.run_benchmarks),
            "3": ("Launch automatic benchmark", self.run_automatic_benchmarks),
            "4": ("Exit", lambda: True),
        }

    def register_node(self, ip: str, data: Dict) -> Dict:
        """Register a new node with its metadata"""
        node_entry = {
            "ip": ip,
            "data": data,
            "registered_at": datetime.now().isoformat(),
        }
        self.nodes.append(node_entry)
        return node_entry

    def display_nodes(self) -> None:
        """Display all registered nodes and their information"""
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

    def _get_benchmark_params(self) -> Dict[str, int]:
        """Get benchmark parameters from user input"""
        params = {}
        param_names = ["ps", "qs", "n_value", "nb", "instances_num"]
        
        for param in param_names:
            while True:
                try:
                    value = input(f"Enter {param} value: ")
                    params[param] = int(value)
                    break
                except ValueError:
                    print(f"Invalid input. Please enter a number for {param}")
        
        return params
    
    def _get_automatic_benchmark_params(self) -> Dict:
        """Get parameters for automatic benchmark"""
        while True:
            try:
                iterations = int(input("Enter number of benchmark iterations: "))
                if iterations > 0:
                    break
                print("Please enter a positive number")
            except ValueError:
                print("Invalid input. Please enter a number")
        
        params = self._get_benchmark_params()
        return {"iterations": iterations, **params}

    def _launch_node_benchmarks(self, params: Dict[str, int], benchmark_dir: Path) -> Dict:
        """Launch benchmarks on all nodes and return active tasks"""
        active_tasks = {}
        
        for node in self.nodes:
            ip = node["ip"]
            port = node["data"].get("metrics", {}).get("node_port", 5000)
            node_api = NodeAPI(ip, port)
            
            # Add delay between node submissions
            if active_tasks:
                time.sleep(5)  # Wait 5 seconds between node submissions
            
            task_id = node_api.submit_benchmark(**params)
            if task_id:
                print(f"Started benchmark for {ip} - Task ID: {task_id}")
                active_tasks[ip] = {
                    'task_id': task_id,
                    'api': node_api,
                    'dir': benchmark_dir / ip
                }
                active_tasks[ip]['dir'].mkdir(exist_ok=True)
            else:
                print(f"Failed to submit benchmark for {ip}")
        
        return active_tasks

    def _monitor_benchmarks(self, active_tasks: Dict) -> None:
        """Monitor all active benchmark tasks until completion"""
        print("\nMonitoring all benchmarks...")
        while active_tasks:
            time.sleep(5)
            completed_nodes = []
            
            for ip, task_info in active_tasks.items():
                status = task_info['api'].check_status(task_info['task_id'])
                
                if not status:
                    print(f"Failed to get status for {ip}")
                    completed_nodes.append(ip)
                    continue
                
                if status.lower() == "completed":
                    if task_info['api'].get_results(task_info['task_id'], task_info['dir']):
                        print(f"Completed benchmark for {ip} - Task ID: {task_info['task_id']}")
                        self.benchmark_results[ip] = task_info['task_id']
                    completed_nodes.append(ip)
                elif status.lower() == "running":
                    print(f"Benchmark still running for {ip}...")
                else:
                    print(f"Unexpected status '{status}' for {ip}")
                    completed_nodes.append(ip)
            
            for ip in completed_nodes:
                active_tasks.pop(ip)

    def _setup_benchmark_environment(self) -> Path:
        """Create and return the benchmark directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        benchmark_dir = Path(f"benchmarks/benchmark_{timestamp}")
        benchmark_dir.mkdir(parents=True, exist_ok=True)
        return benchmark_dir

    def run_automatic_benchmarks(self) -> None:
        """Run benchmarks multiple times automatically"""
        if not self.nodes:
            print("No nodes registered")
            return

        params = self._get_automatic_benchmark_params()
        iterations = params.pop("iterations")
        
        for i in range(iterations):
            print(f"\nStarting benchmark iteration {i+1}/{iterations}")
            benchmark_dir = self._setup_benchmark_environment()
            
            # Wait longer between iterations to ensure nodes are ready
            if i > 0:
                print("Waiting for nodes to be ready...")
                time.sleep(15)  # 15 seconds between iterations
            
            active_tasks = self._launch_node_benchmarks(params, benchmark_dir)
            self._monitor_benchmarks(active_tasks)
            
            # Additional wait after completing all tasks in an iteration
            if i < iterations - 1:
                print("\nCompleted iteration, waiting before next run...")
                time.sleep(10)
        
        print(f"\nCompleted {iterations} benchmark iterations!")

    def _handle_benchmark_status(self, ip: str, status: str, task_info: Dict, completed_nodes: List[str]) -> None:
        """Handle different benchmark status cases"""
        if status == "completed":
            if task_info['api'].get_results(task_info['task_id'], task_info['dir']):
                print(f"Completed benchmark for {ip} - Task ID: {task_info['task_id']}")
                self.benchmark_results[ip] = task_info['task_id']
            completed_nodes.append(ip)
        elif status == "running":
            print(f"Benchmark still running for {ip}...")
        else:
            print(f"Unexpected status '{status}' for {ip}")
            completed_nodes.append(ip)

    def run_benchmarks(self) -> None:
        """Main benchmark execution flow"""
        if not self.nodes:
            print("No nodes registered")
            return

        params = self._get_benchmark_params()
        benchmark_dir = self._setup_benchmark_environment()
        active_tasks = self._launch_node_benchmarks(params, benchmark_dir)
        self._monitor_benchmarks(active_tasks)
        print("\nAll benchmarks completed!")

    def clear_screen(self) -> None:
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def run(self) -> None:
        """Main menu loop"""
        while True:
            self.clear_screen()
            print("\nMaster Server Menu:")
            
            for key, (description, _) in self.commands.items():
                print(f"{key}. {description}")

            choice = input(f"Enter choice (1-{len(self.commands)}): ").strip()

            if not choice:
                continue
            elif choice in self.commands:
                if self.commands[choice][1]():
                    break
                input("\nPress enter to continue...")
            else:
                print("Invalid choice")
                input("\nPress enter to continue...")