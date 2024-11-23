import os
import math

# Fetch system details
with open("/proc/cpuinfo") as f:
    total_cpus = sum(1 for line in f if line.startswith("processor"))

with open("/proc/meminfo") as f:
    meminfo = {line.split(':')[0]: int(line.split()[1]) for line in f}
total_memory = meminfo["MemTotal"] // 1024  # Convert to MB
available_memory = meminfo["MemAvailable"] // 1024  # Convert to MB
usable_memory = int(available_memory * 0.85)  # Use 85% of available memory

print(f"Total CPUs available: {total_cpus}")
print(f"Total Memory: {total_memory} MB")
print(f"Available Memory: {available_memory} MB")
print(f"Usable Memory (85% of available): {usable_memory} MB\n")

# Helper function to calculate Ps and Qs for near-square grids
def calculate_ps_qs(cpu_count):
    ps = int(math.sqrt(cpu_count))  # Start with the square root
    while cpu_count % ps != 0 and ps > 1:  # Find the nearest divisor
        ps -= 1
    qs = cpu_count // ps
    return ps, qs

# Helper function to calculate N (problem size)
def calculate_problem_size(ram_mb):
    ram_bytes = ram_mb * 1024 * 1024  # Convert MB to bytes
    n = int(math.sqrt(ram_bytes / 8))  # Solve for N
    return n

# Generate HPL configuration file
def generate_hpl_file(cpu_count, ram_allocation, output_dir, instance_id=None):
    ps, qs = calculate_ps_qs(cpu_count)
    n_value = calculate_problem_size(ram_allocation)
    nb = 192  # Fixed block size as per your template

    instance_suffix = f"_instance{instance_id}" if instance_id is not None else ""
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
    file_path = os.path.join(output_dir, f"hpl_{cpu_count}cpu{instance_suffix}.dat")
    with open(file_path, "w") as f:
        f.write(hpl_template)

# Create configurations for cooperative benchmarks
def create_cooperative_configs():
    print("Generating cooperative benchmark configurations...\n")
    cpu_counts = []
    cpu = total_cpus
    while cpu >= 1:
        cpu_counts.append(cpu)
        cpu //= 2  # Halve the CPU count for each step

    for cpu_count in cpu_counts:
        ram_allocation = usable_memory // total_cpus * cpu_count
        generate_hpl_file(cpu_count, ram_allocation, "hpl_configs/cooperative")

# Create configurations for competitive benchmarks
def create_competitive_configs():
    print("Generating competitive benchmark configurations...\n")
    cpu = total_cpus
    instances = []

    # Dynamically create instance definitions
    while cpu >= 1:
        instances.append(cpu)
        cpu //= 2  # Halve the CPUs for the next level

    for i, cores_per_instance in enumerate(instances):
        num_instances = total_cpus // cores_per_instance
        instance_dir = f"hpl_configs/competitive/{num_instances}_instances"
        ram_per_instance = usable_memory // num_instances

        for instance_id in range(num_instances):
            generate_hpl_file(cores_per_instance, ram_per_instance, instance_dir, instance_id + 1)

# Main function
def main():
    create_cooperative_configs()
    create_competitive_configs()
    print("All configurations have been generated.")
    print("Cooperative configurations are in 'hpl_configs/cooperative/'")
    print("Competitive configurations are in 'hpl_configs/competitive/'")

# Execute
main()
