"""Example datafeed used by PLSUSDReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price.spot.pulsex_subgraph import PulseXSubgraphSource
from telliot_feeds.sources.price.spot.dexscreener_api import DexScreenerApiSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

pls_usd_median_feed = DataFeed(
    query=SpotPrice(asset="PLS", currency="USD"),
    source=PriceAggregator(
        asset="pls",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="pls", currency="usd"),
            DexScreenerApiSource(asset="369,pulsex,wpls", currency="dai"),
            DexScreenerApiSource(asset="369,pulsex,wpls", currency="usdc"),
            DexScreenerApiSource(asset="369,pulsex,wpls", currency="usdt"),
            CoinpaprikaSpotPriceSource(asset="pls-pulsechain", currency="usd"),
            #UniswapV3PriceSource(asset="pls", currency="usd"), #needs an API key. If you have it, set it in Telliot folder in HOME and comment this out
            PulseXSubgraphSource(asset="wpls", currency="usd"),
        ],
    ),
)