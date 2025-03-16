import time

from typing import Dict, Optional, Type, Any
from Log.LogInterface import LogInterface 
from Benchmarks.BaseBenchmarkHandler import BaseBenchmarkHandler
from Benchmarks.HPL.HPLHandler import HPLHandler
from Benchmarks.Collectl.CollectlHandler import CollectlHandler
from Benchmarks.NETPipe.NETPipeHandler import NETPipeHandler
from Database.DatabaseInterface import DatabaseInterface

class BaseBenchmarkInterface:
    def __init__(self, logger: LogInterface):
        self.logger = logger
        self.active_benchmarks: Dict[str, tuple[BaseBenchmarkHandler, Any]] = {}
        self.database = DatabaseInterface(logger=self.logger)
        self.benchmark_handlers = {
            'hpl': HPLHandler,
            'collectl': CollectlHandler,
            'netpipe': NETPipeHandler
        }

    def start_benchmark(self, 
                       benchmark_type: str,
                       task_id: str,
                       command_line: str,
                       **config_params) -> bool:
        """
        Start a benchmark of the specified type with given parameters.
        
        Args:
            benchmark_type: Type of benchmark to run ('hpl', 'collectl', 'netpipe')
            task_id: Unique identifier for this benchmark run
            command_line: Command line parameters for the benchmark
            **config_params: Additional configuration parameters specific to the benchmark
        """
        try:
            if benchmark_type not in self.benchmark_handlers:
                self.logger.error(f"Unknown benchmark type: {benchmark_type}")
                return False

            handler_class = self.benchmark_handlers[benchmark_type]
            handler = handler_class(command_line, task_id, self.logger)

            # Prepare environment with any config params
            if benchmark_type == 'hpl':
                handler.prepare_environment(**config_params)
            else:
                handler.prepare_environment()

            handler.prepare_command_line()
            process = handler.run()

            if process:
                self.active_benchmarks[task_id] = (handler, process)
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error starting benchmark: {e}")
            return False

    def stop_benchmark(self, task_id: str) -> bool:
        """
        Stop a running benchmark.
        """
        if task_id not in self.active_benchmarks:
            return False

        handler, process = self.active_benchmarks[task_id]
        try:
            handler.kill(process)
            files = handler.retrieve_data()
            self.database.insert_files_for_id(task_id, files)
            handler.cleanup_environment()
            del self.active_benchmarks[task_id]
            self.logger.info(f"Stopped benchmark {task_id} from BaseInterface")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping benchmark {task_id}: {e}")
            return False

    def get_benchmark_status(self, task_id: str) -> Optional[str]:
        """
        Get the current status of a benchmark.
        Returns: 'running', 'completed', or None if not found
        """
        if task_id not in self.active_benchmarks:
            return None

        handler, process = self.active_benchmarks[task_id]
        if process.poll() is None:
            return 'running'
        return 'completed'

    def get_benchmark_results(self, task_id: str) -> Optional[list]:
        """
        Get results for a completed benchmark.
        """
        if task_id not in self.active_benchmarks:
            return None

        handler, process = self.active_benchmarks[task_id]
        if process.poll() is not None:  
            files = handler.retrieve_data()
            self.database.insert_files_for_id(task_id, files)
            handler.cleanup_environment()
            del self.active_benchmarks[task_id]
            results = self.database.get_files_by_id(task_id)
            if results:
                return results
        return None

    def cleanup_all(self):
        """
        Stop all running benchmarks and cleanup.
        """
        for task_id, (handler, _) in list(self.active_benchmarks.items()):
            if not self.stop_benchmark(task_id):
                self.logger.error(f"Failed to stop benchmark {task_id}")
            handler.cleanup_environment()
            
