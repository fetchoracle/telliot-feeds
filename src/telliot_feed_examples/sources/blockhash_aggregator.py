from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Optional

import requests
from telliot_core.datasource import DataSource
from telliot_core.dtypes.datapoint import DataPoint
from web3 import Web3

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)

w3 = Web3(
    Web3.HTTPProvider(
        "https://eth-mainnet.alchemyapi.io/v2/hP3lNPFpxPSwfwJtfaZi4ezZlPgimAnN"
    )
)


@dataclass
class TellorRNGManualSource(DataSource[Any]):
    """DataSource for TellorRNG manually-entered timestamp."""

    timestamp = 0

    def parse_user_val(self) -> int:
        """Parse timestamp from user input."""
        print("Enter timestamp for generating a random number: ")

        data = None
        while data is None:
            inpt = input()

            try:
                inpt = int(inpt)  # type: ignore
            except ValueError:
                print("Invalid input. Enter decimal value (int).")
                continue

            print(
                "Generating random number from timestamp: "
                f"{inpt}\nPress [ENTER] to confirm."
            )
            _ = input()
            data = inpt

        # data = 1649769707
        self.timestamp = data
        return data

    def getEthHashByTimestamp(self, timestamp: int) -> str:
        this_block = w3.eth.get_block("latest")
        if this_block is None:
            return ""
        if this_block["timestamp"] < timestamp:
            return ""
        else:
            min_num: int = 0
            max_num: int = this_block["number"]
            mid_num: int = 0
            while max_num - min_num > 1:
                mid_num = round((max_num + min_num) / 2)
                this_block = w3.eth.get_block(mid_num)
                if this_block["timestamp"] > timestamp:
                    max_num = mid_num
                else:
                    min_num = mid_num
            this_block = w3.eth.get_block(max_num)
            return str(this_block["hash"].hex())

    def getBtcHashByTimestamp(self, timestamp: int) -> str:
        this_block = requests.get("https://blockchain.info/latestblock").json()
        if this_block is None:
            return ""
        if this_block["time"] < timestamp:
            return ""
        else:
            min_num: int = 0
            max_num: int = this_block["height"]
            mid_num: int = 0
            while max_num - min_num > 1:
                mid_num = round((max_num + min_num) / 2)
                this_block = requests.get(
                    "https://blockchain.info/rawblock/" + str(mid_num)
                ).json()
                if this_block["time"] > timestamp:
                    max_num = mid_num
                else:
                    min_num = mid_num
            this_block = requests.get(
                "https://blockchain.info/rawblock/" + str(max_num)
            ).json()
            return str(this_block["hash"])

    async def fetch_new_datapoint(self) -> DataPoint[bytes]:
        """Update current value with time-stamped value fetched from user input.

        Returns:
            Current time-stamped value
        """
        eth_hash: str = ""
        btc_hash: str = ""

        # while len(eth_hash) == 0 and len(btc_hash) == 0:
        while eth_hash == "" and btc_hash == "":
            if self.timestamp == 0:
                timestamp = self.parse_user_val()
            else:
                timestamp = self.timestamp
            eth_hash = self.getEthHashByTimestamp(timestamp)
            btc_hash = self.getBtcHashByTimestamp(timestamp)

        data = Web3.solidityKeccak(["string", "string"], [eth_hash, str(btc_hash)])
        dt = datetime.fromtimestamp(self.timestamp, tz=timezone.utc)
        datapoint = (data, dt)

        self.store_datapoint(datapoint)

        logger.info(f"Stored random number for timestamp {timestamp}: {data}")

        return datapoint
