# menu_handler.py

import os
import time
from datetime import datetime
from typing import Any, Dict, List

import logic
from node_api import NodeAPI

class MenuHandler:

    NODES_LIST: List[Dict[str, Any]] = []

    def __init__(self):
       
        self.commands = {
            "1": ("Display registered nodes", self.display_nodes),
            "2": ("Reload nodes", self.reload_nodes),
            "3": ("Launch competitive benchmark", self.run_competitive_benchmark),
            "4": ("Launch cooperative benchmark", self.run_cooperative_benchmark),
            "5": ("Exit", self.exit_menu),
        }

    def register_node(self, ip: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new node with the master server.
        Remove duplicate entries if the node ip/port is already registered.
        """

        for node in self.NODES_LIST:
            if node["ip"] == ip and node["data"] == data:
                self.NODES_LIST.remove(node)
                print(f"Node {ip} is already registered. Updating the entry.")
                break

        node_entry = {
            "ip": ip,
            "data": data,
            "registered_at": datetime.now().isoformat(),
        }
        self.NODES_LIST.append(node_entry)
        return node_entry
    
    def reload_nodes(self) -> None:
        """
        Send a ping request to all registered nodes to update their status.
        If a node is not reachable, remove it from the list.
        """
        for node in self.NODES_LIST:
            ip = node["ip"]
            port = node["data"].get("metrics", {}).get("node_port", 5000)
            node_api = NodeAPI(ip, port)
            if not node_api.ping():
                print(f"Node {ip} is not reachable. Removing from the list.")
                self.NODES_LIST.remove(node)

    def display_nodes(self) -> None:
        if not self.NODES_LIST:
            print("No nodes registered")
            return

        print("\nRegistered Nodes:\n" + "-" * 50)
        for idx, node in enumerate(self.NODES_LIST, start=1):
            metrics = node['data']['metrics']
            print(
                f"Node {idx}:\n"
                f"IP: {node['ip']}\n"
                f"CPU Count: {metrics['cpu_count']}\n"
                f"Total RAM: {metrics['total_ram_gb']:.2f} GB\n"
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

    def run_cooperative_benchmark(self) -> None:
        benchmark_params = self.prompt_for_params(["ps", "qs", "n_value", "nb", "node_slots"])
        logic.launch_cooperative_benchmark(self.NODES_LIST, benchmark_params=benchmark_params)


    def run_competitive_benchmark(self) -> None:
        benchmark_params = self.prompt_for_params(["ps", "qs", "n", "nb", "instances_num"])
        logic.launch_competitive_benchmark(self.NODES_LIST, benchmark_params=benchmark_params)


    def clear_screen(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')

    def exit_menu(self) -> bool:
        return True

    def run(self) -> None:
        # Sleep 2 seconds to allow the server to start
        print("Waiting for server to start...")
        time.sleep(1)
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
