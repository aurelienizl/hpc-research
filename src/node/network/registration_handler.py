import requests
import psutil
import platform
import time
from typing import Dict, Any
from log.LogInterface import LogInterface
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RegistrationHandler:
    def __init__(self, master_port: int, master_ip: str, additional_info: Dict[str, Any] = {}):
        self.log = LogInterface("RegistrationHandler")
        self.master_port = master_port
        self.master_ip = master_ip
        self.additional_info = additional_info
        self.register_endpoint = f"http://{self.master_ip}:{self.master_port}/register"

    def collect_system_metrics(self) -> Dict[str, Any]:
        try:
            metrics = {
                "cpu_count": psutil.cpu_count(logical=True),
                "total_ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
                "available_ram_gb": round(psutil.virtual_memory().available / (1024 ** 3), 2),
                "hostname": platform.node(),
                "operating_system": platform.system(),
                "python_version": platform.python_version(),
                "disk_total_gb": round(psutil.disk_usage('/').total / (1024 ** 3), 2),
                "disk_available_gb": round(psutil.disk_usage('/').free / (1024 ** 3), 2),
                
            }
            metrics.update(self.additional_info)
            self.log.info(f"Collected system metrics: {metrics}")
            return metrics
        except Exception as e:
            self.log.error(f"Error collecting system metrics: {e}")
            return {}

    def register_node(self, max_retries: int = 10) -> bool:
        attempt = 0
        while attempt < max_retries:
            success = self._attempt_registration()
            if success:
                return True
            attempt += 1
            self.log.warning(f"Registration attempt {attempt} failed. Retrying in 2 seconds...")
            time.sleep(2)
        self.log.error("All registration attempts failed.")
        return False

    def _attempt_registration(self) -> bool:
        metrics = self.collect_system_metrics()
        if not metrics:
            self.log.error("No metrics collected. Cannot register node.")
            return False

        try:
            self.log.info(f"Attempting to register node with master at {self.register_endpoint}...")
            response = requests.post(
                self.register_endpoint,
                json={"metrics": metrics},
                timeout=10,
                verify=False
            )

            if response.status_code == 200:
                self.log.info("Node successfully registered with the master node.")
                return True

            self.log.error(
                f"Failed to register node. Status Code: {response.status_code}, Response: {response.text}"
            )
            return False

        except requests.exceptions.RequestException as e:
            self.log.error(f"Exception during node registration: {e}")
            return False
