import os
from datetime import datetime
from typing import Any, Dict, List

import logic

class MenuHandler:
    """
    Handles the interactive menu and stores all nodes/benchmark results.
    """

    def __init__(self):
        # Store information about registered nodes.
        self.nodes: List[Dict[str, Any]] = []
        # Store benchmark results, keyed by IP.
        self.benchmark_results: Dict[str, str] = {}

        # Define menu commands.
        self.commands = {
            "1": ("Display registered nodes", self.display_nodes),
            "2": ("Launch competitive benchmark", self.run_benchmarks),
            "3": ("Launch automatic competitive benchmark", self.run_automatic_benchmarks),
            "4": ("Exit", self.exit_menu),
        }

    def register_node(self, ip: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new node given its IP and any additional data.
        """
        node_entry = {
            "ip": ip,
            "data": data,
            "registered_at": datetime.now().isoformat(),
        }
        self.nodes.append(node_entry)
        return node_entry

    def display_nodes(self) -> None:
        """
        Print the list of registered nodes to the console.
        """
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
        """
        Prompt the user for integer values corresponding to each name in param_names.
        Returns a dictionary of these values.
        """
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
        """
        Prompt the user for benchmark parameters, then run benchmarks on all registered nodes.
        """
        if not self.nodes:
            print("No nodes registered")
            return

        params = self.prompt_for_params(["ps", "qs", "n_value", "nb", "instances_num"])
        benchmark_dir = logic.setup_benchmark_environment()
        logic.launch_and_monitor(self, params, benchmark_dir)

        print("\nAll benchmarks completed!")
        input("Press enter to continue...")

    def run_automatic_benchmarks(self) -> None:
        """
        Prompt the user for the number of automatic benchmark iterations, then run them.
        """
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

        # Prompt once for common parameters to use in all iterations.
        common_params = self.prompt_for_params(["ps", "qs", "n_value", "nb", "instances_num"])

        import time
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

    def clear_screen(self) -> None:
        """
        Clear the console screen on Windows or Unix-like systems.
        """
        os.system('cls' if os.name == 'nt' else 'clear')

    def exit_menu(self) -> bool:
        """
        Return True to indicate that the user wants to exit the menu.
        """
        return True

    def run(self) -> None:
        """
        Continuously display the menu and handle user input until 'Exit' is chosen.
        """
        while True:
            self.clear_screen()
            print("\nMaster Server Menu:")
            for key, (desc, _) in self.commands.items():
                print(f"{key}. {desc}")

            choice = input(f"Enter choice (1-{len(self.commands)}): ").strip()
            action = self.commands.get(choice, (None, None))[1]

            if action:
                # If the method returns True, we exit the menu.
                if action():
                    break
            else:
                print("Invalid choice")

            input("\nPress enter to continue...")
