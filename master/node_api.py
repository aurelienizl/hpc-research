from typing import Dict, Optional, Any
import requests
from pathlib import Path


class NodeAPI:
    def __init__(self, ip: str, port: int):
        self.base_url = f"http://{ip}:{port}"

    def submit_benchmark(
        self, ps: int, qs: int, n_value: int, nb: int, instances_num: int
    ) -> Optional[str]:
        try:
            data = {
                "ps": ps,
                "qs": qs,
                "n_value": n_value,
                "nb": nb,
                "instances_num": instances_num,
            }
            response = requests.post(f"{self.base_url}/submit_custom_task", json=data)
            response.raise_for_status()
            return response.json().get("task_id")
        except Exception as e:
            print(f"Error submitting benchmark: {e}")
            return None

    def check_status(self, task_id: str) -> Optional[str]:
        try:
            response = requests.get(f"{self.base_url}/task_status/{task_id}")
            response.raise_for_status()
            return response.json().get("status")
        except Exception as e:
            print(f"Error checking status: {e}")
            return None

    def get_results(self, task_id: str, save_dir: Path) -> bool:
        try:
            response = requests.get(f"{self.base_url}/get_results/{task_id}")
            response.raise_for_status()
            results = response.json()

            for result in results.get("results", []):
                with open(save_dir / result["filename"], "w") as f:
                    f.write(result["content"])
            return True
        except Exception as e:
            print(f"Error getting results: {e}")
            return False
