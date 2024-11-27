from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.sources.price.spot.pulsex_fetch_dai import PulseXFETCHDAISource
from dotenv import load_dotenv

load_dotenv()

fetch_usd_feed = DataFeed(
    query=SpotPrice(asset="fetch", currency="usd"),
    source=PriceAggregator(
        asset="fetch",
        currency="usd",
        algorithm="weighted_average",
        sources=[PulseXFETCHDAISource(asset="fetch", currency="pls")],
    )
)
