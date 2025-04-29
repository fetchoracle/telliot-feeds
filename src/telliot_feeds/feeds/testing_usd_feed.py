"""Example testing feed for QA"""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsex_rpc import PulseXRPC
from telliot_feeds.sources.price.spot.dexscreener_api import DexScreenerApiSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

testing_usd_median_feed = DataFeed(
    query=SpotPrice(asset="TESTING", currency="USD"),
    source=PriceAggregator(
        asset="testing",
        currency="usd",
        algorithm="median",
        sources=[
            PulseXRPC(asset="wpls", currency="dai"),
            PulseXRPC(asset="wpls", currency="usdc"),
            PulseXRPC(asset="wpls", currency="usdt"),
            PulseXRPC(asset="wpls2", currency="dai"),
            DexScreenerApiSource(asset="369,pulsexv2,wpls", currency="dai"),
            DexScreenerApiSource(asset="369,pulsexv2,wpls", currency="plsx"),
        ],
    ),
)