from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsex_subgraph import PulseXSubgraphSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

tusdc_usd_median_feed = DataFeed(
    query=SpotPrice(asset="TUSDC", currency="USD"),
    source=PriceAggregator(
        asset="tusdc",
        currency="usd",
        algorithm="median",
        sources=[
            PulseXSubgraphSource(asset="t*usdc", currency="usd"), #pulsechain testnet USDC
        ],
    ),
)
