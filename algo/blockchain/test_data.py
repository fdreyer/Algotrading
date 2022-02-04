import unittest
import logging
from algo.blockchain.process_volumes import SwapScraper
from algo.blockchain.process_prices import PriceScraper
from algo.blockchain.utils import datetime_to_int
from tinyman.v1.client import TinymanMainnetClient
import datetime


class TestData(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        logging.basicConfig(level=logging.NOTSET)
        self.logger = logging.getLogger("TestData")
        self.client = TinymanMainnetClient()

        self.date_min = datetime.datetime(year=2022, month=1, day=20)

        super().__init__(*args, **kwargs)

    def test_volumes(self, n_queries=10):
        asset1 = 0
        asset2 = 470842789

        sc = SwapScraper(self.client, asset1, asset2)
        for tx in sc.scrape(datetime_to_int(self.date_min), num_queries=n_queries):
            print(tx)

    def test_prices(self, n_queries=10):
        asset1 = 0
        asset2 = 470842789

        pool = self.client.fetch_pool(asset1, asset2)
        assert pool.exists

        ps = PriceScraper(self.client, asset1, asset2)

        for tx in ps.scrape(datetime_to_int(self.date_min), num_queries=n_queries):
            print(tx)
