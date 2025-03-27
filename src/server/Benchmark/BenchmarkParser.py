import yaml


class BenchmarkInstance:
    """
    Store and manage the information of a single benchmark.
    """

    def __init__(
        self, id, type, custom_params, openmpi_hosts, openmpi_np, targets_list
    ):
        self.id = id
        self.type = type
        self.custom_params = custom_params
        self.openmpi_hosts = openmpi_hosts
        self.openmpi_np = openmpi_np
        self.targets_list = targets_list

        self.command_line = self.__build_command_line()

    def __build_command_line(self) -> str:
        command_line = ""
        if self.openmpi_hosts:
            for ip, processes in self.openmpi_hosts.items():
                command_line += f" --host {ip}:{processes}"
        if self.openmpi_np:
            command_line += f" -np {self.openmpi_np} --bind-to none --mca plm_rsh_agent \"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null\""
        return command_line

    def __repr__(self):
        return (
            f"BenchmarkInstance(id={self.id}, type={self.type}, "
            f"custom_params={self.custom_params}, openmpi_hosts={self.openmpi_hosts}, "
            f"openmpi_np={self.openmpi_np}, targets_list={self.targets_list})"
        )


class ClusterInstance:
    """
    Store and manage benchmark instances that are running on a single cluster.
    Includes pre_processing_cmd and post_processing_cmd.
    """

    def __init__(
        self, id, runs, pre_processing_cmd: str = None, post_processing_cmd: str = None
    ):
        self.id = id
        self.runs = runs
        self.pre_processing_cmd = pre_processing_cmd
        self.post_processing_cmd = post_processing_cmd
        self.benchmark_instances = []

    def add_benchmark_instance(self, benchmark_instance):
        self.benchmark_instances.append(benchmark_instance)

    def __repr__(self):
        return (
            f"ClusterInstance(id={self.id}, runs={self.runs}, "
            f"pre_processing_cmd={self.pre_processing_cmd}, post_processing_cmd={self.post_processing_cmd}, "
            f"benchmark_instances={self.benchmark_instances})"
        )


class ClusterInstances:
    """
    Manage multiple cluster benchmark configurations loaded from a YAML file.
    """

    def __init__(self, file_path):
        self.file_path = file_path
        self.cluster_benchmarks = []

    def load_benchmarks(self):
        with open(self.file_path, "r") as f:
            yaml_data = f.read()
        data = yaml.safe_load(yaml_data)
        cluster_benchmarks = []
        for inst in data:
            cluster = ClusterInstance(
                id=inst["id"],
                runs=inst["runs"],
                pre_processing_cmd=inst.get("pre_processing_cmd"),
                post_processing_cmd=inst.get("post_processing_cmd"),
            )
            for bench in inst.get("benchmark_instance", []):
                bench_instance = BenchmarkInstance(
                    id=bench["benchmark_id"],
                    type=bench["benchmark_type"],
                    custom_params=bench.get("custom_params", {}),
                    openmpi_hosts=bench.get("openmpi_hosts", {}),
                    openmpi_np=bench.get("openmpi_processes"),
                    targets_list=bench.get("target_nodes", []),
                )
                cluster.add_benchmark_instance(bench_instance)
            cluster_benchmarks.append(cluster)
        self.cluster_benchmarks = cluster_benchmarks
