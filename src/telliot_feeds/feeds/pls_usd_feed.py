"""Example datafeed used by PLSUSDReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsechain_pulsex import PulsechainPulseXSource
from dotenv import load_dotenv
from telliot_feeds.utils.log import get_logger
import os

load_dotenv()
logger = get_logger(__name__)

DEFAULT_LP_CURRENCIES = ['usdt', 'usdc', 'dai']

def get_sources_objs():
    sources = os.getenv("PLS_CURRENCY_SOURCES")
    if not sources:
        logger.info(f"Using default '{DEFAULT_LP_CURRENCIES}' as currencies for PLS LP feed")
        return [PulsechainPulseXSource(asset="pls", currency=currency) for currency in DEFAULT_LP_CURRENCIES]
    sources_list = sources.split(',')
    return [PulsechainPulseXSource(asset="pls", currency=currency) for currency in sources_list]

pls_usd_feed = DataFeed(
    query=SpotPrice(asset="pls", currency="usd"),
    source=PriceAggregator(
        asset="pls",
        currency="usd",
        algorithm="weighted_average",
        sources=get_sources_objs(),
    ),
)
