"""Example datafeed used by PLSUSDReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsex_rpc import PulseXRPC
from telliot_feeds.sources.price.spot.dexscreener_api import DexScreenerApiSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

plstest_usd_median_feed = DataFeed(
    query=SpotPrice(asset="PLStest", currency="USD"),
    source=PriceAggregator(
        asset="plstest",
        currency="usd",
        algorithm="median",
        sources=[
            PulseXRPC(asset="wpls", currency="dai"),
            PulseXRPC(asset="wpls", currency="usdc"),
            PulseXRPC(asset="wpls", currency="usdt"),
            DexScreenerApiSource(asset="369,pulsex,wpls", currency="dai"),
            DexScreenerApiSource(asset="369,pulsexv2,wpls", currency="dai"),
            DexScreenerApiSource(asset="369,pulsex,wpls", currency="usdc"),
            DexScreenerApiSource(asset="369,pulsex,wpls", currency="usdt"),
            DexScreenerApiSource(asset="369,pulsexv2,wpls", currency="plsx"),
            DexScreenerApiSource(asset="369,9inch,wpls", currency="plsx"),
        ],
    ),
)