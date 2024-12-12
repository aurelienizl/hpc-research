# hpl/HPLConfig.py

import os
import math
import shutil
import subprocess
from pathlib import Path
from typing import Tuple, List, Optional, Dict
import logging


class HPLConfig:
    """
    Generates and manages HPL benchmark configurations based on user-defined parameters.
    """

    SCRIPT_PATH = Path(__file__).parent / "HPLInstall.sh"
    DEFAULT_RAM_USAGE_PERCENT = 2

    def __init__(self, output_dir: str = "../HPLConfigurations"):
        """
        Initialize the HPLConfig.

        Args:
            output_dir (str): Directory to save the generated configurations.
        """
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("HPLConfig initialized.")

        self.total_cpus = self._get_total_cpus()
        self.total_memory, self.available_memory, self.usable_memory = (
            self._get_memory_info()
        )

        self.logger.info(
            f"System details: {self.total_cpus} CPUs, {self.usable_memory} MB usable memory."
        )

    @staticmethod
    def _read_proc_file(filepath: str) -> List[str]:
        """
        Read and return the lines from a /proc filesystem file.

        Args:
            filepath (str): Path to the /proc file.

        Returns:
            List[str]: Lines from the file.
        """
        try:
            with open(filepath, "r") as file:
                return file.readlines()
        except FileNotFoundError:
            logging.error(f"File not found: {filepath}")
            return []

    def get_total_cpus(self) -> int:
        """
        Fetch the total number of physical CPU cores on the system.
        Returns:
        int: Total number of physical CPU cores.
        """
        cpuinfo = self._read_proc_file("/proc/cpuinfo")
        # Look for 'core id' lines and count unique entries
        core_ids = set()
        for line in cpuinfo:
            if line.startswith("core id"):
                core_id = line.split(':')[1].strip()
                core_ids.add(core_id)
        
        cpu_count = len(core_ids)
        self.logger.info(f"Total physical CPU cores detected: {cpu_count}")
        return cpu_count
        
    def _get_memory_info(self) -> Tuple[int, int, int]:
        """
        Fetch memory details from the system.

        Returns:
            Tuple[int, int, int]: Total memory, available memory, and usable memory (in MB).
        """
        meminfo_lines = self._read_proc_file("/proc/meminfo")
        meminfo = {}
        for line in meminfo_lines:
            parts = line.split(":")
            if len(parts) == 2:
                key, value = parts
                meminfo[key.strip()] = int(value.strip().split()[0])

        total_memory = meminfo.get("MemTotal", 0) // 1024  # Convert to MB
        available_memory = meminfo.get("MemAvailable", 0) // 1024  # Convert to MB
        usable_memory = int(available_memory * 0.85)  # Use 85% of available memory

        self.logger.info(
            f"Memory details - Total: {total_memory} MB, Available: {available_memory} MB, Usable: {usable_memory} MB"
        )
        return total_memory, available_memory, usable_memory

    @staticmethod
    def _calculate_ps_qs(cpu_count: int) -> Tuple[int, int]:
        """
        Calculate Ps and Qs for near-square process grids.

        Args:
            cpu_count (int): Number of CPUs.

        Returns:
            Tuple[int, int]: Ps and Qs values.
        """
        ps = int(math.sqrt(cpu_count))
        while cpu_count % ps != 0 and ps > 1:
            ps -= 1
        qs = cpu_count // ps
        logging.info(f"Calculated process grid for {cpu_count} CPUs: Ps={ps}, Qs={qs}")
        return ps, qs

    @staticmethod
    def _calculate_problem_size(ram_mb: int) -> int:
        """
        Calculate the problem size (N) based on available RAM.

        Args:
            ram_mb (int): Available RAM in MB.

        Returns:
            int: Problem size N.
        """
        ram_bytes = ram_mb * 1024 * 1024  # Convert MB to bytes
        n = int(math.sqrt(ram_bytes / 8))
        logging.info(f"Calculated problem size N based on {ram_mb} MB RAM: N={n}")
        return n

    def _generate_hpl_file(
        self,
        file_name: str,
        n_value: int,
        nb: int,
        ps: int,
        qs: int,
        custom_params: Optional[Dict[str, str]] = None,
    ) -> Path:
        """
        Generate the HPL configuration file.

        Args:
            file_name (str): Name of the configuration file.
            n_value (int): Problem size N.
            nb (int): Block size.
            ps (int): Process grid P.
            qs (int): Process grid Q.
            custom_params (Optional[Dict[str, str]]): Additional custom HPL parameters.

        Returns:
            Path: Path to the generated configuration file.
        """
        config_dir = self.output_dir / "custom"
        config_dir.mkdir(parents=True, exist_ok=True)
        file_path = config_dir / file_name

        hpl_template = (
            f"HPLinpack benchmark input file\n"
            f"Generated by HPLConfig\n"
            f"HPL.out      output file name (if any)\n"
            f"6            device out (6=stdout,7=stderr,file)\n"
            f"1            # of problems sizes (N)\n"
            f"{n_value}    Ns\n"
            f"1            # of NBs\n"
            f"{nb}         NBs\n"
            f"0            PMAP process mapping (0=Row-,1=Column-major)\n"
            f"1            # of process grids (P x Q)\n"
            f"{ps}         Ps\n"
            f"{qs}         Qs\n"
            f"16.0         threshold\n"
            f"1            # of panel fact\n"
            f"2            PFACTs (0=left, 1=Crout, 2=Right)\n"
            f"1            # of recursive stopping criterium\n"
            f"4            NBMINs (>= 1)\n"
            f"1            # of panels in recursion\n"
            f"2            NDIVs\n"
            f"1            # of recursive panel fact.\n"
            f"1            RFACTs (0=left, 1=Crout, 2=Right)\n"
            f"1            # of broadcast\n"
            f"1            BCASTs (0=1rg,1=1rM,2=2rg,3=2rM,4=Lng,5=LnM)\n"
            f"1            # of lookahead depth\n"
            f"1            DEPTHs (>=0)\n"
            f"2            SWAP (0=bin-exch,1=long,2=mix)\n"
            f"64           swapping threshold\n"
            f"0            L1 in (0=transposed,1=no-transposed) form\n"
            f"0            U  in (0=transposed,1=no-transposed) form\n"
            f"1            Equilibration (0=no,1=yes)\n"
            f"8            memory alignment in double (> 0)\n"
            f"##### This line (no. 32) is ignored (it serves as a separator). ######\n"
            f"0                               Number of additional problem sizes for PTRANS\n"
            f"1200 10000 30000                values of N\n"
            f"0                               number of additional blocking sizes for PTRANS\n"
            f"40 9 8 13 13 20 16 32 64        values of NB\n"
        )

        if custom_params:
            for key, value in custom_params.items():
                hpl_template += f"{key} {value}\n"

        with open(file_path, "w") as f:
            f.write(hpl_template)

        self.logger.info(f"HPL configuration file generated at {file_path}")
        return file_path

    def get_config(
        self, cpu_count: int, ram_percent: int, competitive: bool
    ) -> Tuple[Path, int]:
        """
        Retrieve configuration based on CPU count, RAM percentage, and competitive mode.

        Args:
            cpu_count (int): Number of CPUs for the configuration.
            ram_percent (int): Percentage of available RAM to allocate (0 < ram_percent <= 100).
            competitive (bool): Competitive mode flag.

        Returns:
            Tuple[Path, int]: Path to the configuration file and number of instances.
        """
        self.logger.debug(
            f"Generating config for CPU: {cpu_count}, RAM%: {ram_percent}, Competitive: {competitive}"
        )

        if not (0 < ram_percent <= 100):
            raise ValueError("ram_percent must be between 1 and 100.")

        if cpu_count > self.total_cpus:
            raise ValueError(
                f"CPU count ({cpu_count}) exceeds total CPUs ({self.total_cpus})."
            )

        ram_allocation = int(self.available_memory * (ram_percent / 100))
        n_value = self._calculate_problem_size(ram_allocation)
        ps, qs = self._calculate_ps_qs(cpu_count)
        nb = 192  # Fixed block size

        if competitive:
            num_instances = math.ceil(self.total_cpus / cpu_count)
            ram_per_instance = int(ram_allocation / num_instances)
            n_value = self._calculate_problem_size(ram_per_instance)
            self.logger.info(
                f"Competitive mode: {num_instances} instances each with {cpu_count} CPUs and {ram_per_instance} MB RAM."
            )
        else:
            num_instances = 1

        file_name = f"hpl_cpu{cpu_count}_ram{ram_percent}percent_comp{competitive}.dat"
        config_path = self._generate_hpl_file(file_name, n_value, nb, ps, qs)

        return config_path, num_instances

    def get_custom_config(
        self, n: int, nb: int, p: int, q: int, competitive: bool
    ) -> Tuple[Path, int]:
        """
        Retrieve configuration based on direct specification of N, NB, P, Q.

        Args:
            n (int): Problem size N.
            nb (int): Block size.
            p (int): Process grid P.
            q (int): Process grid Q.
            competitive (bool): Competitive mode flag.

        Returns:
            Tuple[Path, int]: Path to the configuration file and number of instances.
        """
        self.logger.debug(
            f"Generating custom config with N={n}, NB={nb}, P={p}, Q={q}, Competitive={competitive}"
        )

        if p * q > self.total_cpus:
            raise ValueError(
                f"Process grid P*Q ({p}*{q}={p*q}) exceeds total CPUs ({self.total_cpus})."
            )

        if competitive:
            num_instances = math.ceil(self.total_cpus / (p * q))
            self.logger.info(
                f"Competitive mode: {num_instances} instances each with {p*q} CPUs."
            )
        else:
            num_instances = 1

        file_name = f"hpl_N{n}_NB{nb}_P{p}_Q{q}.dat"
        config_path = self._generate_hpl_file(file_name, n, nb, p, q)

        return config_path, num_instances

    def install_hpl(self, script_path: Optional[str] = None):
        """
        Install HPL and its dependencies using a script.

        Args:
            script_path (Optional[str]): Path to the installation script. Defaults to SCRIPT_PATH.

        Raises:
            FileNotFoundError: If the installation script is not found.
            subprocess.CalledProcessError: If the installation script fails.
        """
        script = Path(script_path) if script_path else self.SCRIPT_PATH
        self.logger.info(f"Starting HPL installation using script: {script}")

        if not script.exists():
            raise FileNotFoundError(f"Installation script not found: {script}")

        try:
            subprocess.run(["bash", str(script)], check=True)
            self.logger.info("HPL installation completed successfully.")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error during HPL installation: {e}")
            raise
