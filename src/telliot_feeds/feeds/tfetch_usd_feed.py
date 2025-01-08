"""Datafeed for current price of FETCH in USD."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.pulsex_subgraph import PulseXSubgraphSource
from telliot_feeds.sources.price.spot.fetch_usd_mock import FetchUsdMockSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator
from dotenv import load_dotenv
import os

load_dotenv()

if os.getenv("FETCH_USD_MOCK_PRICE"):
    tfetch_usd_median_feed = DataFeed(
        query=SpotPrice(asset="tfetch", currency="usd"),
        source=FetchUsdMockSpotPriceSource(asset="tfetch", currency="usd")
        )
        
else:
    tfetch_usd_median_feed = DataFeed(
        query=SpotPrice(asset="tfetch", currency="usd"),
        source=PriceAggregator(
            asset="tfetch",
            currency="usd",
            algorithm="median",
            sources=[PulseXSubgraphSource(asset="t*fetch", currency="usd")],
        )
    )
