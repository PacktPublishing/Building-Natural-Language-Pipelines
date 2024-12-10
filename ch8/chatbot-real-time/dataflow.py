from bytewax.dataflow import Dataflow
from bytewax.inputs import (FixedPartitionedSource,\
                            StatefulSourcePartition,\
                            batch_async)
from bytewax import operators as op
from bytewax.connectors.stdio import StdOutSink
from bytewax.connectors.files import FileSink
from bytewax.run import cli_main
import websockets
import json
from dataclasses import dataclass, field
from datetime import timedelta, datetime
from typing import Dict, List, Optional
import ssl
import threading
import time
import sys 

async def _ws_agen(product_id):
    """Connect to websocket and yield messages as they arrive."""
    url = "wss://ws-feed.exchange.coinbase.com"
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)

    async with websockets.connect(url, ssl=ssl_context, max_size=10**7) as websocket:
        msg = json.dumps(
            {
                "type": "subscribe",
                "product_ids": [product_id],
                "channels": ["level2_batch"],
            }
        )
        await websocket.send(msg)
        await websocket.recv()

        while True:
            msg = await websocket.recv()
            try:
                # Parse the incoming message as JSON
                parsed_msg = json.loads(msg)
                yield (product_id, parsed_msg)  # Ensure we yield (key, dictionary)
            except json.JSONDecodeError as e:
                print(f"Error decoding message: {msg}, error: {e}")



class CoinbasePartition(StatefulSourcePartition):
    def __init__(self, product_id):
        agen = _ws_agen(product_id)
        self._batcher = batch_async(agen, timedelta(seconds=0.5), 100)

    def next_batch(self):
        return next(self._batcher)


    def snapshot(self):
        return None

class CoinbaseSource(FixedPartitionedSource):
    def list_parts(self):
        return ["BTC-USD"]

    def build_part(self, step_id, for_key, _resume_state):
        return CoinbasePartition(for_key)

@dataclass(frozen=True)
class OrderBookSummary:
    """Represents a summary of the order book state."""

    bid_price: float
    bid_size: float
    ask_price: float
    ask_size: float
    spread: float
    timestamp: datetime

@dataclass
class OrderBookState:
    """Maintains the state of the order book."""

    bids: Dict[float, float] = field(default_factory=dict)
    asks: Dict[float, float] = field(default_factory=dict)
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None

    def update(self, data):
        """Update the order book state with the given data.

        Args:
            data: The data to update the order book state with.
        """
        # Initialize bids and asks if they're empty
        if not self.bids:
            self.bids = {float(price): float(size) for price, size in data["bids"]}
            self.bid_price = max(self.bids.keys(), default=None)
        if not self.asks:
            self.asks = {float(price): float(size) for price, size in data["asks"]}
            self.ask_price = min(self.asks.keys(), default=None)

        # Process updates from the "changes" field in the data
        for change in data.get("changes", []):
            side, price_str, size_str = change
            price, size = float(price_str), float(size_str)

            target_dict = self.asks if side == "sell" else self.bids

            # If size is zero, remove the price level; otherwise,
            # update/add the price level
            if size == 0.0:
                target_dict.pop(price, None)
            else:
                target_dict[price] = size

            # After update, recalculate the best bid and ask prices
            if side == "sell":
                self.ask_price = min(self.asks.keys(), default=None)
            else:
                self.bid_price = max(self.bids.keys(), default=None)

    def spread(self) -> float:
        """Calculate the spread between the best bid and ask prices.

        Returns:
            float: The spread between the best bid and ask prices.
        """
        return self.ask_price - self.bid_price  # type: ignore

    
    def summarize(self):
        """Summarize the order book state.

        Returns:
            OrderBookSummary: A summary of the order book state.
        """
        return OrderBookSummary(
            bid_price=self.bid_price,
            bid_size=self.bids[self.bid_price],
            ask_price=self.ask_price,
            ask_size=self.asks[self.ask_price],
            spread=self.spread(),
            timestamp=datetime.now(),
        )


def create_dataflow(init_name, percentage):
    flow = Dataflow(init_name)
    source = CoinbaseSource()
    inp = op.input("coinbase", flow, source)

    def mapper(state, value):
        """Update the state with the given value and return the state and a summary."""
        if state is None:
            state = OrderBookState()

        state.update(value)
        return (state, state.summarize())

    stats = op.stateful_map("orderbook", inp, mapper)
    
    def just_large_spread(prod_summary):
        """Filter out products with a spread less than a given percentage."""
        product, summary = prod_summary
        return summary.spread / summary.ask_price > percentage
        
    filter = op.filter("big_spread", stats, just_large_spread)
    op.output("out", filter, StdOutSink())
    
    return flow

# Example usage
percentage = 0.0001
timer = 5  # Run for 5 seconds
flow = create_dataflow("coinbase", percentage)
cli_main(flow)  # Use run_main to handle Bytewax's lifecycle
