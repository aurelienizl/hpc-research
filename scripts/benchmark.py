import os
import subprocess
from multiprocessing import Process
from pathlib import Path
import shutil

# Constants
HPL_BIN_DIR = "/usr/local/hpl/bin"
HPL_INSTANCE_DIR = "/tmp/hpl_instance"
COOP_CONFIG_DIR = "hpl_configs/cooperative"
COMP_CONFIG_DIR = "hpl_configs/competitive"
RESULT_DIR = "results"


# Utility Functions
def run_command(command, cwd=None):
    """Run a shell command with optional working directory."""
    try:
        subprocess.run(command, shell=True, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}\n{e}")
        raise


def ensure_directory(path):
    """Ensure a directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)


# System Setup Functions
def disable_sleep():
    """Disable system sleep modes."""
    print("Disabling sleep, suspend, hibernate, and hybrid-sleep...")
    run_command("sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target")


def setup_hpl():
    """Setup HPL using the provided shell script."""
    print("Setting up HPL...")
    run_command("./hpl.sh")
    print("HPL setup completed.")


def install_collectl():
    """Install Collectl using the provided shell script."""
    print("Installing Collectl...")
    run_command("./collectl.sh install")
    print("Collectl installation completed.")


def start_collectl():
    """Start Collectl for monitoring."""
    print("Starting Collectl monitoring...")
    run_command("./collectl.sh start")
    print("Collectl started.")


def stop_collectl():
    """Stop Collectl monitoring."""
    print("Stopping Collectl monitoring...")
    run_command("./collectl.sh stop")
    print("Collectl stopped.")


def generate_configs():
    """Generate HPL configurations."""
    print("Generating HPL configurations...")
    run_command("python3 hpl_config.py")
    print("HPL configurations generated.")


# HPL Execution Functions
def get_cpu_count_from_filename(filename):
    """Extract the CPU count from a configuration filename."""
    base_name = os.path.basename(filename)
    try:
        if "cpu" in base_name and "instance" in base_name:
            return int(base_name.split('_')[1].split('cpu')[0])
        elif "cpu" in base_name:
            return int(base_name.split('_')[1].replace("cpu", "").replace(".dat", ""))
        else:
            raise ValueError("Filename format not recognized.")
    except (IndexError, ValueError):
        raise ValueError(f"Invalid configuration file name: {filename}")


def run_hpl_single(config_file, result_dir, instance_id=None):
    """Run a single HPL benchmark with isolated working directories."""
    print(f"Running HPL for config: {config_file}")

    # Define unique working directory for the instance
    instance_dir = f"{HPL_INSTANCE_DIR}_{instance_id}" if instance_id else HPL_INSTANCE_DIR

    try:
        # Ensure the working directory exists
        print(f"Creating working directory: {instance_dir}")
        ensure_directory(instance_dir)

        # Copy necessary files
        print("Copying xhpl binary and configuration file...")
        shutil.copy(os.path.join(HPL_BIN_DIR, "xhpl"), instance_dir)
        shutil.copy(config_file, os.path.join(instance_dir, "HPL.dat"))

        # Ensure result directory exists
        print(f"Ensuring parent directory exists: {RESULT_DIR}")
        ensure_directory(RESULT_DIR)
        print(f"Ensuring result directory exists: {result_dir}")
        ensure_directory(result_dir)

        # Define result file path with absolute path
        config_basename = os.path.basename(config_file)
        result_file = os.path.abspath(os.path.join(result_dir, config_basename.replace(".dat", ".result")))

        # Run HPL benchmark
        command = f"mpirun -np {get_cpu_count_from_filename(config_file)} --use-hwthread-cpus --allow-run-as-root ./xhpl > {result_file} 2>&1"
        print(f"Executing command: {command}")
        run_command(command, cwd=instance_dir)

        print(f"HPL result saved to: {result_file}")

    except Exception as e:
        print(f"Error during HPL execution for {config_file}: {e}")
        raise
    finally:
        # Clean up the temporary directory
        print(f"Cleaning up working directory: {instance_dir}")
        shutil.rmtree(instance_dir, ignore_errors=True)





def run_hpl_parallel(config_files, result_dir):
    """Run multiple HPL instances in parallel."""
    processes = []
    for instance_id, config_file in enumerate(config_files, start=1):
        process = Process(target=run_hpl_single, args=(config_file, result_dir, instance_id))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()


# Benchmark Execution
def run_cooperative_benchmarks():
    """Run HPL benchmarks for cooperative configurations."""
    print("Running cooperative benchmarks...")
    for config_file in Path(COOP_CONFIG_DIR).glob("*.dat"):
        run_hpl_single(str(config_file), os.path.join(RESULT_DIR, "cooperative"))
    print("Cooperative benchmarks completed.")


def run_competitive_benchmarks():
    """Run HPL benchmarks for competitive configurations."""
    print("Running competitive benchmarks...")
    for folder in Path(COMP_CONFIG_DIR).iterdir():
        if folder.is_dir():
            print(f"Running benchmarks for folder: {folder.name}")
            config_files = list(folder.glob("*.dat"))
            folder_result_dir = os.path.join(RESULT_DIR, "competitive", folder.name)
            run_hpl_parallel(config_files, folder_result_dir)
    print("Competitive benchmarks completed.")


# Main Workflow
def main():
    print("Starting automated HPL and Collectl benchmarking tool...")

    try:
        # Step 1: Disable sleep, suspend, and hibernate
        disable_sleep()

        # Step 2: Setup HPL and install Collectl
        setup_hpl()
        install_collectl()

        # Step 3: Generate HPL configurations
        generate_configs()

        # Step 4: Start Collectl monitoring
        start_collectl()

        # Step 5: Run benchmarks
        run_cooperative_benchmarks()
        run_competitive_benchmarks()
    finally:
        # Step 6: Stop Collectl after all benchmarks are done
        stop_collectl()

    print("All benchmarks completed. Results are saved in the 'results' directory.")


if __name__ == "__main__":
    main()
