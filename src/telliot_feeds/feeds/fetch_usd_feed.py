"""Datafeed for current price of FETCH in USD."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.dexscreener_api import DexScreenerApiSource
from telliot_feeds.sources.price.spot.nineinch_v3_rpc import NineInchV3Source
from telliot_feeds.sources.price_aggregator import PriceAggregator

fetch_usd_median_feed = DataFeed(
    query=SpotPrice(asset="fetch", currency="usd"),
    source=PriceAggregator(
        asset="fetch",
        currency="usd",
        algorithm="median",
        sources=[
            DexScreenerApiSource(asset="369,9inch,fetch", currency="usdl"),
            NineInchV3Source(asset="fetch", currency="usdl"),
        ],
    )
)
