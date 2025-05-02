import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class MPIHost:
    ip: str
    slots: int

@dataclass
class BenchmarkInstance:
    id: str
    type: str
    target_nodes: List[str]
    pre_cmd_exec: Optional[str] = None
    mpi_processes: Optional[int] = None
    mpi_hosts: List[MPIHost] = field(default_factory=list)
    mpi_args: str = ""
    command_line: Optional[str] = None

@dataclass
class ClusterInstance:
    name: str
    run_count: int
    pre_process_cmd: str
    benchmarks: List[BenchmarkInstance] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> "ClusterInstance":
        benches = []
        for b in data.get("benchmark", []):
            benches.extend(parse_benchmark(b))
        return cls(
            name=data["name"],
            run_count=data.get("run_count", 1),
            pre_process_cmd=data.get("pre_process_cmd", ""),
            benchmarks=benches
        )

def parse_mpi_hosts(entries: List[str]) -> List[MPIHost]:
    return [MPIHost(ip=e.split(":" )[0], slots=int(e.split(":" )[1])) for e in entries]


def parse_benchmark(b: Dict) -> List[BenchmarkInstance]:
    target_nodes = b["target_nodes"]
    # Accept both keys for pre-command
    pre_cmd = b.get("pre_cmd_exec") or b.get("pre_process_cmd")
    instances = b.get("instances", 1)

    if b.get("command_line"):
        command_line = b["command_line"]
        mpi_procs = None
        mpi_hosts = []
        mpi_args = ""
    else:
        mpi_procs = b["mpi_processes"]
        mpi_args = b.get("mpi_args", "")
        mpi_hosts = parse_mpi_hosts(b.get("mpi_hosts", []))
        command_line = None

    out = []
    for i in range(1, instances + 1):
        bid = b["id"] if instances == 1 else f"{b['id']}-{i}"
        out.append(BenchmarkInstance(
            id=bid,
            type=b.get("type", ""),
            target_nodes=target_nodes,
            pre_cmd_exec=pre_cmd,
            mpi_processes=mpi_procs,
            mpi_hosts=mpi_hosts,
            mpi_args=mpi_args,
            command_line=command_line
        ))
    return out


def load_cluster_instances(file_path: str) -> List[ClusterInstance]:
    with open(file_path) as f:
        data = yaml.safe_load(f)
    return [ClusterInstance.from_dict(c) for c in data.get("cluster_instances", [])]

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python config_handler.py <path_to_yaml>")
        sys.exit(1)
    clusters = load_cluster_instances(sys.argv[1])
    for c in clusters:
        print(c)
