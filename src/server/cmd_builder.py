#!/usr/bin/env python3
"""
cmd_builder.py

This module defines the CmdBuilder class, which builds the execution commands
for a given BenchmarkInstance.

Usage:
    from cmd_builder import CmdBuilder
    # Assume benchmark is an instance of BenchmarkInstance (loaded from your config).
    builder = CmdBuilder(benchmark)
    cmds = builder.build()
    # cmds is a dictionary with keys "pre_cmd", "command_line", and "post_cmd".
"""

class CmdBuilder:
    def __init__(self, benchmark):
        """
        Initialize the CmdBuilder with a BenchmarkInstance.
        
        :param benchmark: A BenchmarkInstance object.
        """
        self.benchmark = benchmark

    def build(self) -> dict:
        """
        Builds the commands needed for executing the benchmark.
        
        Returns a dictionary with:
          - "pre_cmd": The command to run before the benchmark.
          - "command_line": The main command to run.
          - "post_cmd": The command to run after the benchmark.
        
        If the benchmark is a custom one (i.e. if 'command_line' is provided),
        it simply returns the provided command along with any pre- and post-
        commands.
        
        Otherwise, for an OpenMPI benchmark, it builds:
          - A pre_cmd that creates a hostfile (hostfile.txt) based on mpi_hosts.
          - A main command of the form:
                mpirun -np <mpi_processes> --hostfile hostfile.txt [mpi_args] <benchmark type>
          - The post_cmd as provided.
        """
        # If a custom benchmark, return its command_line and optional pre/post commands.
        if self.benchmark.command_line:
            return {
                "pre_cmd": self.benchmark.pre_cmd_exec or "",
                "command_line": self.benchmark.command_line,
                "post_cmd": self.benchmark.post_cmd_exec or ""
            }
        else:
            # Build the main command for an OpenMPI benchmark.
            mpi_procs = self.benchmark.mpi_processes
            mpi_args = self.benchmark.mpi_args.strip() if self.benchmark.mpi_args else ""
            bench_type = self.benchmark.type.strip() if self.benchmark.type else ""
            
            main_cmd = f"mpirun -np {mpi_procs} --hostfile hostfile.txt"
            if mpi_args:
                main_cmd += f" {mpi_args}"
            if bench_type:
                main_cmd += f" {bench_type}"
            
            # Create the hostfile from each MPIHost entry.
            # Each entry will be formatted as: "ip slots=<slots>"
            host_entries = []
            for mpi_host in self.benchmark.mpi_hosts:
                host_entries.append(f'echo "{mpi_host.ip} slots={mpi_host.slots}" >> hostfile.txt')
            hostfile_cmd = " && ".join(host_entries)
            
            # Build the pre-command: include optional pre_cmd_exec if provided.
            if self.benchmark.pre_cmd_exec:
                pre_cmd = f"{self.benchmark.pre_cmd_exec} && touch hostfile.txt && {hostfile_cmd}"
            else:
                pre_cmd = f"touch hostfile.txt && {hostfile_cmd}"
            
            post_cmd = self.benchmark.post_cmd_exec or ""
            
            return {
                "pre_cmd": pre_cmd,
                "command_line": main_cmd,
                "post_cmd": post_cmd
            }

#if __name__ == "__main__":
#    config_file = "config.yaml"
#    from config_handler import BenchmarkInstance, MPIHost, load_cluster_instances
#    
#    # Example usage:
#    clusters = load_cluster_instances(config_file)
#    for cluster in clusters:
#        for benchmark in cluster.benchmarks:
#            builder = CmdBuilder(benchmark)
#            commands = builder.build()
#            print(f"Commands for benchmark {benchmark.id}:")
#            print(f"Pre-command: {commands['pre_cmd']}")
#            print(f"Main command: {commands['command_line']}")
#            print(f"Post-command: {commands['post_cmd']}")

