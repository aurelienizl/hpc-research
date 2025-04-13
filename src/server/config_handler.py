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

    For OpenMPI benchmarks, mpi_processes, mpi_hosts, and mpi_args are used.
    For custom benchmarks, a command_line is provided instead.
    """
    id: str
    type: str
    target_nodes: List[str]
    pre_cmd_exec: Optional[str] = None
    post_cmd_exec: Optional[str] = None
    mpi_processes: Optional[int] = None
    mpi_hosts: List[MPIHost] = field(default_factory=list)
    mpi_args: str = ""
    command_line: Optional[str] = None

@dataclass
class ClusterInstance:
    """
    Represents a cluster configuration containing benchmark instances.
    Now uses a string "name" field instead of a numeric "id".
    """
    name: str
    run_count: int
    pre_process_cmd: str
    post_process_cmd: str
    benchmarks: List[BenchmarkInstance] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> "ClusterInstance":
        # Directly assume all required keys exist.
        benchmarks = []
        for b in data["benchmark"]:
            benchmarks.extend(parse_benchmark(b))
        return cls(
            name=data["name"],
            run_count=data.get("run_count", 1),
            pre_process_cmd=data["pre_process_cmd"],
            post_process_cmd=data["post_process_cmd"],
            benchmarks=benchmarks,
        )

def parse_mpi_hosts(entries: List[str]) -> List[MPIHost]:
    """
    Convert each entry in the mpi_hosts list from "ip:slots" format to an MPIHost instance.
    """
    return [MPIHost(ip=entry.split(":")[0], slots=int(entry.split(":")[1])) for entry in entries]

def parse_benchmark(b: Dict) -> List[BenchmarkInstance]:
    """
    Parse a benchmark configuration and return one or more BenchmarkInstance objects.
    """
    target_nodes = b["target_nodes"]
    pre_cmd_exec = b.get("pre_cmd_exec")
    post_cmd_exec = b.get("post_cmd_exec")
    instances = b.get("instances", 1)

    if "command_line" in b:
        # Custom benchmark: use command_line.
        command_line = b["command_line"]
        mpi_processes = None
        mpi_hosts = []
        mpi_args = ""
    else:
        # OpenMPI benchmark: use MPI settings.
        mpi_processes = b["mpi_processes"]
        mpi_args = b["mpi_args"]
        mpi_hosts = parse_mpi_hosts(b["mpi_hosts"])
        command_line = None

    benchmarks = []
    for i in range(1, instances + 1):
        new_id = b["id"] if instances == 1 else f"{b['id']}-{i}"
        benchmarks.append(BenchmarkInstance(
            id=new_id,
            type=b.get("type", ""),
            target_nodes=target_nodes,
            pre_cmd_exec=pre_cmd_exec,
            post_cmd_exec=post_cmd_exec,
            mpi_processes=mpi_processes,
            mpi_hosts=mpi_hosts,
            mpi_args=mpi_args,
            command_line=command_line,
        ))
    return benchmarks

def load_cluster_instances(file_path: str) -> List[ClusterInstance]:
    """
    Loads a YAML configuration file and creates ClusterInstance objects.
    Expects a top-level key 'cluster_instances' that contains a list of clusters.
    """
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)
    return [ClusterInstance.from_dict(cluster) for cluster in data["cluster_instances"]]

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python config_handler.py <path_to_yaml>")
        sys.exit(1)
    clusters = load_cluster_instances(sys.argv[1])
    for cluster in clusters:
        print(f"Loaded ClusterInstance: {cluster}")
