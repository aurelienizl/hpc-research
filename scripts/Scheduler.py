import os
import sys
from multiprocessing import Process

import hpl.HPLInterface
import collectl.CollectlInterface
import log.LogInterface

CONFIGURATIONS_DIR = "HPLConfigurations"

class Scheduler:
    hplInterface = hpl.HPLInterface.HPLInterface(config_output_dir=CONFIGURATIONS_DIR)
    collectlInterface = collectl.CollectlInterface.CollectlInterface()
    logInterface = log.LogInterface.LogInterface(verbose=True)

    def __init__(self):
        print("Scheduler initialized.")

    def install_dependencies(self):
        try:
            self.hplInterface.install_hpl()
            self.collectlInterface.install_collectl()
            self.logInterface.info("Dependencies installed successfully.")
        except Exception as e:
            self.logInterface.error(f"Failed to install dependencies: {e}")
            sys.exit(1)

    def setup_environment(self):
        try:
            self.hplInterface.generate_hpl_configs(cooperative=True, competitive=True)
            self.logInterface.info("Environment setup completed.")
        except Exception as e:
            self.logInterface.error(f"Failed to set up environment: {e}")
            sys.exit(1)

    def run_cooperative_instance(self, cpu_count):
        try:
            print(f"Running cooperative benchmark with {cpu_count} CPUs...")

            if not os.path.exists(CONFIGURATIONS_DIR + f"/cooperative/hpl_{cpu_count}cpu.dat"):
                raise FileNotFoundError("HPL configuration file not found.")

            hpl_instance = self.hplInterface.setup_hpl_instance(
                config_path=CONFIGURATIONS_DIR + f"/cooperative/hpl_{cpu_count}cpu.dat",
                process_count=cpu_count,
                instance_id=1
            )
            self.collectlInterface.start_collectl(id=f"collectl_cooperative_{cpu_count}", output_file=f"collectl_cooperative_{cpu_count}.txt")
            hpl_instance.run()
            self.collectlInterface.stop_collectl(id=f"collectl_cooperative_{cpu_count}")
            print(f"Cooperative benchmark with {cpu_count} CPUs completed successfully.")
        except Exception as e:
            print(f"Error running cooperative benchmark with {cpu_count} CPUs: {e}")


    def run_competitive_instance(self, instance_number):
        """
        Run multiple competitive benchmark instances in parallel.

        Arguments:
            instance_number (int): The instance number for the competitive setup.
        """
        try:
            # Ensure the configuration directory for the competitive instances exists
            competitive_config_dir = os.path.join(CONFIGURATIONS_DIR, f"competitive/{instance_number}_instances")
            if not os.path.exists(competitive_config_dir):
                raise FileNotFoundError(f"Competitive configuration directory not found: {competitive_config_dir}")

            # List all the configuration files for this instance
            instances = os.listdir(competitive_config_dir)
            if not instances:
                raise FileNotFoundError(f"No HPL configuration files found in {competitive_config_dir}")

            # Initialize list to keep track of processes
            processes = []

            # Start one process per HPL instance
            for instance in instances:
                config_path = os.path.join(competitive_config_dir, instance)

                # Ensure the configuration file exists
                if not os.path.exists(config_path):
                    raise FileNotFoundError(f"Configuration file {config_path} not found.")

                # Setup the HPL instance
                hpl_instance = self.hplInterface.setup_hpl_instance(
                    config_path=config_path,
                    # process_count is instance number divided by total cpu count
                    process_count=3,
                    instance_id=instance
                )

                # Start collectl for monitoring this instance
                collectl_process_id = f"collectl_competitive_{instance}"
                self.collectlInterface.start_collectl(
                    id=collectl_process_id,
                    output_file=f"collectl_{instance}.txt"
                )

                # Create a new process to run the HPL instance
                p = Process(target=hpl_instance.run)
                processes.append(p)
                p.start()

            # Wait for all processes to finish
            for p in processes:
                p.join()

            print(f"Competitive benchmark with instance {instance_number} completed successfully.")

        except Exception as e:
            print(f"Error running competitive benchmark with instance {instance_number}: {e}")




if __name__ == "__main__":
    scheduler = Scheduler()
    scheduler.install_dependencies()
    scheduler.setup_environment()
