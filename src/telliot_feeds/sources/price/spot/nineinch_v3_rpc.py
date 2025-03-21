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

POOL_ABI = """
[
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            { "internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160" },
            { "internalType": "int24", "name": "tick", "type": "int24" },
            { "internalType": "uint16", "name": "observationIndex", "type": "uint16" },
            { "internalType": "uint16", "name": "observationCardinality", "type": "uint16" },
            { "internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16" },
            { "internalType": "uint32", "name": "feeProtocol", "type": "uint32" },
            { "internalType": "bool", "name": "unlocked", "type": "bool" }
        ],
        "stateMutability": "view",
        "type": "function"
    },
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
    }
]
"""

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

class PairPriceService(WebPriceService):
    """9inch V3 RPC Price Service.
        Tries to fetch the asset price from a pool.
        Edit self.pair_address to match the asset and currency of the
        desired pool.
        This source works only with V3 pools (forks of PancakeSwap, like 9inch).
        Using stable coin pools we get an asset USD price, like fetch/usdl"""
    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "9inch V3 price service"
        kwargs["url"] = "https://rpc.pulsechain.com"
        self.pair_address = Web3.toChecksumAddress("0xf3dA9A1FF38c6D774e6aA583302A5aB7646b7025")
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        try:
            w3 = Web3(Web3.HTTPProvider(self.url))
            pool_contract = w3.eth.contract(address=self.pair_address, abi=POOL_ABI)
            logger.info(f"Fetching {asset}/{currency} in {self.pair_address} pool")

            token0_address = pool_contract.functions.token0().call()
            token1_address = pool_contract.functions.token1().call()

            logger.debug(f"Token0 address: {token0_address}")
            logger.debug(f"Token1 address: {token1_address}")

            token0_contract = w3.eth.contract(address=token1_address, abi=TOKEN_ABI)
            token1_contract = w3.eth.contract(address=token0_address, abi=TOKEN_ABI)

            token0_decimals = token0_contract.functions.decimals().call()
            token0_symbol = token0_contract.functions.symbol().call()

            token1_decimals = token1_contract.functions.decimals().call()
            token1_symbol = token1_contract.functions.symbol().call()

            logger.debug(f"Token0 Symbol: {token0_symbol}, Decimals: {token0_decimals}")
            logger.debug(f"Token1 Symbol: {token1_symbol}, Decimals: {token1_decimals}")

            block_number = w3.eth.block_number
            block = w3.eth.get_block(block_number)
            timestamp = block["timestamp"]

            # Get slot0 data with the price for pool
            slot0_data = pool_contract.functions.slot0().call()
            logger.debug(f'slot0_data: {slot0_data}')
            sqrt_price_x96 = slot0_data[0]
            logger.debug(f'sqrt_price_x96: {slot0_data[0]}')

            # Determine if asset is token0 or token1 to calculate correct asset price
            if token0_symbol.lower() == asset.lower():
                # token0 is the asset, so token1 is the currency (USDL)
                if token1_symbol.lower() == currency.lower():
                    price = ((2 ** 96) / sqrt_price_x96) ** 2 * (10 ** (token0_decimals - token1_decimals))
                    logger.debug(f"Price of {asset} in {currency}: {price}")
                else:
                    logger.error(f"Currency {currency} not found in the pool")
                    return None, None
            elif token1_symbol.lower() == asset.lower():
                # token1 is the asset, so token0 is the currency (USDL)
                if token0_symbol.lower() == currency.lower():
                    price = (sqrt_price_x96 / (2 ** 96)) ** 2 * (10 ** (token1_decimals - token0_decimals))
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
        except Exception as e:
            logger.critical("Error:", e)
            return None, None

@dataclass
class NineInchV3Source(PriceSource):
    asset: str = ""
    currency: str = ""
    addr: str = ""
    service: PairPriceService = field(default_factory=PairPriceService, init=False)