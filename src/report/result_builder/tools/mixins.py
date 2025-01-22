

class HPLAggregationsMixin:
    def _aggregate_hpl(self, metric: str, agg_func, source: str = 'default'):
        """
        Generic aggregation method for HPL metrics.
        
        - metric: Name of the HPLResult attribute to aggregate.
        - agg_func: Function to aggregate list of metric values (e.g., sum, max, min, average).
        - source: 'default' to use self.hpl_results, 'benchmark' to use self.all_hpl_results().
        """
        # Select list of HPL results based on source type.
        if source == 'benchmark':
            hpl_list = self.all_hpl_results()
        else:
            hpl_list = self.hpl_results

        # Extract non-null metric values.
        values = [getattr(hpl, metric) for hpl in hpl_list if getattr(hpl, metric) is not None]
        return agg_func(values) if values else None

    @staticmethod
    def _average(values):
        return sum(values) / len(values) if values else None
