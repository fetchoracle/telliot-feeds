from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsex_subgraph import PulseXSubgraphSource
from telliot_feeds.sources.price.spot.pulsex_subgraph_v2 import PulseXSubgraphv2Source
from telliot_feeds.sources.price.spot.pulsex_rpc import PulseXRPC
from telliot_feeds.sources.price.spot.dexscreener_api import DexScreenerApiSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

hex_usd_median_feed = DataFeed(
    query=SpotPrice(asset="HEX", currency="USD"),
    source=PriceAggregator(
        asset="hex",
        currency="usd",
        algorithm="median",
        sources=[
            PulseXSubgraphSource(asset="hex", currency="usd"),
            DexScreenerApiSource(asset="369,pulsex,hex", currency="wpls"),
            DexScreenerApiSource(asset="369,pulsexv2,hex", currency="wpls"),
            DexScreenerApiSource(asset="369,pulsexv2,hex", currency="usdc"),
            PulseXSubgraphv2Source(asset="hex", currency="usd"),
            PulseXRPC(asset="hex", currency="usdc"),
        ],
    ),
)