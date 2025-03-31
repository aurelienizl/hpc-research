#!/usr/bin/env python3
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class MPIHost:
    """
    Represents an MPI host with available slots.
    """
    ip: str
    slots: int

@dataclass
class BenchmarkInstance:
    """
    Represents a single benchmark configuration.
    
    For OpenMPI benchmarks, mpi_processes, mpi_hosts, and mpi_args are mandatory.
    For custom benchmarks, a command_line must be provided instead.
    Optional fields pre_cmd_exec and post_cmd_exec will be executed on the target node
    before and after the benchmark.
    """
    id: str  # Supports replica suffixes.
    type: str
    target_nodes: List[str]
    pre_cmd_exec: Optional[str] = None
    post_cmd_exec: Optional[str] = None
    # OpenMPI fields (used if command_line is not provided):
    mpi_processes: Optional[int] = None
    mpi_hosts: List[MPIHost] = field(default_factory=list)
    mpi_args: str = ""
    # Custom command field (if provided, MPI settings must not be provided):
    command_line: Optional[str] = None

@dataclass
class ClusterInstance:
    """
    Represents a cluster configuration containing benchmark instances.
    """
    id: int
    pre_process_cmd: str
    post_process_cmd: str
    hosts: List[str]
    benchmarks: List[BenchmarkInstance] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> "ClusterInstance":
        """
        Create a ClusterInstance from a dictionary.
        
        Validates that required cluster fields are present.
        For each benchmark:
          - If 'command_line' is present, it's a custom benchmark. In that case:
              * 'command_line' is mandatory.
              * MPI settings (mpi_processes, mpi_hosts, mpi_args) must not be provided.
          - Otherwise, it is treated as an OpenMPI benchmark, and mpi_processes, mpi_hosts,
            and mpi_args are mandatory.
          - In both cases, target_nodes is mandatory and must belong to the cluster's hosts.
          - Supports an optional 'instances' field to replicate the benchmark multiple times.
          - Optional fields pre_cmd_exec and post_cmd_exec are stored if provided.
        """
        required_cluster_fields = ['id', 'pre_process_cmd', 'post_process_cmd', 'hosts', 'benchmark']
        for field_name in required_cluster_fields:
            if field_name not in data:
                raise ValueError(f"Missing required cluster field: {field_name}")

        cluster_id = data['id']
        pre_process_cmd = data['pre_process_cmd']
        post_process_cmd = data['post_process_cmd']
        hosts = data['hosts']
        if not isinstance(hosts, list):
            raise ValueError("The 'hosts' field must be a list of IP addresses.")

        benchmarks_data = data['benchmark']
        if not isinstance(benchmarks_data, list):
            raise ValueError("The 'benchmark' field must be a list.")

        benchmarks = []
        benchmark_ids = set()

        for b in benchmarks_data:
            # Validate target_nodes field.
            target_nodes = None
            for key in ['target_nodes', 'target_node', 'target_node(s)']:
                if key in b:
                    target_nodes = b[key]
                    break
            if target_nodes is None:
                raise ValueError("Missing target nodes field in benchmark configuration.")
            if not isinstance(target_nodes, list):
                raise ValueError("The target nodes field must be a list of IP addresses.")
            for ip in target_nodes:
                if ip not in hosts:
                    raise ValueError(f"Benchmark id {b['id']}: target node '{ip}' is not declared in cluster hosts.")

            # Get optional pre_cmd_exec and post_cmd_exec.
            pre_cmd_exec = b.get("pre_cmd_exec")
            post_cmd_exec = b.get("post_cmd_exec")

            # Determine the number of replicas.
            replicas = b.get("instances", 1)
            if not isinstance(replicas, int) or replicas < 1:
                raise ValueError("The 'instances' field must be an integer >= 1.")

            # Determine if benchmark is custom: presence of command_line indicates a custom benchmark.
            is_custom = "command_line" in b

            if is_custom:
                command_line = b.get("command_line")
                if not command_line:
                    raise ValueError(f"Benchmark id {b['id']}: 'command_line' is required for custom benchmarks.")
                # Ensure no MPI settings are provided.
                if any(key in b for key in ['mpi_processes', 'mpi_hosts', 'mpi_args']):
                    raise ValueError(f"Benchmark id {b['id']}: MPI settings are not allowed for custom benchmarks.")
                mpi_processes = None
                mpi_hosts = []
                mpi_args = ""
            else:
                # For OpenMPI benchmarks, require mpi_processes, mpi_hosts, and mpi_args.
                required_mpi_fields = ['mpi_processes', 'mpi_hosts', 'mpi_args']
                for key in required_mpi_fields:
                    if key not in b:
                        raise ValueError(f"Missing required benchmark field: {key} in benchmark configuration for id {b['id']}.")
                mpi_processes = b['mpi_processes']
                mpi_args = b['mpi_args']
                mpi_hosts = []
                for entry in b['mpi_hosts']:
                    try:
                        ip, slots_str = entry.split(':')
                        slots = int(slots_str)
                        if slots <= 0:
                            raise ValueError
                    except Exception:
                        raise ValueError(
                            f"Benchmark id {b['id']}: Invalid mpi_host entry '{entry}'. Must be in format ip:slots with slots as a positive integer."
                        )
                    if ip not in hosts:
                        raise ValueError(
                            f"Benchmark id {b['id']}: mpi_host '{ip}' is not declared in cluster hosts."
                        )
                    mpi_hosts.append(MPIHost(ip=ip, slots=slots))
                total_slots = sum(host.slots for host in mpi_hosts)
                if total_slots != mpi_processes:
                    raise ValueError(
                        f"Benchmark id {b['id']}: mpi_processes value {mpi_processes} does not equal total slots {total_slots} from mpi_hosts."
                    )
                command_line = None

            # Create the specified number of benchmark replicas.
            for i in range(1, replicas + 1):
                new_benchmark_id = f"{b['id']}" if replicas == 1 else f"{b['id']}-{i}"
                if new_benchmark_id in benchmark_ids:
                    raise ValueError(f"Duplicate benchmark id found: {new_benchmark_id}")
                benchmark_ids.add(new_benchmark_id)
                benchmark = BenchmarkInstance(
                    id=new_benchmark_id,
                    type=b.get("type", ""),
                    target_nodes=target_nodes,
                    pre_cmd_exec=pre_cmd_exec,
                    post_cmd_exec=post_cmd_exec,
                    mpi_processes=mpi_processes,
                    mpi_hosts=mpi_hosts,
                    mpi_args=mpi_args,
                    command_line=command_line
                )
                benchmarks.append(benchmark)

        return cls(
            id=cluster_id,
            pre_process_cmd=pre_process_cmd,
            post_process_cmd=post_process_cmd,
            hosts=hosts,
            benchmarks=benchmarks
        )

def load_cluster_instances(file_path: str) -> List[ClusterInstance]:
    """
    Loads a YAML file containing multiple cluster instances.
    
    Expects a top-level key 'cluster_instances' that contains a list of clusters.
    """
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    if "cluster_instances" not in data:
        raise ValueError("Missing required top-level key: cluster_instances")
    clusters = []
    for cluster_data in data["cluster_instances"]:
        cluster = ClusterInstance.from_dict(cluster_data)
        clusters.append(cluster)
    return clusters

# Example usage:
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python config_handler.py <path_to_yaml>")
        sys.exit(1)
    config_file = sys.argv[1]
    try:
        clusters = load_cluster_instances(config_file)
        for cluster in clusters:
            print(f"Loaded ClusterInstance: {cluster}")
    except Exception as e:
        print(f"Error loading configuration: {e}")
