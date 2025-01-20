"""Datafeed for current price of FETCH in USD."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.pulsex_subgraph_v2 import PulseXSubgraphv2Source
from telliot_feeds.sources.price_aggregator import PriceAggregator

fetch_usd_median_feed = DataFeed(
    query=SpotPrice(asset="fetch", currency="usd"),
    source=PriceAggregator(
        asset="fetch",
        currency="usd",
        algorithm="median",
        sources=[PulseXSubgraphv2Source(asset="fetch", currency="usd")],
    )
)
