import pandas as pd
import requests
from typing import Optional
import datetime


def query_transactions(params: dict, num_queries: Optional[int], before_time: Optional[datetime.datetime]):
    query = f'https://algoindexer.algoexplorerapi.io/v2/transactions'

    if before_time is not None:
        params = {**params, **{'before-time': before_time.strftime('%Y-%m-%d')}}

    resp = requests.get(query, params=params).json()

    i = 0
    while resp and (num_queries is None or i < num_queries):
        if 'transactions' not in resp:
            print(f"'transactions' key not in resp:{resp}")
        else:
            for tx in resp['transactions']:
                yield tx

        if 'next-token' in resp:
            resp = requests.get(query, params={**params, **{'next': resp['next-token']}}).json()
        else:
            resp = None
        i += 1


def datetime_to_int(t: datetime.datetime):
    return int(t.timestamp())


def generator_to_df(gen, time_columns=('time',)):
    df = pd.DataFrame(gen)
    if df.empty:
        print("DataFrame is empty")
    else:
        for col in time_columns:
            df[col] = pd.to_datetime(df[col], unit='s', utc=True)
    return df
