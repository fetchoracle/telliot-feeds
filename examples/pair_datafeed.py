import asyncio
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

from web3 import Web3
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.queries.price.spot_price import SpotPrice

PAIR_ABI = """
[
    {
        "constant": true, "inputs": [], "name": "getReserves",
        "outputs": [
            { "internalType": "uint112", "name": "_reserve0", "type": "uint112" },
            { "internalType": "uint112", "name": "_reserve1", "type": "uint112" },
            { "internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32" }
        ],
        "payable": false, "stateMutability": "view", "type": "function"
    },
    {
        "constant": true, "inputs": [], "name": "token0",
        "outputs": [
            { "internalType": "address", "name": "", "type": "address" }
        ], "payable": false, "stateMutability": "view", "type": "function"
    },
    {
        "constant": true, "inputs": [], "name": "token1",
        "outputs": [
            { "internalType": "address", "name": "", "type": "address" }
        ], "payable": false, "stateMutability": "view", "type": "function"
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
    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Your Price Service"
        kwargs["url"] = "https://rpc.pulsechain.com"
        self.pair_address = Web3.toChecksumAddress("0xE56043671df55dE5CDf8459710433C10324DE0aE")
        super().__init__(**kwargs)

    def get_amount_out(self, amount_in, reserve_in, reserve_out):
        amount_in_with_fee = amount_in*1000
        numerator = amount_in_with_fee*reserve_out
        denominator = reserve_in*1000 + amount_in_with_fee
        return float(numerator/denominator)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        try:
            w3 = Web3(Web3.HTTPProvider(self.url))
            pair_contract = w3.eth.contract(address=self.pair_address, abi=PAIR_ABI)

            token0_address = pair_contract.functions.token0().call()
            token1_address = pair_contract.functions.token1().call()

            token0_contract = w3.eth.contract(address=token0_address, abi=TOKEN_ABI)
            token1_contract = w3.eth.contract(address=token1_address, abi=TOKEN_ABI)

            token0_symbol = token0_contract.functions.symbol().call()
            token0_decimals = token0_contract.functions.decimals().call()

            print("Token0: ", token0_symbol) # WPLS
            print("Token0 Decimals: ", token0_decimals) # 18

            token1_symbol = token1_contract.functions.symbol().call()
            token1_decimals = token1_contract.functions.decimals().call()

            print("Token1: ", token1_symbol) # DAI
            print("Token1 Decimals: ", token1_decimals) # 18

            if asset.lower() not in token0_symbol.lower():
                raise Exception("Asset not found in pair")
            
            if currency.lower() not in token1_symbol.lower():
                raise Exception("Currency not found in pair")
            
            [reserve0, reserve1, timestamp] = pair_contract.functions.getReserves().call()

            decimals = token1_decimals
            if token1_symbol.lower() != currency.lower():
                reserve0, reserve1 = reserve1, reserve0
                decimals = token0_decimals

            price = self.get_amount_out(10 ** decimals, reserve0, reserve1)
            price = w3.fromWei(price, 'ether')

            print(f"Price of {asset} in {currency}: {price}")
            timestamp = datetime.fromtimestamp(timestamp)
            return float(price), timestamp
        except Exception as e:
            print("Error:", e)
            return None, None

@dataclass
class PairPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    addr: str = ""
    service: PairPriceService = field(default_factory=PairPriceService, init=False)

pls_usd_feed = DataFeed(
    query=SpotPrice(asset="pls", currency="usd"),
    source=PriceAggregator(
        asset="pls",
        currency="usd",
        algorithm="mean",
        sources=[PairPriceSource(asset="pls", currency="dai")],
    )
)
async def call_datafeed():
    await pls_usd_feed.source.fetch_new_datapoint()
    latest_data = pls_usd_feed.source.latest
    query = pls_usd_feed.query
    query_id = query.query_id
    print(f"""
        query: {query}
        query_id: {query_id.hex()}

        latest_data price: {latest_data[0]}
        latest_data timestamp: {latest_data[1]}
    """)

asyncio.run(call_datafeed())