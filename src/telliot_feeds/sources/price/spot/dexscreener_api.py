import os
import logging
from dataclasses import dataclass
from dataclasses import field
from typing import Any

from decimal import Decimal

import requests

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.INFO)

dexscreener_supported_pools = {
#pulsechain exchanges:
"9inch":{
    "fetch/usdl": "0xf3dA9A1FF38c6D774e6aA583302A5aB7646b7025",
},
"9mm":{
    "fetch/wpls": "0x547998b2119dB28a62Ff91FDD64032f6176e9060",
},
"pulsex":{
    "fetch/wpls": "0xDFB503E2da6D58eFFfB1710AaDf7A97f21EA76ad",
},
#BASE exchanges:
"aerodrome":{
    "aero/usdc": "0x6cDcb1C4A4D1C3C6d054b27AC5B77e89eAFb971d",
},

}

dexscreener_supported_chains = {
    "369": "pulsechain",
    "8453": "base",

}
MAINNET_API_URL = "https://api.dexscreener.com"

class DexScreenerService(WebPriceService):
    """DexScreener API Price Service for specific pool prices.
    Checks if the pool and chain are valid and tries to fetch the asset price.
    Need to pass 'asset' from the feed like this:
    asset= 'chain,exchange,asset'.
    Double check chain and exchange are present in supported pools and chains."""

    def __init__(self, **kwargs: Any) -> None:  
        kwargs["name"] = "DexScreener API source"
        kwargs["url"] = None
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface
        This implementation gets the price from the DexScreener API
        """
        logger.debug(f'Using {MAINNET_API_URL} to fetch {asset}/{currency}')
        logger.debug(f'asset received:{asset}')

        #splitting 'asset' values to get chain, exchange and asset
        parts = asset.split(",", 2)
        if len(parts) == 3:
            chain = parts[0]
            exchange = parts[1]
            asset = parts[2]
        else:
            logger.error('Missing information for chain, exchange and asset to fetch pool address')
            return None, None

        chain_id = dexscreener_supported_chains.get(chain)
        if not chain_id:
            #Checks the chain requested to fetch the pool address is valid.
            logger.error(f"ChainID not supported for: {chain}")
            return None, None

        asset = asset.lower()
        currency = currency.lower()

        if exchange in dexscreener_supported_pools:
            exchange_pools = dexscreener_supported_pools[exchange]
            key = asset + '/' + currency
            if key in exchange_pools:
                pair_id = exchange_pools[key]
            else:
                logger.error(f"No pool address for {key} in {exchange}")
                return None, None
        else:
            logger.error(f"Exchange {exchange} not supported")
            return None, None
        logger.info(f'Fetching {asset}/{currency} in {exchange}')

        request_url = MAINNET_API_URL + f"/latest/dex/pairs/{chain_id}/{pair_id}"

        with requests.Session() as s:
            try:
                r = s.get(request_url, timeout=self.timeout)
                r.raise_for_status()
                res = r.json()
                data = res

            except requests.exceptions.RequestException as e:
                logger.error(f"Error during request: {e}")
                return None, None

        if not isinstance(data, dict):
            logger.error("Data fetched is not a dictionary.")
            return None, None

        if "pair" not in data:
            logger.error("Missing 'pair' key in data fetched.")
            return None, None

        pair_data = data["pair"]

        if not isinstance(pair_data, dict):
            logger.error("'pair' data fetched is not a dictionary.")
            return None, None

        if "priceUsd" not in pair_data:
            logger.error("Missing 'priceUsd' key in 'pair' data fetched.")
            return None, None

        if pair_data["pairAddress"] != pair_id:
            logger.error(f"Pool address returned {pair_data['pairAddress']} is different than requested: {pair_id}.")
            return None, None

        try:
            price_usd = float(pair_data["priceUsd"])
            if price_usd <= 0:
                logger.error(f"Invalid priceUsd value: {price_usd}. Price should be positive.")
                return None, None
        except (ValueError, TypeError):
            logger.error(f"Invalid 'priceUsd' format: {pair_data['priceUsd']}.")
            return None, None

        return price_usd, datetime_now_utc()


@dataclass
class DexScreenerApiSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: DexScreenerService = field(default_factory=DexScreenerService, init=False)
