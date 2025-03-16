from Log.LogInterface import LogInterface 
from WebClients.WebClient import WebClient
from Benchmarks.BenchmarksQueue import BenchmarkInstance

from typing import List, Tuple
import os

class ResultFile:
    def __init__(self, path: str, content: str):
        self.path = path
        self.content = content

    def __repr__(self):
        return f"ResultFile({self.path})"

class NodeResults:
    def __init__(self, node: WebClient):
        self.node = node
        self.results = []
        
    def add_result(self, result: ResultFile):
        self.results.append(result)

    def get_results(self):
        return [(result.path, result.content) for result in self.results]

    def __repr__(self):
        return f"NodeResults({self.node})"

class BenchmarkResults:
    def __init__(self, benchmarkInstance: BenchmarkInstance, results: List[Tuple[List[Tuple[str, str]], WebClient]], logger: LogInterface):
        self.benchmarkInstance = benchmarkInstance
        self.nodeResults = []
        self.results = results
        self.logger = logger
    
    def print_results(self):
        for node in self.nodeResults:
            for result in node.get_results():
                self.logger.log("info", f"{result[0]}: {result[1]}")

    def load_results(self):
        for files, client in self.results:
            # Use hostname as the unique key to group results from the same server
            unique_key = client.hostname
            # Look up any existing NodeResults based on hostname
            existing_node = next((node for node in self.nodeResults 
                                  if node.node.hostname == unique_key), None)
            if existing_node is None:
                # Save the hostname in instance_key (if needed later)
                client.instance_key = unique_key
                node = NodeResults(client)
                self.logger.log("info", f"Loading results from {unique_key}")
                self.nodeResults.append(node)
            else:
                node = existing_node
                self.logger.log("info", f"Merging results from {unique_key}")
                
            for path, file in files:
                # Optionally, check using the full path or a basename to decide on duplicates.
                if any(existing_path == path for existing_path, _ in node.get_results()):
                    self.logger.log("info", f"Skipping duplicate file {path} from {unique_key}")
                else:
                    self.logger.log("info", f"Loading {path}")
                    result = ResultFile(path, file)
                    node.add_result(result)

    def save_results(self):
        main_folder = f"results/{self.benchmarkInstance.id}"
        if not os.path.exists(main_folder):
            os.makedirs(main_folder)

        for node in self.nodeResults:
            node_folder = f"{main_folder}/{node.node.hostname}"
            if not os.path.exists(node_folder):
                os.makedirs(node_folder)
            for result in node.get_results():
                # Use os.path.basename to get only the filename
                file_name = os.path.basename(result[0])
                self.logger.log("info", f"Node {node.node.hostname} saving {file_name}")
                file_path = os.path.join(node_folder, file_name)
                # If the file already exists, append a number to the filename.
                if os.path.exists(file_path):
                    i = 1
                    base, ext = os.path.splitext(file_name)
                    new_file_path = file_path
                    while os.path.exists(new_file_path):
                        new_file_path = os.path.join(node_folder, f"{base}_{i}{ext}")
                        i += 1
                    file_path = new_file_path
                with open(file_path, "w") as f:
                    f.write(result[1])
        self.logger.log("info", f"Results saved to {main_folder}")

