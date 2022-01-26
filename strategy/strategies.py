from strategy.base import StrategyBase
from strategy.analysis import AnalyticProvider


class SimpleStrategyEMA(StrategyBase):
    """Simple strategy based on monitoring of EMA"""

    def __init__(self, analytic_provider: AnalyticProvider):
        self.analytic_provider = analytic_provider
        # use a dictionary with {assetid: weight} format for more sophisticated strategies?
        self.buy = set()
        self.sell = set()

    def score(self, assetid: int):
        """Return list of tuples with coins to long"""

        diff = self.analytic_provider.expavg_long[assetid] - self.analytic_provider.expavg_short[assetid]
        # if difference becomes negative and was previously positive, buy coin, and vice vera
        if diff[-1] < 0:
            self.sell.discard(assetid)
            self.buy.add(assetid)
        if diff[-1] > 0:
            self.buy.discard(assetid)
            self.sell.add(assetid)
