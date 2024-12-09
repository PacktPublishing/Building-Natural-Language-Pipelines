from bytewax.dataflow import Dataflow
from bytewax.inputs import FixedPartitionedSource
from bytewax import operators as op
from bytewax.connectors.stdio import StdOutSink
from typing import List

# Coinbase data source
class CoinbaseSource(FixedPartitionedSource):
    def list_parts(self):
        return ["BTC-USD"]

    def build_part(self, step_id, for_key, _resume_state):
        return CoinbasePartition(for_key)


class CoinbasePartition:
    def __init__(self, product_id):
        self._product_id = product_id
        self._data = iter([
            {"product_id": "BTC-USD", "bids": [["30000", "1.5"]], "asks": [["30010", "2.0"]]},
            {"product_id": "BTC-USD", "changes": [["buy", "30000", "1.0"]]},
        ])

    def next_batch(self):
        try:
            return [next(self._data)]
        except StopIteration:
            return []

    def snapshot(self):
        return None


# Define Dataflow
flow = Dataflow()

source = CoinbaseSource()
inp = op.input("coinbase", flow, source)

def process_orderbook(state, value):
    if state is None:
        state = {"bids": {}, "asks": {}}
    # Process bids and asks
    for bid, size in value.get("bids", []):
        state["bids"][float(bid)] = float(size)
    for ask, size in value.get("asks", []):
        state["asks"][float(ask)] = float(size)
    return state, {
        "best_bid": max(state["bids"].keys(), default=None),
        "best_ask": min(state["asks"].keys(), default=None)
    }

orderbook_stats = op.stateful_map("orderbook", inp, process_orderbook)

op.output("out", orderbook_stats, StdOutSink())
