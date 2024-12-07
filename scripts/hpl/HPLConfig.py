import os
import math
import glob
import subprocess
from pathlib import Path
from typing import Tuple, List, Optional



class HPLConfig:
    """
    A class to generate and manage HPL benchmark configurations for cooperative and competitive setups.
    """

    SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "HPLInstall.sh")


    def __init__(self, output_dir: str = "HPLConfigurations"):
        """
        Initialize the HPLConfig class.

        Args:
            output_dir (str): Base directory to save the generated configurations.
        """
        self.output_dir = output_dir
        print("HPLConfig initialized.")
        self.total_cpus = self._get_total_cpus()
        self.total_memory, self.available_memory, self.usable_memory = self._get_memory_info()
        print(f"System details: {self.total_cpus} CPUs, {self.usable_memory} MB usable memory.")

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
            with open(filepath, 'r') as file:
                return file.readlines()
        except FileNotFoundError:
            print(f"File not found: {filepath}")
            return []

    def _get_total_cpus(self) -> int:
        """
        Fetch the total number of CPUs on the system.

        Returns:
            int: Total number of CPUs.
        """
        cpuinfo = self._read_proc_file("/proc/cpuinfo")
        cpu_count = sum(1 for line in cpuinfo if line.startswith("processor"))
        print(f"Total CPUs detected: {cpu_count}")
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
            parts = line.split(':')
            if len(parts) == 2:
                key, value = parts
                meminfo[key.strip()] = int(value.strip().split()[0])

        total_memory = meminfo.get("MemTotal", 0) // 1024  # Convert to MB
        available_memory = meminfo.get("MemAvailable", 0) // 1024  # Convert to MB
        usable_memory = int(available_memory * 0.85)  # Use 85% of available memory

        print(f"Memory details - Total: {total_memory} MB, Available: {available_memory} MB, Usable: {usable_memory} MB")
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
        print(f"Calculated process grid for {cpu_count} CPUs: Ps={ps}, Qs={qs}")
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
        print(f"Calculated problem size N based on {ram_mb} MB RAM: N={n}")
        return n

    def _generate_hpl_file(
        self,
        cpu_count: int,
        ram_allocation: int,
        output_dir: str,
        instance_id: Optional[int] = None,
        num_instances: Optional[int] = None
    ):
        """
        Generate the HPL configuration file.

        Args:
            cpu_count (int): Number of CPUs for the configuration.
            ram_allocation (int): RAM allocation in MB.
            output_dir (str): Directory to save the configuration file.
            instance_id (Optional[int]): Instance ID for competitive configurations.
            num_instances (Optional[int]): Number of instances for competitive configurations.
        """
        ps, qs = self._calculate_ps_qs(cpu_count)
        n_value = self._calculate_problem_size(ram_allocation)
        nb = 192  # Fixed block size as per template

        if instance_id is not None:
            file_name = f"hpl_{cpu_count}cpu_instance{instance_id}.dat"
        else:
            file_name = f"hpl_{cpu_count}cpu.dat"

        file_path = os.path.join(output_dir, file_name)

        hpl_template = (
            f"HPLinpack benchmark input file\n"
            f"Innovative Computing Laboratory, University of Tennessee\n"
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

        os.makedirs(output_dir, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(hpl_template)
        print(f"HPL file generated: {file_path}")

    def create_cooperative_configs(self):
        """
        Create HPL configurations for cooperative benchmarking.
        """
        print("Generating cooperative benchmark configurations...")
        cpu_counts = self._generate_cpu_counts(self.total_cpus)
        cooperative_dir = os.path.join(self.output_dir, "cooperative")

        for cpu_count in cpu_counts:
            ram_allocation = self.usable_memory // self.total_cpus * cpu_count
            self._generate_hpl_file(cpu_count, ram_allocation, cooperative_dir)

    def create_competitive_configs(self):
        """
        Create HPL configurations for competitive benchmarking.
        """
        print("Generating competitive benchmark configurations...")
        cpu_counts = self._generate_cpu_counts(self.total_cpus)
        competitive_base_dir = os.path.join(self.output_dir, "competitive")

        for cpu_count in cpu_counts:
            num_instances = self.total_cpus // cpu_count
            competitive_dir = os.path.join(competitive_base_dir, f"{num_instances}_instances")
            ram_per_instance = self.usable_memory // num_instances

            for instance_id in range(1, num_instances + 1):
                self._generate_hpl_file(
                    cpu_count,
                    ram_per_instance,
                    competitive_dir,
                    instance_id=instance_id
                )

    def _generate_cpu_counts(self, total_cpus: int) -> List[int]:
        """
        Generate a list of CPU counts by halving the total CPUs until 1.

        Args:
            total_cpus (int): Total number of CPUs.

        Returns:
            List[int]: List of CPU counts.
        """
        cpu_counts = []
        cpu = total_cpus
        while cpu >= 1:
            cpu_counts.append(cpu)
            cpu //= 2
        print(f"Generated CPU counts for configurations: {cpu_counts}")
        return cpu_counts

    def generate_configs(self):
        """
        Generate both cooperative and competitive HPL configurations.
        """
        print("Starting HPL configuration generation...")
        self.create_cooperative_configs()
        self.create_competitive_configs()
        print("All configurations have been generated.")
        print(f"Configurations saved in {self.output_dir}")

    def get_config_paths(self, config_type: str, cpu_count: int) -> List[str]:
        """
        Retrieve the configuration file paths based on the specified type and CPU count.

        Args:
            config_type (str): Type of configuration ('cooperative' or 'competitive').
            cpu_count (int): Number of CPUs for the configuration.

        Returns:
            List[str]: List of configuration file paths. Empty list if no configurations found.
        """
        config_type = config_type.lower()
        config_paths = []

        if config_type == "cooperative":
            # Path: HPLConfigurations/cooperative/hpl_{cpu_count}cpu.dat
            file_path = os.path.join(self.output_dir, "cooperative", f"hpl_{cpu_count}cpu.dat")
            if os.path.isfile(file_path):
                config_paths.append(file_path)
                print(f"Found cooperative configuration: {file_path}")
            else:
                print(f"No cooperative configuration found for {cpu_count} CPUs.")
        elif config_type == "competitive":
            # Competitive configurations are stored in directories like {num_instances}_instances
            if cpu_count == 0:
                print("CPU count cannot be zero for competitive configurations.")
                return config_paths

            num_instances = self.total_cpus // cpu_count
            instance_dir = os.path.join(self.output_dir, "competitive", f"{num_instances}_instances")
            if not os.path.isdir(instance_dir):
                print(f"No competitive configurations directory found for {num_instances} instances.")
                return config_paths

            # Pattern to match files: hpl_{cpu_count}cpu_instance*.dat
            pattern = os.path.join(instance_dir, f"hpl_{cpu_count}cpu_instance*.dat")
            matched_files = glob.glob(pattern)
            if matched_files:
                config_paths.extend(matched_files)
                print(f"Found {len(matched_files)} competitive configurations for {cpu_count} CPUs.")
            else:
                print(f"No competitive configurations found for {cpu_count} CPUs in {instance_dir}.")
        else:
            print(f"Invalid configuration type: {config_type}. Use 'cooperative' or 'competitive'.")

        return config_paths

    @staticmethod
    def install_hpl(script_path: Optional[str] = None):
        """
        Install HPL and its dependencies using a script.

        Args:
            script_path (Optional[str]): Path to the installation script. If not provided, uses the default SCRIPT_PATH.
        """
        script = script_path if script_path else HPLConfig.SCRIPT_PATH
        print("Starting HPL installation...")
        if not Path(script).exists():
            raise FileNotFoundError(f"Installation script not found: {script}")
        try:
            subprocess.run(["bash", script], check=True)
            print("HPL installation completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error during HPL installation: {e}")
            raise
