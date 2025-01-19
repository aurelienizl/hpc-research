import requests
from pathlib import Path
from typing import Dict, Optional


class NodeAPI:
    """
    A helper class for communicating with a single node's HTTP API.
    """

    def __init__(self, ip: str, port: int):
        self.base_url = f"http://{ip}:{port}"

    def get_task_status(self, task_id: str) -> Optional[str]:
        """
        Check the status of a benchmark task.
        Returns the status string ("running", "completed", etc.) if successful.
        """
        try:
            response = requests.get(
                f"{self.base_url}/task_status/{task_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("status")
        except Exception as e:
            print(f"Error checking status for task {task_id}: {e}")
            return None

    def get_benchmark_results(self, task_id: str, save_dir: Path) -> bool:
        """
        Fetch benchmark results for a completed task and save them to disk.
        Returns True if the results were successfully retrieved and saved.
        """
        try:
            response = requests.get(
                f"{self.base_url}/get_results/{task_id}",
                timeout=30
            )
            response.raise_for_status()
            results = response.json().get("results", [])

            for result in results:
                filename = result["filename"]
                content = result["content"]
                file_path = save_dir / filename
                # Explicitly specify encoding
                file_path.write_text(content, encoding='utf-8')

            return True
        except Exception as e:
            print(f"Error retrieving results for task {task_id}: {e}")
            return False

    def submit_cooperative_benchmark(
        self,
        ps: int,
        qs: int,
        n_value: int,
        nb: int,
        node_slots: Dict[str, int]
    ) -> Optional[str]:
        """
        Submit a cooperative benchmark request to the node. Returns a task_id if successful.
        Expected payload:
            ps: int
            qs: int
            n_value: int
            nb: int
            node_slots: Dict[str, int]
        """
        try:
            payload = {
                "ps": ps,
                "qs": qs,
                "n_value": n_value,
                "nb": nb,
                "node_slots": node_slots
            }
            response = requests.post(
                f"{self.base_url}/submit_cooperative_benchmark",
                json=payload,
                timeout=10
            )

            response.raise_for_status()

            return response.json().get("task_id")

        except Exception as e:
            print(f"Error submitting cooperative benchmark to {
                  self.base_url}: {e}")
            return None

    def submit_competitive_benchmark(self, 
                                     ps: int,
                                     qs: int,
                                     n_value: int, 
                                     nb: int, 
                                     instances_num: int
                                     ) -> Optional[str]:
        """
        Submit a standard benchmark request to the node. Returns a task_id if successful.
        """
        try:
            response = requests.post(
                f"{self.base_url}/submit_competitive_benchmark",
                json={
                    "ps": ps,
                    "qs": qs,
                    "n_value": n_value,
                    "nb": nb,
                    "instances_num": instances_num
                },
                timeout=10
            )
            response.raise_for_status()

            return response.json().get("task_id")
        except Exception as e:
            print(f"Error submitting benchmark to {self.base_url}: {e}")
            return None

    def ping(self) -> bool:
        """
        Check if the node is reachable.
        The response is jsonify({"message": "pong"}) if successful.
        """
        try:
            response = requests.get(f"{self.base_url}/ping", timeout=5)
            return response.status_code == 200 and response.json().get("message") == "pong"
        except Exception as e:
            print(f"Error pinging {self.base_url}: {e}")
            return False