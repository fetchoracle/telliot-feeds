import logging
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

from web3 import Web3
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.INFO)

POOL_ABI = [
    {
        "inputs": [],
        "name": "token0",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {
                "internalType": "uint112",
                "name": "_reserve0",
                "type": "uint112"
            },
            {
                "internalType": "uint112",
                "name": "_reserve1",
                "type": "uint112"
            },
            {
                "internalType": "uint32",
                "name": "_blockTimestampLast",
                "type": "uint32"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

TOKEN_ABI = """
[
    {
        "constant": true, "inputs": [], "name": "decimals", "outputs": [
            { "internalType": "uint8", "name": "", "type": "uint8" }
        ], "payable": false, "stateMutability": "view", "type": "function"
    },
    {
        "constant": true, "inputs": [], "name": "symbol",
        "outputs": [
            { "internalType": "string", "name": "", "type": "string" }
        ], "payable": false, "stateMutability": "view", "type": "function"
    }
]
"""

supported_pools = {
    "wpls/dai": "0xE56043671df55dE5CDf8459710433C10324DE0aE",
    "wpls/usdc": "0x6753560538ECa67617A9Ce605178F788bE7E524E",
    "wpls/usdt": "0x322Df7921F28F1146Cdf62aFdaC0D6bC0Ab80711",
}

class PairPriceService(WebPriceService):
    """pulseX RPC Price Service.
        Tries to fetch the asset price from a pool using the RPC.
        Edit 'supported pools' if the desired pool is not present.
        Using stable coin pools we get an asset's USD price, like wpls/dai"""
    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "pulseX RPC price service"
        kwargs["url"] = "https://rpc.pulsechain.com"
        self.pair_address = None
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        try:
            w3 = Web3(Web3.HTTPProvider(self.url))

            if asset + '/' + currency in supported_pools:
                self.pair_address = supported_pools.get(asset+'/'+currency)
            else:
                logger.error(f"Asset: {asset} and Currency: {currency} not in supported pools list")
                return None, None

            pool_contract = w3.eth.contract(address=self.pair_address, abi=POOL_ABI)
            logger.debug(f"Fetching {asset}/{currency} in {self.pair_address} pool")

            token0_address = pool_contract.functions.token0().call()
            token1_address = pool_contract.functions.token1().call()

            logger.debug(f"Token0 address: {token0_address}")
            logger.debug(f"Token1 address: {token1_address}")

            token0_contract = w3.eth.contract(address=token0_address, abi=TOKEN_ABI)
            token1_contract = w3.eth.contract(address=token1_address, abi=TOKEN_ABI)

            token0_decimals = token0_contract.functions.decimals().call()
            token0_symbol = token0_contract.functions.symbol().call()

            token1_decimals = token1_contract.functions.decimals().call()
            token1_symbol = token1_contract.functions.symbol().call()

            logger.debug(f"Token0 Symbol: {token0_symbol}, Decimals: {token0_decimals}")
            logger.debug(f"Token1 Symbol: {token1_symbol}, Decimals: {token1_decimals}")

            # Get reserve from pool
            reserves = pool_contract.functions.getReserves().call()
            reserve0 = reserves[0]
            reserve1 = reserves[1]
            timestamp = reserves[2]

            # Determine if asset is token0 or token1 to calculate correct asset price
            if token0_symbol.lower() == asset.lower():
                # token0 is the asset, so token1 is the currency
                if token1_symbol.lower() == currency.lower():
                    price = (reserve1 / (10 ** token1_decimals)) / (reserve0 / (10 ** token0_decimals))
                    logger.debug(f"Price of {asset} in {currency}: {price}")
                else:
                    logger.error(f"Currency {currency} not found in the pool")
                    return None, None
            elif token1_symbol.lower() == asset.lower():
                # token1 is the asset, so token0 is the currency
                if token0_symbol.lower() == currency.lower():
                    price = (reserve0 / (10 ** token0_decimals)) / (reserve1 / (10 ** token1_decimals))
                    logger.debug(f"Price of {asset} in {currency}: {price}")
                else:
                    logger.error(f"Currency {currency} not found in the pool")
                    return None, None
            else:
                logger.error(f"Asset {asset} not found in the pool {self.pair_address}")
                return None, None

            logger.debug(f"Price of {asset} in {currency}: {price}")
            timestamp = datetime.fromtimestamp(timestamp)
            return float(price), timestamp
            #return None, None
        except Exception as e:
            logger.critical("Error:", e)
            return None, None

@dataclass
class PulseXRPC(PriceSource):
    asset: str = ""
    currency: str = ""
    addr: str = ""
    service: PairPriceService = field(default_factory=PairPriceService, init=False)