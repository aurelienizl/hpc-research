import os
import subprocess
import asyncio
from typing import Optional, List, Tuple

from Benchmark.BenchmarkAPI import BenchmarksAPI
from Benchmark.BenchmarkParser import (
    BenchmarkInstance,
    ClusterInstances,
    ClusterInstance,
)
from WebClient.WebClientHandler import WebClient
from Log.LogInterface import LogInterface


class BenchmarkHandler:
    def __init__(
        self, clients: List[WebClient], config_path: str, logger: LogInterface
    ):
        self.benchmarks_api = BenchmarksAPI()
        self.cluster_instances = ClusterInstances(config_path)
        self.logger = logger
        self.clients = clients

    def load_benchmarks(self):
        self.cluster_instances.load_benchmarks()

    async def run_benchmarks(self):
        self.load_benchmarks()
        for cluster_benchmark in self.cluster_instances.cluster_benchmarks:
            for _ in range(cluster_benchmark.runs):
                await self.__run_cluster_benchmark(cluster_benchmark)

    async def __exec_cmd(self, cmd: str) -> bool:
        try:
            self.logger.info(f"Running command: {cmd}")
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                self.logger.error(f"Error running command: {cmd}")
                self.logger.error(stderr.decode())
                return False
            return True
        except Exception as e:
            self.logger.error(f"Exception while running command: {cmd} - {e}")
            return False

    async def __run_cluster_benchmark(self, cluster_benchmark: ClusterInstance):
        self.logger.info(f"Running cluster benchmark {cluster_benchmark.id}")
        if cluster_benchmark.pre_processing_cmd:
            self.logger.info(
                f"Running pre-processing command: {cluster_benchmark.pre_processing_cmd}"
            )
            if not await self.__exec_cmd(cluster_benchmark.pre_processing_cmd):
                return
        tasks_info: List[Tuple[str, WebClient]] = []
        for benchmark_instance in cluster_benchmark.benchmark_instances:
            task_infos = await self.__run_benchmark(benchmark_instance)
            self.logger.info(f"Running benchmark {benchmark_instance.id}")
            if task_infos:
                tasks_info.extend(task_infos)
        for task_info in tasks_info:
            self.logger.info(
                f"Waiting for benchmark {task_info[0]} on {task_info[1].hostname}"
            )
            await self.__wait_benchmark(task_info)
        results = []
        for task_info in tasks_info:
            self.logger.info(
                f"Getting results for benchmark {task_info[0]} on {task_info[1].hostname}"
            )
            result = await self.__get_benchmark_results(task_info)
            results.append((task_info, result))

        self.logger.info(f"Saving results for cluster benchmark {cluster_benchmark.id}")
        await self.__save_benchmark_results(cluster_benchmark, results)

        if cluster_benchmark.post_processing_cmd:
            self.logger.info(
                f"Running post-processing command: {cluster_benchmark.post_processing_cmd}"
            )
            if not await self.__exec_cmd(cluster_benchmark.post_processing_cmd):
                return

    async def __run_benchmark(
        self, benchmark_instance: BenchmarkInstance
    ) -> Optional[List[Tuple[str, WebClient]]]:
        tasks_info: List[Tuple[str, WebClient]] = []
        clients_by_hostname = {client.hostname: client for client in self.clients}
        targets_nodes: List[WebClient] = [
            clients_by_hostname[target]
            for target in benchmark_instance.targets_list
            if target in clients_by_hostname
        ]
        if not targets_nodes:
            print("No target nodes found for benchmark:", benchmark_instance)
            return None
        for target in targets_nodes:
            task_id = os.urandom(16).hex()
            result = await self.benchmarks_api.start_benchmark(
                target.websocket,
                task_id,
                benchmark_instance.type,
                benchmark_instance.command_line,
                benchmark_instance.custom_params,
            )
            if result:
                tasks_info.append((task_id, target))
            else:
                raise Exception(f"Failed to start benchmark on {target.hostname}")
        return tasks_info

    async def __wait_benchmark(self, task_info: Tuple[str, WebClient]) -> None:
        task_id, target = task_info
        websocket = target.websocket
        status = await self.benchmarks_api.get_benchmark_status(task_id, websocket)
        while status == "running":
            await asyncio.sleep(5)
            status = await self.benchmarks_api.get_benchmark_status(task_id, websocket)
        if status == "error":
            raise Exception(f"Benchmark {task_id} on {target.hostname} failed")

    async def __get_benchmark_results(self, task_info: Tuple[str, WebClient]) -> str:
        task_id, target = task_info
        websocket = target.websocket
        result = await self.benchmarks_api.get_benchmark_results(task_id, websocket)
        print("Benchmark", task_id, "on", target.hostname, "results:", result)
        return result

    async def __save_benchmark_results(
        self,
        cluster_benchmark: ClusterInstance,
        results: List[Tuple[Tuple[str, WebClient], List[str]]],
    ) -> None:
        cluster_results_dir = f"results/{cluster_benchmark.id}"
        os.makedirs(cluster_results_dir, exist_ok=True)
        for task_info, result in results:
            task_id, target = task_info
            target_results_dir = f"{cluster_results_dir}/{target.hostname}"
            os.makedirs(target_results_dir, exist_ok=True)
            result_file = f"{target_results_dir}/{task_id}.txt"
            with open(result_file, "w") as f:
                # Join the list of strings into one single string.
                result_str = "\n".join(result) if isinstance(result, list) else result
                f.write(result_str)
        self.logger.info(f"Saved results for cluster benchmark {cluster_benchmark.id}")

    def __repr__(self):
        return f"BenchmarkHandler(benchmarks_api={self.benchmarks_api}, cluster_instances={self.cluster_instances})"
