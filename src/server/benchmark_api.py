#!/usr/bin/env python3
import requests
import time

class BenchmarkAPI:
    """
    A simple API client to communicate with benchmark client endpoints.
    
    Methods:
      - launch_benchmark(command, pre_cmd_exec=None, post_cmd_exec=None): 
            Launches a benchmark on the client.
      - get_status(task_id): Retrieves the status of the benchmark task.
      - get_results(task_id): Retrieves the results of the benchmark task.
    
    Usage:
      api = BenchmarkAPI(client_url="http://client1:5000", secret_key="mySecret123")
      launch_resp = api.launch_benchmark("sysbench cpu run", pre_cmd_exec="echo pre-cmd executed", post_cmd_exec="echo post-cmd executed")
      task_id = launch_resp.get("task_id")
      status = api.get_status(task_id)
      results = api.get_results(task_id)
    """
    def __init__(self, client_url: str, secret_key: str):
        # Remove trailing slash if present.
        self.client_url = client_url.rstrip('/')
        self.secret_key = secret_key

    def launch_benchmark(self, command: str, pre_cmd_exec: str = None, post_cmd_exec: str = None) -> dict:
        """
        Launches a benchmark on the client.
        
        Parameters:
          command (str): The command line to execute.
          pre_cmd_exec (str, optional): Command to execute before the main benchmark.
          post_cmd_exec (str, optional): Command to execute after the main benchmark.
        
        Returns:
          dict: A dictionary containing the client response.
        """
        endpoint = f"{self.client_url}/api/benchmark/launch"
        payload = {"command": command, "secret_key": self.secret_key}
        if pre_cmd_exec:
            payload["pre_cmd_exec"] = pre_cmd_exec
        if post_cmd_exec:
            payload["post_cmd_exec"] = post_cmd_exec
        try:
            response = requests.post(endpoint, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_status(self, task_id: str) -> dict:
        """
        Retrieves the current status of the benchmark task.
        
        Parameters:
          task_id (str): The unique task identifier.
        
        Returns:
          dict: A dictionary containing the task status.
        """
        endpoint = f"{self.client_url}/api/benchmark/status/{task_id}"
        try:
            response = requests.get(endpoint, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_results(self, task_id: str) -> dict:
        """
        Retrieves the benchmark results once the task is finished.
        
        Parameters:
          task_id (str): The unique task identifier.
        
        Returns:
          dict: A dictionary containing the task results.
        """
        endpoint = f"{self.client_url}/api/benchmark/results/{task_id}"
        try:
            response = requests.get(endpoint, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

## Example usage (for testing purposes):
if __name__ == "__main__":
    # Replace with your actual client URL and secret key.
    client_url = "http://localhost:5000"
    secret_key = "mySecret123"
    
    api = BenchmarkAPI(client_url, secret_key)
    
    # Launch benchmark using a simple command with pre and post commands.
    launch_response = api.launch_benchmark(
        "sysbench cpu run",
        pre_cmd_exec="echo pre-cmd executed",
        post_cmd_exec="echo post-cmd executed"
    )
    print("Launch response:", launch_response)
    
    task_id = launch_response.get("task_id")
    if task_id:
        print("Task ID:", task_id)
        while True:
            # Check the status of the benchmark task.
            status_response = api.get_status(task_id)
            print("Status response:", status_response)
            
            if status_response.get("status") in ["finished", "error"]:
                break
            # Sleep for a while before checking again.
            time.sleep(5)
            
        # Get benchmark results.
        results_response = api.get_results(task_id)
        print("Results response:", results_response)
    else:
        print("Error launching benchmark:", launch_response.get("message"))
