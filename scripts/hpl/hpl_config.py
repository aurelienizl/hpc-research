import os
import math
from log.log_interface import ShellLogger  # Import the ShellLogger class for logging


class HPLBenchmarkConfig:
    """
    A class to generate HPL benchmark configurations for cooperative and competitive setups.
    """

    def __init__(self, output_dir: str = "hpl_configs", logger: ShellLogger = None):
        """
        Initialize the HPLBenchmarkConfig class.

        Args:
            output_dir (str): Base directory to save the generated configurations.
            logger (ShellLogger): Logger instance for logging messages.
        """
        self.output_dir = output_dir
        self.logger = logger or ShellLogger()
        self.logger.info("HPLBenchmarkConfig initialized.")
        self.total_cpus = self._get_total_cpus()
        self.total_memory, self.available_memory, self.usable_memory = self._get_memory_info()
        self.logger.info(f"System details: {self.total_cpus} CPUs, {self.usable_memory} MB usable memory.")

    def _get_total_cpus(self):
        """
        Fetch the total number of CPUs on the system.
        """
        with open("/proc/cpuinfo") as f:
            return sum(1 for line in f if line.startswith("processor"))

    def _get_memory_info(self):
        """
        Fetch memory details from the system.

        Returns:
            tuple: Total memory, available memory, and usable memory (in MB).
        """
        with open("/proc/meminfo") as f:
            meminfo = {line.split(':')[0]: int(line.split()[1]) for line in f}
        total_memory = meminfo["MemTotal"] // 1024  # Convert to MB
        available_memory = meminfo["MemAvailable"] // 1024  # Convert to MB
        usable_memory = int(available_memory * 0.85)  # Use 85% of available memory
        return total_memory, available_memory, usable_memory

    @staticmethod
    def _calculate_ps_qs(cpu_count):
        """
        Calculate Ps and Qs for near-square process grids.
        """
        ps = int(math.sqrt(cpu_count))  # Start with the square root
        while cpu_count % ps != 0 and ps > 1:  # Find the nearest divisor
            ps -= 1
        qs = cpu_count // ps
        return ps, qs

    @staticmethod
    def _calculate_problem_size(ram_mb):
        """
        Calculate the problem size (N) based on available RAM.
        """
        ram_bytes = ram_mb * 1024 * 1024  # Convert MB to bytes
        return int(math.sqrt(ram_bytes / 8))  # Solve for N

    def _generate_hpl_file(self, cpu_count, ram_allocation, output_dir, instance_id=None):
        """
        Generate the HPL configuration file.
        """
        ps, qs = self._calculate_ps_qs(cpu_count)
        n_value = self._calculate_problem_size(ram_allocation)
        nb = 192  # Fixed block size as per template

        instance_suffix = f"_instance{instance_id}" if instance_id is not None else ""
        file_path = os.path.join(output_dir, f"hpl_{cpu_count}cpu{instance_suffix}.dat")

        hpl_template = f"""HPLinpack benchmark input file
Innovative Computing Laboratory, University of Tennessee
HPL.out      output file name (if any) 
6            device out (6=stdout,7=stderr,file)
1            # of problems sizes (N)
{n_value}    Ns
1            # of NBs
{nb}         NBs
0            PMAP process mapping (0=Row-,1=Column-major)
1            # of process grids (P x Q)
{ps}         Ps
{qs}         Qs
16.0         threshold
1            # of panel fact
2            PFACTs (0=left, 1=Crout, 2=Right)
1            # of recursive stopping criterium
4            NBMINs (>= 1)
1            # of panels in recursion
2            NDIVs
1            # of recursive panel fact.
1            RFACTs (0=left, 1=Crout, 2=Right)
1            # of broadcast
1            BCASTs (0=1rg,1=1rM,2=2rg,3=2rM,4=Lng,5=LnM)
1            # of lookahead depth
1            DEPTHs (>=0)
2            SWAP (0=bin-exch,1=long,2=mix)
64           swapping threshold
0            L1 in (0=transposed,1=no-transposed) form
0            U  in (0=transposed,1=no-transposed) form
1            Equilibration (0=no,1=yes)
8            memory alignment in double (> 0)
##### This line (no. 32) is ignored (it serves as a separator). ######
0                               Number of additional problem sizes for PTRANS
1200 10000 30000                values of N
0                               number of additional blocking sizes for PTRANS
40 9 8 13 13 20 16 32 64        values of NB
"""
        os.makedirs(output_dir, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(hpl_template)
        self.logger.info(f"HPL file generated: {file_path}")

    def create_cooperative_configs(self):
        """
        Create HPL configurations for cooperative benchmarking.
        """
        self.logger.info("Generating cooperative benchmark configurations...")
        cpu_counts = []
        cpu = self.total_cpus
        while cpu >= 1:
            cpu_counts.append(cpu)
            cpu //= 2  # Halve the CPU count for each step

        for cpu_count in cpu_counts:
            ram_allocation = self.usable_memory // self.total_cpus * cpu_count
            self._generate_hpl_file(cpu_count, ram_allocation, os.path.join(self.output_dir, "cooperative"))

    def create_competitive_configs(self):
        """
        Create HPL configurations for competitive benchmarking.
        """
        self.logger.info("Generating competitive benchmark configurations...")
        cpu = self.total_cpus
        instances = []

        while cpu >= 1:
            instances.append(cpu)
            cpu //= 2  # Halve the CPUs for the next level

        for i, cores_per_instance in enumerate(instances):
            num_instances = self.total_cpus // cores_per_instance
            instance_dir = os.path.join(self.output_dir, "competitive", f"{num_instances}_instances")
            ram_per_instance = self.usable_memory // num_instances

            for instance_id in range(num_instances):
                self._generate_hpl_file(cores_per_instance, ram_per_instance, instance_dir, instance_id + 1)

    def generate_configs(self):
        """
        Generate both cooperative and competitive HPL configurations.
        """
        self.logger.info("Starting HPL configuration generation...")
        self.create_cooperative_configs()
        self.create_competitive_configs()
        self.logger.info("All configurations have been generated.")
        self.logger.info(f"Configurations saved in {self.output_dir}")


# Example usage
if __name__ == "__main__":
    logger = ShellLogger(script_path="./log/log.sh")
    hpl_config = HPLBenchmarkConfig(output_dir="hpl_configs", logger=logger)
    hpl_config.generate_configs()
