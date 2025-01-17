import requests
from pathlib import Path
from typing import Dict, Optional

class NodeAPI:
    """
    A helper class for communicating with a single node's HTTP API.
    """

    def __init__(self, ip: str, port: int):
        self.base_url = f"http://{ip}:{port}"

    def submit_benchmark(self, params: Dict[str, int]) -> Optional[str]:
        """
        Submit a standard benchmark request to the node. Returns a task_id if successful.
        """
        try:
            response = requests.post(
                f"{self.base_url}/submit_custom_task",
                json=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("task_id")
        except Exception as e:
            print(f"Error submitting benchmark to {self.base_url}: {e}")
            return None

    def check_status(self, task_id: str) -> Optional[str]:
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

    def get_results(self, task_id: str, save_dir: Path) -> bool:
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
                file_path.write_text(content)

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

            # If the server returns a 4xx or 5xx status code, this will raise an HTTPError
            response.raise_for_status()

            # Parse JSON response
            data = response.json()

            # Return task_id if available
            return data.get("task_id")

        except requests.HTTPError as http_err:
            # In case of a 409 (Resource busy) or other HTTP error
            try:
                # Attempt to parse server's JSON error message
                error_data = response.json()
                error_msg = error_data.get("error", "Unknown error.")
                print(f"HTTP error from {self.base_url}: {error_msg} (Status code {response.status_code})")
            except Exception:
                # Fallback if JSON parsing fails
                print(f"HTTP error from {self.base_url}: {http_err}")
            return None
        except Exception as e:
            print(f"Error submitting cooperative benchmark to {self.base_url}: {e}")
            return None
