from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsex_subgraph import PulseXSubgraphSource
from telliot_feeds.sources.price.spot.pulsex_rpc import PulseXRPC
from telliot_feeds.sources.price.spot.dexscreener_api import DexScreenerApiSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

plsx_usd_median_feed = DataFeed(
    query=SpotPrice(asset="PLSX", currency="USD"),
    source=PriceAggregator(
        asset="plsx",
        currency="usd",
        algorithm="median",
        sources=[
            PulseXSubgraphSource(asset="plsx", currency="usd"),
            PulseXRPC(asset="plsx", currency="dai"),
            DexScreenerApiSource(asset="369,pulsex,plsx", currency="wpls"),
            DexScreenerApiSource(asset="369,9mm,plsx", currency="wpls"),
        ],
    ),
)
