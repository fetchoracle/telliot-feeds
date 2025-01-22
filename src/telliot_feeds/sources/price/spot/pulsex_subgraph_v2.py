import os
#from dotenv import load_dotenv

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

pulsex_subgraph_supporten_tokens = {
#mainnet tokens
    #"wpls": "0xa1077a294dde1b09bb078844df40758a5d0f9a27",
    #"dai": "0xefd766ccb38eaf1dfd701853bfce31359239f305",
    #"usdc": "0x15d38573d2feeb82e7ad5187ab8c1d52810b1f07",
    #"plsx": "0x95b303987a60c71504d99aa1b13b4da07b0790ab",
    "fetch": "0xe39B70c9978E4232140d148Ad3C0b08f4A42220D",
    #"hex": "0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39",
    #"inc": "0x2fa878ab3f87cc1c9737fc071108f904c0b0c95d",
    "loan": "0x9159f1d2a9f51998fc9ab03fbd8f265ab14a1b3b",
#Testnet Tokens
    #"t*dai": "0x826e4e896cc2f5b371cd7bb0bd929db3e3db67c0",
    #"t*usdc": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    #"t*plsx": "0x8a810ea8b121d08342e9e7696f4a9915cbe494b7",
    "t*fetch": "0xC0573e2Fc47B26fb05097a553BBfcf0166bada0A",
    #"t*wpls": "0x70499adebb11efd915e3b69e700c331778628707",
    #"t*hex": "0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39",
    #"t*inc": "0x6eFAfcb715F385c71d8AF763E8478FeEA6faDF63",
    #"t*loan": "0x2720F69787cE6ba408fB6e2282d7640E805DF367",
}
TESTNET_GRAPH = "https://graph.v4.testnet.pulsechain.com"
MAINNET_GRAPH = "https://graph.pulsechain.com"

class PulseXSubgraphv2Service(WebPriceService):
    """PulseX Subgraph V2 Price Service for token price.
    Checks if the asset is testnet or mainnet and uses the correct url to fetch prices.
    It fetches prices from V2 pools of pulseX. Make sure to check token addresses are present in v2, otherwise use the regular pulseX source for V1."""

    def __init__(self, **kwargs: Any) -> None:  
        kwargs["name"] = "PulseX Subgraph V2 Price Service"
        kwargs["url"] = None
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the PulseX V2 hosted subgraphs

        """
        self.url = TESTNET_GRAPH if asset.startswith('t*') else MAINNET_GRAPH
        logger.info(f'Using {self.url} to fetch values')
        
        asset = asset.lower()
        currency = currency.lower()

        if currency != "usd":
            logger.error(f"Currency not supported: {currency}")
            return None, None

        token = pulsex_subgraph_supporten_tokens.get(asset, None)
        if not token:
            logger.error(f"Asset not supported: {asset}")
            return None, None

        headers = {
            "Content-Type": "application/json",
        }

        query = "{ token(id: \"" + token.lower() + "\") { derivedUSD } }"

        json_data = {
            "query": query,
            "variables": None,
            "operationName": None,
        }

        request_url = self.url + "/subgraphs/name/pulsechain/pulsexv2"

        with requests.Session() as s:
            try:
                r = s.post(request_url, headers=headers, json=json_data, timeout=self.timeout)
                res = r.json()
                data = {"response": res}

            except requests.exceptions.ConnectTimeout:
                logger.warning("Timeout Error, No prices retrieved from PulseX V2 Subgraph")
                return None, None

            except Exception as e:
                logger.warning(f"No prices retrieved from PulseX V2 Subgraph with Exception {e}")
                return None, None

        if "error" in data:
            logger.error(data)
            return None, None

        elif "response" in data:
            response = data["response"]

            try:
                if response["data"]["token"] == None:
                    logger.error(f"No data found for the token {token}")
                    logger.info(f"It is possible that no Liquidity Pool exists including this token ({token})")
                    return None, None

                price = float(response["data"]["token"]["derivedUSD"])
                return price, datetime_now_utc()
            except KeyError as e:
                msg = f"Error parsing Pulsechain Subgraph response: KeyError: {e}"
                if response["data"]["token"] == None:
                    msg = f"Invalid token address: {token}"
                logger.critical(msg)
                return None, None

        else:
            logger.error("Invalid response from get_url")
            return None, None


@dataclass
class PulseXSubgraphv2Source(PriceSource):
    asset: str = ""
    currency: str = ""
    service: PulseXSubgraphv2Service = field(default_factory=PulseXSubgraphv2Service, init=False)
