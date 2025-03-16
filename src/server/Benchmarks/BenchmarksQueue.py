import os
import yaml

from Log.LogInterface import LogInterface

class BenchmarkInstance:
    def __init__(self, benchmark_name: str, command_line: str, config_params: dict, id: str,
                 openmpi_hosts: dict = None, target_nodes: list = None, instances_parallel=None, instances_loop=None):
        """
        Initialize a benchmark instance.
        
        Args:
            benchmark_name (str): Name of the benchmark.
            command_line (str): Command line arguments for the benchmark.
            config_params (dict): Dictionary of configuration parameters.
            openmpi_hosts (dict): Dictionary mapping IP addresses/hostnames to number of slots.
            target_nodes (list): List of IP addresses where the benchmark will be launched.
            instances_parallel (int or str): Number of parallel instances.
            instances_loop (int): Number of loop iterations for the benchmark.
        """
        openmpi_hosts = openmpi_hosts if openmpi_hosts is not None else {}
        openmpi_hosts_str = ' '.join([f"--host {ip} -N {slots}" for ip, slots in openmpi_hosts.items()])
        full_command_line = f"{command_line} {openmpi_hosts_str}"
        
        self.benchmark_name = benchmark_name
        self.command_line = full_command_line
        self.config_params = config_params
        self.openmpi_hosts = openmpi_hosts
        self.target_nodes = target_nodes if target_nodes is not None else []
        self.instances_parallel = instances_parallel
        self.id = id
        self.instances_loop = instances_loop if instances_loop is not None else 1

    def generate_task_id(self) -> str:
        """Generate a unique task ID for the benchmark instance."""
        return os.urandom(16).hex()

    def __str__(self) -> str:
        """Return a string representation of the benchmark instance."""
        return f"""
        Benchmark Instance:
        Benchmark: {self.benchmark_name}
        Command line: {self.command_line}
        Config params: {self.config_params}
        OpenMPI hosts: {self.openmpi_hosts}
        Target nodes: {self.target_nodes}
        Parallel instances: {self.instances_parallel}
        Id: {self.id}
        Instances loop: {self.instances_loop}
        """

class BenchmarksQueue:
    def __init__(self, logger: LogInterface):
        """Initialize an empty queue of benchmarks."""
        self.queue = []
        self.logger = logger

    def load_config_file(self, filename: str) -> bool:
        """
        Load benchmarks from a YAML config file.
        
        Args:
            filename (str): Path to the YAML config file.
        """
        if not os.path.exists(filename):
            self.logger.error(f"Config file not found: {filename}")
            return False

        self.logger.info(f"Loading benchmarks from config file: {filename}")
        try:
            with open(filename, 'r') as f:
                benchmarks = yaml.safe_load(f)
                for bench in benchmarks:
                    name = bench.get('benchmark')
                    cmd = bench.get('command_line', "")
                    params = bench.get('config_params', {})
                    hosts = bench.get('openmpi_hosts', {})
                    target_nodes = bench.get('target_nodes', [])
                    parallel = bench.get('instances_parallel', None)
                    id = bench.get('id', None)
                    instances_loop = bench.get('instances_loop', 1)

                    self.queue.append(BenchmarkInstance(name, cmd, params, id, hosts, target_nodes, parallel, instances_loop))
                    self.logger.info(f"Loaded benchmark: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}")
            return False

    def __len__(self) -> int:
        """Return the number of benchmarks in the queue."""
        return len(self.queue)

    def get_next(self) -> BenchmarkInstance:
        """Return and remove the next benchmark from the queue."""
        if self.queue:
            return self.queue.pop(0)
        return None

    def __str__(self) -> str:
        """Return a string representation of the benchmark queue."""
        return '\n'.join([str(bench) for bench in self.queue])
