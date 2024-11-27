from collectl.collectl_interface import CollectlManager
from hpl.hpl_config import HPLBenchmarkConfig
from log.log_interface import ShellLogger

if __name__ == "__main__":
    logger = ShellLogger(script_path="./log/log.sh", verbose=True)
    manager = CollectlManager(logger=logger)
    hpl_config = HPLBenchmarkConfig(output_dir="hpl_configs", logger=logger)


    # Install Collectl
    manager.install_collectl()

    # Start Collectl
    manager.start_collectl("test_id", "output")

    # Check if Collectl is running # Expected output: True
    assert manager.is_collectl_running("test_id") 

    # Stop Collectl
    manager.stop_collectl("test_id") 

    # Check if Collectl is running, expecing False
    assert manager.is_collectl_running("test_id") == False

    hpl_config.generate_configs()

