from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

# from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource

lleth_usd_median_feed = DataFeed(
    query=SpotPrice(asset="LLETH", currency="USD"),
    source=PriceAggregator(
        asset="lleth",
        currency="usd",
        algorithm="median",
        sources=[
            # BinanceSpotPriceSource(asset="eth", currency="btc"),
            CoinGeckoSpotPriceSource(asset="eth", currency="usd"),
            GeminiSpotPriceSource(asset="eth", currency="usd"),
            KrakenSpotPriceSource(asset="eth", currency="usd"),
            OKXSpotPriceSource(asset="eth", currency="usdt"),
        ],
    ),
)
