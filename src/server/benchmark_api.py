# benchmark_api.py
import requests

class BenchmarkAPI:
    """
    A simple API client for the two-step init/launch benchmark API.
    """

    def __init__(self, client_url: str, secret_key: str):
        self.client_url = client_url.rstrip("/")
        self.secret_key = secret_key

    def init_benchmark(self, pre_cmd_exec: str) -> dict:
        """
        Initializes the benchmark environment by running pre_cmd_exec.

        Returns:
            dict: { status, task_id } or error
        """
        endpoint = f"{self.client_url}/api/benchmark/init"
        payload = {"secret_key": self.secret_key, "pre_cmd_exec": pre_cmd_exec}
        try:
            resp = requests.post(endpoint, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def launch_benchmark(self, task_id: str, command: str) -> dict:
        """
        Launches the main benchmark using an existing initialized task_id.

        Returns:
            dict: { status, task_id } or error
        """
        endpoint = f"{self.client_url}/api/benchmark/launch"
        payload = {"secret_key": self.secret_key, "task_id": task_id, "command": command}
        try:
            resp = requests.post(endpoint, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_status(self, task_id: str) -> dict:
        """Retrieves the current status of the task."""
        endpoint = f"{self.client_url}/api/benchmark/status/{task_id}"
        try:
            resp = requests.get(endpoint, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_results(self, task_id: str) -> dict:
        """Retrieves the results once the task is finished."""
        endpoint = f"{self.client_url}/api/benchmark/results/{task_id}"
        try:
            resp = requests.get(endpoint, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}