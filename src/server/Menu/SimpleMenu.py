from WebClients import WebClientHandler
from Benchmarks.BenchmarksHandler import BenchmarksHandler  
from Log import LogInterface
import asyncio
import sys

class SimpleMenu:
    def __init__(self, client_handler: WebClientHandler, logger: LogInterface, loop, shutdown_event: asyncio.Event):
        self.client_handler = client_handler
        self.logger = logger
        self.running = True
        self.loop = loop  
        self.shutdown_event = shutdown_event

    def display_menu(self):
        # Clear the terminal
        print("\033c")
        print("Welcome to the Simple Menu")
        print("1. Display all clients")
        print("2. Launch benchmark")
        print("3. Exit")
        sys.stdout.flush()

    def display_clients(self):
        try:
            print("\nConnected clients:")
            clients = self.client_handler.get_clients()
            if not clients:
                print("No clients connected")
            else:
                for client in clients:
                    print(f"- {client}")
            sys.stdout.flush()
        except Exception as e:
            self.logger.error(f"Error displaying clients: {e}")
        print("\nPress Enter to continue...")
        input()

    def run_menu(self):
        """Run the menu loop synchronously in a separate thread."""
        while self.running:
            try:
                self.display_menu()
                choice = input("Enter your choice: ")
                
                if choice == "1":
                    self.display_clients()
                elif choice == "2":
                    future = asyncio.run_coroutine_threadsafe(self.launch_benchmark(), self.loop)
                    try:
                        future.result()
                    except Exception as exc:
                        self.logger.error(f"Error in benchmark: {exc}")
                elif choice == "3":
                    self.running = False
                    print("Exiting...")
                    self.loop.call_soon_threadsafe(self.shutdown_event.set)
                else:
                    print("Invalid choice")
            except Exception as e:
                self.logger.error(f"Menu error: {e}")

    async def launch_benchmark(self):
        try:
            print("\nLaunching benchmark...")
            clients = self.client_handler.get_clients()
            if not clients:
                print("No clients connected")
                return
            bench_handler = BenchmarksHandler("benchmarks.yaml", clients, self.logger)
            await bench_handler.run_benchmarks()
            print("Benchmark execution completed")
        except Exception as e:
            self.logger.error(f"Error launching benchmark: {e}")
            print(f"Failed to launch benchmark: {e}")
        print("\nPress Enter to continue...")
        input()
