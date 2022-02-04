import requests, warnings
import json, time
from dataclasses import dataclass
from typing import Optional
from tinyman.v1.client import TinymanMainnetClient
from tinyman.utils import get_state_int

@dataclass
class PoolTransaction:
    amount: int
    asset_id: int
    block: int
    counterparty: str
    tx_type: str

@dataclass
class PoolState:
    time: int
    asset1_reserves: int
    asset2_reserves: int

def get_pool_state(pool_address: str):
    query = f'https://algoindexer.algoexplorerapi.io/v2/accounts/{pool_address}'
    resp = requests.get(query).json()['account']['apps-local-state'][0]
    state = {y['key']: y['value'] for y in resp['key-value']}
    return PoolState(int(time.time()), get_state_int(state, 's1'), get_state_int(state,'s2'))

def get_pool_state_txn(tx: dict):
    if tx['tx-type'] != 'appl':
        warnings.warn('Attempting to extract pool state from non application call')
    state = {x['key'] : x['value'] for x in tx['local-state-delta'][0]['delta']}
    s1 = get_state_int(state, 's1')
    s2 = get_state_int(state, 's2')
    if s1 <= 0 or s2 <= 0:
        return None
    return PoolState(tx['round-time'], s1, s2)

def query_transactions(params: dict, num_queries: int):
    query = f'https://algoindexer.algoexplorerapi.io/v2/transactions'
    resp = requests.get(query, params=params).json()

    i = 0
    while resp and i < num_queries:
        for tx in resp['transactions']:
            yield tx
        resp = requests.get(query, params={**params, **{'next': resp['next-token']}}).json()
        i += 1

def build_pool_data(pool_address: str, num_queries: int):
    prev_time = None
    for tx in query_transactions(params={'address': pool_address}, num_queries=num_queries):
        if tx['tx-type']!='appl':
            continue
        ps = get_pool_state_txn(tx)
        if not ps or (prev_time and prev_time==ps.time):
            continue
        prev_time = ps.time
        yield ps

def query_transactions_for_pool(pool_address: str, num_queries: int):
    for tx in query_transactions(params={'address': pool_address}, num_queries=num_queries):

        try:
            if tx['tx-type'] == 'axfer':
                # ASA
                key = 'asset-transfer-transaction'
                asset_id = tx[key]['asset-id']

            elif tx['tx-type'] == 'pay':
                # Algo
                key = 'payment-transaction'
                asset_id = 0
            else:
                continue

            receiver, sender = tx[key]['receiver'], tx['sender']

            if pool_address == receiver:
                counterparty = sender
                sign = +1
            elif pool_address == sender:
                counterparty = receiver
                sign = -1
            elif pool_address == tx[key]['close-to']:
                # I haven't understood this case but hopefully it's not too important
                continue
            else:
                raise ValueError(f'pool_address {pool_address} neither in sender nor receiver')

            amount = sign * tx[key]['amount']
            block = tx['confirmed-round']
            yield PoolTransaction(amount, asset_id, block, counterparty, tx['tx-type'])

        except Exception as e:
            raise Exception(json.dumps(tx, indent=4)) from e


# Logged swap for a pool, excluding redeeming amounts
@dataclass
class Swap:
    # Asset id going to the pool
    asset_in: int
    # Amount going the pool
    amount_in: int
    # Asset id going to the counterparty
    asset_out: int
    # Amount going to the counterparty
    amount_out: int
    counterparty: str
    block: int


# TODO Check this is valid, does it also hold for pools without Algo?
def is_fee_payment(tx: PoolTransaction):
    return tx.asset_id == 0 and tx.amount == 2000 and tx.tx_type == 'pay'


class SwapScraper:
    def __init__(self, asset1_id, asset2_id):

        client = TinymanMainnetClient()
        pool = client.fetch_pool(asset1_id, asset2_id)
        assert pool.exists

        self.liquidity_asset = pool.liquidity_asset.id
        self.assets = [asset1_id, asset2_id]
        self.address = pool.address

    def scrape(self, num_queries:int):

        def is_transaction_in(tx: PoolTransaction, transaction_out: PoolTransaction):
            return tx.counterparty == transaction_out.counterparty \
                   and tx.asset_id != transaction_out.asset_id \
                   and tx.asset_id in self.assets \
                   and not is_fee_payment(tx)

        transaction_out: Optional[PoolTransaction] = None
        transaction_in: Optional[PoolTransaction] = None

        for tx in query_transactions_for_pool(self.address, num_queries):

            if transaction_out:
                # We recorded a transaction out and in, looking for a fee payment
                if transaction_in:
                    if is_fee_payment(tx) and tx.counterparty == transaction_in.counterparty:
                        yield Swap(asset_in=transaction_in.asset_id,
                                   asset_out=transaction_out.asset_id,
                                   amount_in=transaction_in.amount,
                                   amount_out=-transaction_out.amount,
                                   counterparty=tx.counterparty,
                                   block=tx.block
                                   )
                    transaction_out = None
                    transaction_in = None

                # We recorded a transaction out, looking for a transaction in
                else:
                    # TODO We should account for redeeming excess funds from the pool?
                    if is_transaction_in(tx, transaction_out):
                        transaction_in = tx
                    else:
                        transaction_out = None
            else:
                if tx.amount < 0 and tx.asset_id in self.assets:
                    transaction_out = tx


sc = SwapScraper(0, 470842789)
for tx in sc.scrape(10):
    print(tx)
