import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

class NodeAPI:
    def __init__(self, ip: str, port: int):
        self.base_url = f"http://{ip}:{port}"

    def submit_benchmark(self, params: Dict[str, int]) -> Optional[str]:
        try:
            response = requests.post(
                f"{self.base_url}/submit_custom_task", json=params, timeout=10
            )
            response.raise_for_status()
            return response.json().get("task_id")
        except Exception as e:
            print(f"Error submitting benchmark to {self.base_url}: {e}")
            return None

    def check_status(self, task_id: str) -> Optional[str]:
        try:
            response = requests.get(
                f"{self.base_url}/task_status/{task_id}", timeout=10
            )
            response.raise_for_status()
            return response.json().get("status")
        except Exception as e:
            print(f"Error checking status for task {task_id}: {e}")
            return None

    def get_results(self, task_id: str, save_dir: Path) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/get_results/{task_id}", timeout=30
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            for result in results:
                file_path = save_dir / result["filename"]
                file_path.write_text(result["content"])
            return True
        except Exception as e:
            print(f"Error retrieving results for task {task_id}: {e}")
            return False
