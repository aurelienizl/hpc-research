import asyncio

from WebClients.WebClient import WebClient
from Log.LogInterface import LogInterface
from Benchmarks.BenchmarksQueue import BenchmarksQueue
from Benchmarks.BenchmarksQueue import BenchmarkInstance
from Benchmarks.BenchmarksAPI import BenchmarksAPI
from Benchmarks.BenchmarkResults import BenchmarkResults

class BenchmarksHandler:

    def __init__(self, config_file: str, clients: WebClient, logger: LogInterface):
        """
        Initialize a handler for benchmarks.

        Args:
            config_file (str): Path to the configuration file
        """
        self.benchmarks_api = BenchmarksAPI()

        self.benchmarks_queue = BenchmarksQueue(logger)
        if not self.benchmarks_queue.load_config_file(config_file):
            raise Exception("Failed to load benchmarks from config file.")

        self.clients = clients
        self.logger = logger

    async def run_benchmarks(self):
        """
        Run all benchmarks in the queue.
        """
        self.logger.info("Processing benchmarks...")
        self.logger.info(f"Displaying all benchmarks: {len(self.benchmarks_queue)}")
        while len(self.benchmarks_queue) > 0:
            benchmark = self.benchmarks_queue.get_next()

            run_count = 0
            while run_count < benchmark.instances_loop:
                self.logger.info(f"Running benchmark: {benchmark.benchmark_name} {benchmark.command_line}")
                self.logger.info(f"Iteration: {run_count + 1}/{benchmark.instances_loop}")

                client_target = [client for client in self.clients 
                            if any(target in client.hostname 
                                    for target in benchmark.target_nodes)]

                iterations = benchmark.instances_parallel
                tasks_id = [benchmark.generate_task_id() for _ in range(iterations)]
                
                # First, launch all benchmarks on all targets
                for task_id in tasks_id:
                    await self.launch_benchmark(benchmark, task_id, client_target, self.logger)
                
                # Then wait for all benchmarks to complete
                for task_id in tasks_id:
                    await self.wait_benchmark(benchmark, task_id, client_target, self.logger)
                
                # Finally, collect and print all results
                for task_id in tasks_id:
                    results = await self.get_results(benchmark, task_id, client_target, self.logger)
                    benchmark_results = BenchmarkResults(benchmark, results, self.logger)
                    benchmark_results.load_results()
                    benchmark_results.save_results()

                run_count += 1
            


    @staticmethod
    async def launch_benchmark(benchmark: BenchmarkInstance, task_id: str, clients: WebClient, logger: LogInterface):
        """
        Asynchronously launch a given benchmark on all clients.
        """
        logger.info(f"Launching benchmark on nodes: {benchmark.target_nodes}")
        tasks = []
        clients_websockets = [client.websocket for client in clients]
        for client in clients_websockets:
            benchmark_name = benchmark.benchmark_name
            command_line = benchmark.command_line
            config_params = benchmark.config_params

            tasks.append(
                BenchmarksAPI.start_benchmark(
                    client, logger, task_id, benchmark_name, command_line, config_params
                )
            )

        await asyncio.gather(*tasks)              

    @staticmethod
    async def get_status(benchmark: BenchmarkInstance, task_id: str, clients: WebClient, logger: LogInterface):
        """
        Asynchronously get status from all clients.
        """
        logger.info(f"Getting status of benchmark: {benchmark.target_nodes}")
        tasks = [
            BenchmarksAPI.get_benchmark_status(client, logger, task_id)
            for client in [client.websocket for client in clients]
        ]
        statuses = await asyncio.gather(*tasks)            
        return statuses

    @staticmethod
    async def wait_benchmark(benchmark: BenchmarkInstance, task_id: str, clients: WebClient, logger: LogInterface):
        """
        Asynchronously wait for the benchmark to complete on all clients.
        """
        logger.info(f"Waiting for benchmark to complete: {benchmark.target_nodes}")
        ready = False
        while not ready:
            await asyncio.sleep(5)
            statuses = await BenchmarksHandler.get_status(benchmark, task_id, clients, logger)
            ready = all(status != "running" for status
                        in statuses)
        return statuses

    @staticmethod
    async def get_results(benchmark: BenchmarkInstance, task_id: str, clients: WebClient, logger: LogInterface):
        """
        Asynchronously get results from all clients.
        
        Returns:
            list: A list of tuples (WebClient, result) containing each client and its associated results
        """
        logger.info(f"Getting results of benchmark: {benchmark.target_nodes}")
        
        # Create tasks with associated clients
        tasks = []
        for client in clients:
            logger.info(f"Getting results from {client}")
            task = BenchmarksAPI.get_benchmark_results(client.websocket, logger, task_id)
            tasks.append((client, task))
        
        # Wait for all results and pair them with their clients
        results = []
        for client, task in tasks:
            result = await task
            results.append((result, client))
            
        return results
    
    @staticmethod
    async def stop_benchmark(benchmark: BenchmarkInstance, task_id: str, clients: WebClient, logger: LogInterface):
        """
        Asynchronously stop the benchmark on all clients.
        """
        logger.info(f"Stopping benchmark: {benchmark.target_nodes}")
        tasks = [
            BenchmarksAPI.stop_benchmark(client, logger, task_id)
            for client in [client.websocket for client in clients]
        ]
        await asyncio.gather(*tasks)

