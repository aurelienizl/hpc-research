class CmdBuilder:
    def __init__(self, benchmark):
        self.benchmark = benchmark

    def build(self) -> dict:
        # Custom benchmark: just forward
        if self.benchmark.command_line:
            return {
                "pre_cmd": self.benchmark.pre_cmd_exec or "",
                "command_line": self.benchmark.command_line
            }

        # OpenMPI benchmark
        mpi_procs = self.benchmark.mpi_processes
        mpi_args = (self.benchmark.mpi_args.strip() if self.benchmark.mpi_args else "")
        bench_type = (self.benchmark.type.strip() if self.benchmark.type else "")

        main_cmd = f"mpirun -np {mpi_procs} --hostfile hostfile.txt"
        if mpi_args:
            main_cmd += f" {mpi_args}"
        if bench_type:
            main_cmd += f" {bench_type}"

        # Build hostfile generator
        host_entries = [
            f'echo "{h.ip} slots={h.slots}" >> hostfile.txt'
            for h in self.benchmark.mpi_hosts
        ]
        hostfile_cmd = " && ".join(host_entries)

        # Pre-cmd: optional user pre, then create hostfile
        if self.benchmark.pre_cmd_exec:
            pre = f"{self.benchmark.pre_cmd_exec} && touch hostfile.txt && {hostfile_cmd}"
        else:
            pre = f"touch hostfile.txt && {hostfile_cmd}"

        return {
            "pre_cmd": pre,
            "command_line": main_cmd
        }
