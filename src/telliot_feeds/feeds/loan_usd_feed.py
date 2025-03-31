from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsex_subgraph_v2 import PulseXSubgraphv2Source
from telliot_feeds.sources.price.spot.dexscreener_api import DexScreenerApiSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

loan_usd_median_feed = DataFeed(
    query=SpotPrice(asset="LOAN", currency="USD"),
    source=PriceAggregator(
        asset="loan",
        currency="usd",
        algorithm="median",
        sources=[
            PulseXSubgraphv2Source(asset="loan", currency="usd"),
            DexScreenerApiSource(asset="369,pulsexv2,loan", currency="wpls"),
            DexScreenerApiSource(asset="369,9inch,loan", currency="wpls"),
        ],
    ),
)
