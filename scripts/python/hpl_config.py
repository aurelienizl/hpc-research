import os
import math

# Fetch system details
with open("/proc/cpuinfo") as f:
    total_cpus = sum(1 for line in f if line.startswith("processor"))

with open("/proc/meminfo") as f:
    meminfo = {line.split(':')[0]: int(line.split()[1]) for line in f}
total_memory = meminfo["MemTotal"] // 1024  # Convert to MB
usable_memory = int(total_memory * 0.85)  # Use 85% of available memory

print(f"Total CPUs available: {total_cpus}")
print(f"Total Memory: {total_memory} MB")
print(f"Usable Memory (85%): {usable_memory} MB\n")

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

# Create configuration files
def create_configurations():
    cpu_counts = []
    cpu = total_cpus
    while cpu >= 1:
        cpu_counts.append(cpu)
        cpu //= 2  # Halve the CPU count for each step

    os.makedirs("hpl_configs", exist_ok=True)

    for cpu_count in cpu_counts:
        # Calculate values for Ns, Ps, Qs, and NB
        ps, qs = calculate_ps_qs(cpu_count)
        ram_allocation = usable_memory // total_cpus * cpu_count
        n_value = calculate_problem_size(ram_allocation)
        nb = 192  # Fixed block size as per your template

        # Debug statements
        print(f"Generating configuration for {cpu_count} CPUs:")
        print(f"  Ps (process rows): {ps}")
        print(f"  Qs (process cols): {qs}")
        print(f"  Allocated RAM: {ram_allocation} MB")
        print(f"  Problem size (N): {n_value}")
        print(f"  Block size (NB): {nb}\n")

        # Use the provided template
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
        file_path = os.path.join("hpl_configs", f"hpl_{cpu_count}cpu.dat")
        with open(file_path, "w") as f:
            f.write(hpl_template)

# Execute
create_configurations()
print("All configurations have been generated and saved in the 'hpl_configs' directory.")
