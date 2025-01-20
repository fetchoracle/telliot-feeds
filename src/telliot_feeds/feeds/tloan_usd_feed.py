from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsex_subgraph import PulseXSubgraphSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

tloan_usd_median_feed = DataFeed(
    query=SpotPrice(asset="TLOAN", currency="USD"),
    source=PriceAggregator(
        asset="tloan",
        currency="usd",
        algorithm="median",
        sources=[
            PulseXSubgraphSource(asset="t*loan", currency="usd"),
        ],
    ),
)
