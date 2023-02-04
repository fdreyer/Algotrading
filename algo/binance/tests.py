import datetime
import logging
import unittest

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import RobustScaler

from algo.binance.fit import fit_eval_model, UniverseDataOptions
from algo.binance.coins import Universe, load_universe_candles, all_symbols, top_mcap, symbol_to_ids
from algo.binance.fit import UniverseDataStore, ModelOptions, ResidOptions, EmaOptions


class TestUniverseDataStore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        coins = ['btc',
                 'ada',
                 'xrp',
                 'dot',
                 'doge',
                 'matic',
                 'algo',
                 'ltc',
                 'atom',
                 'link',
                 'near',
                 'bch',
                 'xlm',
                 'axs',
                 'vet',
                 'hbar',
                 'fil',
                 'egld',
                 'theta',
                 'icp',
                 'etc',
                 'xmr',
                 'xtz',
                 'aave',
                 'gala',
                 'grt',
                 'klay',
                 'cake',
                 'ar',
                 'eos',
                 'lrc',
                 'ksm',
                 'enj',
                 'qnt',
                 'amp',
                 'cvx',
                 'crv',
                 'mkr',
                 'xec',
                 'kda',
                 'tfuel',
                 'spell',
                 'sushi',
                 'bat',
                 'neo',
                 'celo',
                 'zec',
                 'osmo',
                 'chz',
                 'waves',
                 'dash',
                 'fxs',
                 'nexo',
                 'comp',
                 'mina',
                 'yfi',
                 'iotx',
                 'xem',
                 'snx',
                 'zil',
                 'rvn',
                 '1inch',
                 'gno',
                 'lpt',
                 'dcr',
                 'qtum',
                 'ens',
                 'icx',
                 'waxp',
                 'omg',
                 'ankr',
                 'scrt',
                 'sc',
                 'bnt',
                 'woo',
                 'zen',
                 'iost',
                 'btg',
                 'rndr',
                 'zrx',
                 'slp',
                 'anc',
                 'ckb',
                 'ilv',
                 'sys',
                 'uma',
                 'kava',
                 'ont',
                 'hive',
                 'perp',
                 'wrx',
                 'skl',
                 'flux',
                 'ren',
                 'mbox',
                 'ant',
                 'ray',
                 'dgb',
                 'movr',
                 'nu']

        coins = coins[:3]
        universe = Universe(coins)

        start_date = datetime.datetime(year=2022, month=1, day=1)
        end_date = datetime.datetime(year=2023, month=1, day=1)

        time_col = 'Close time'

        df = load_universe_candles(universe, start_date, end_date, '5m')

        df.set_index(['pair', time_col], inplace=True)
        self.price_ts = ((df['Close'] + df['Open']) / 2.0).rename('price')
        self.logret_ts = (np.log(df['Close']) - np.log(df['Open'])).rename('logret')
        self.volume_ts = df['Volume']

        super().__init__(*args, **kwargs)

    def _aa(self, quantile_cap: float):
        ema_options = EmaOptions([4, 12, 24, 48, 96], include_volumes=True)
        ro = ResidOptions(market_pairs={'BTCUSDT'})

        uds = UniverseDataStore(self.price_ts, self.logret_ts, self.volume_ts, ema_options, ro)

        alpha = 1.0

        def get_lm():
            return Ridge(alpha=alpha)

        def transform_fit_target(y):
            return y

        def transform_model_after_fit(lm):
            return lm

        fit_options = UniverseDataOptions(demean=True,
                                          forward_hour=24,
                                          target_scaler=lambda: RobustScaler())
        data = uds.prepare_data(fit_options)

        global_opt = ModelOptions(
            get_lm=lambda: Ridge(alpha=0),
            transform_fit_target=transform_fit_target,
            transform_model_after_fit=transform_model_after_fit,
            cap_oos_quantile=None
            # cap_oos_quantile=0.05
        )
        data_global = uds.prepare_data_global(data)
        global_fit = fit_eval_model(data_global, global_opt)

        opt = ModelOptions(
            get_lm=get_lm,
            transform_fit_target=transform_fit_target,
            transform_model_after_fit=transform_model_after_fit,
            cap_oos_quantile=quantile_cap
        )
        ress = uds.fit_products(data, opt, global_fit)

        print(list(ress.values())[0].test.ypred.min(), list(ress.values())[0].test.ypred.max())
        # print(r2_score(list(ress.values())[0].test.ytrue, list(ress.values())[0].test.ypred))

    def test_a(self):
        self._aa(0.00001)

    def test_b(self):
        self._aa(0.4)


class TestSymbols(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
        super().__init__(*args, **kwargs)

    def test_a(self):
        symbols_map = symbol_to_ids()

        for symbol in all_symbols():
            if symbol == 'eth':
                coin_id = symbols_map.get(symbol, None)
                print(f'{symbol=}, {coin_id=}')

    def test_b(self):
        top_mcap(datetime.date(year=2022, month=1, day=1), dry_run=True)


if __name__ == '__main__':
    unittest.main()