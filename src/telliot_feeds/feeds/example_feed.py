from telliot_feeds.datafeed import DataFeed
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.example_source import PairPriceSource

pls_usd_feed = DataFeed(
    query=SpotPrice(asset="pls", currency="usd"),
    source=PriceAggregator(
        asset="pls",
        currency="usd",
        algorithm="mean",
        sources=[PairPriceSource(asset="pls", currency="dai")],
    )
)
