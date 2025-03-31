from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsex_subgraph import PulseXSubgraphSource
from telliot_feeds.sources.price.spot.pulsex_subgraph_v2 import PulseXSubgraphv2Source
from telliot_feeds.sources.price.spot.dexscreener_api import DexScreenerApiSource
from telliot_feeds.sources.price.spot.pulsex_rpc import PulseXRPC
from telliot_feeds.sources.price_aggregator import PriceAggregator

inc_usd_median_feed = DataFeed(
    query=SpotPrice(asset="INC", currency="USD"),
    source=PriceAggregator(
        asset="inc",
        currency="usd",
        algorithm="median",
        sources=[
            PulseXSubgraphSource(asset="inc", currency="usd"),
            PulseXSubgraphv2Source(asset="inc", currency="usd"),
            DexScreenerApiSource(asset="369,pulsex,inc", currency="wpls"),
            DexScreenerApiSource(asset="369,pulsex,inc", currency="plsx"),
            DexScreenerApiSource(asset="369,pulsexv2,inc", currency="wpls"),
            DexScreenerApiSource(asset="369,pulsexv2,inc", currency="plsx"),
        ],
    ),
)