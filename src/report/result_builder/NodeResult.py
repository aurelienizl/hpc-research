# NodeResult.py
from pathlib import Path
from result_builder.HPLResult import HPLResult
from result_builder.CollectResult import CollectResult
from result_builder.tools.mixins import HPLAggregationsMixin  

class NodeResult(HPLAggregationsMixin):
    def __init__(self, node_folder: Path, collect_keywords: list):
        self.node_folder = node_folder
        self.ip_address = node_folder.name
        self.hpl_results = []
        self.collect_result = None

        self.load_results(collect_keywords)

    def load_results(self, collect_keywords: list):
        """Load HPL and collectl results from the node folder."""
        collect_file = self.node_folder / "collectl.log"
        if collect_file.exists():
            self.collect_result = CollectResult(collect_file, collect_keywords)

        for hpl_file in self.node_folder.glob("hpl_*"):
            self.hpl_results.append(HPLResult(hpl_file))

    @property
    def hpl_total_gflops(self):
        return self._aggregate_hpl('gflops', sum)

    @property
    def hpl_average_gflops(self):
        return self._aggregate_hpl('gflops', self._average)

    @property
    def hpl_average_time(self):
        return self._aggregate_hpl('time', self._average)

    @property
    def hpl_total_time(self):
        return self._aggregate_hpl('time', sum)
