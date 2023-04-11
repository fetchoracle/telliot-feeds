import math
from typing import Optional

from eth_abi import encode_single
from eth_utils.conversions import to_bytes
from telliot_core.utils.response import error_status
from web3 import Web3 as w3

from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds import DATAFEED_BUILDER_MAPPING
from telliot_feeds.reporters.tips import TYPES_WITH_GENERIC_SOURCE
from telliot_feeds.reporters.tips.listener.dtypes import QueryIdandFeedDetails
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.query_search_utils import decode_typ_name
from telliot_feeds.utils.query_search_utils import feed_from_catalog_feeds
from telliot_feeds.utils.query_search_utils import get_query_from_qtyp_name
from telliot_feeds.utils.query_search_utils import query_from_query_catalog

logger = get_logger(__name__)


class FundedFeedFilter:
    def generate_ids(self, feed: QueryIdandFeedDetails) -> tuple[bytes, bytes]:
        """Hash feed details to generate query id and feed id

        Return:
        - query_id: keccak(query_data)
        - feed_id: keccak(abi.encode(queryId,reward,startTime,interval,window,priceThreshold,rewardIncreasePerSecond)
        """
        query_id = to_bytes(hexstr=w3.keccak(feed.query_data).hex())
        feed_data = encode_single(
            "(bytes32,uint256,uint256,uint256,uint256,uint256,uint256)",
            [
                query_id,
                feed.params.reward,
                feed.params.startTime,
                feed.params.interval,
                feed.params.window,
                feed.params.priceThreshold,
                feed.params.rewardIncreasePerSecond,
            ],
        )
        feed_id = to_bytes(hexstr=w3.keccak(feed_data).hex())
        return feed_id, query_id

    def is_timestamp_first_in_window(
        self,
        timestamp_before: int,
        timestamp_to_check: int,
        feed_start_timestamp: int,
        feed_window: int,
        feed_interval: int,
    ) -> tuple[bool, int]:
        """
        Checks if timestamp is first in window

        Args:
        - timestamp_before: the timestamp to check against
        - timetamp_to_check: the timestamp thats checked if its first in window
        - feed_start_timestamp
        - feed_window
        - feed_interval

        Return: bool
        """
        # Number of intervals since start time
        num_intervals = math.floor((timestamp_to_check - feed_start_timestamp) / feed_interval)
        # Start time of latest submission window
        current_window_start = feed_start_timestamp + (feed_interval * num_intervals)
        time_diff = timestamp_to_check - current_window_start
        eligible = [time_diff < feed_window, timestamp_before < current_window_start]
        return all(eligible), time_diff

    async def price_change(self, query_data: bytes, value_before: bytes) -> Optional[float]:
        """Check if priceThreshold is met for submitting now

        Args:
        - query_id: used to get api source
        - value_before: the value used to compare current value

        Returns: float
        """
        query_id = bytes(w3.keccak(query_data))
        query_entry = query_from_query_catalog(qid=query_id.hex())
        if query_entry is not None:
            query = query_entry.query
            datafeed = CATALOG_FEEDS.get(query_entry.tag)
            if datafeed is None:
                logger.info(f"{query_entry.tag} not found in telliot CATALOG_FEEDS needed for priceThreshold check")
                return None
        else:
            qtype_name = decode_typ_name(query_data)
            datafeed = DATAFEED_BUILDER_MAPPING.get(qtype_name) if qtype_name in TYPES_WITH_GENERIC_SOURCE else None
            if datafeed is None:
                logger.info(f"No API source found for {query_id.hex()} to check priceThreshold")
                return None
            query = get_query_from_qtyp_name(query_data)
            if query is None:
                logger.info(f"Unable to decode query data {query_data.hex()}")
                return None
            datafeed.query = query
            for param in datafeed.query.__dict__.keys():
                val = getattr(query, param)
                setattr(datafeed.source, param, val)

        value_before_decoded = query.value_type.decode(value_before)
        if not isinstance(value_before_decoded, (int, float)):
            logger.info(f"Before value is not a number {value_before_decoded} can't calculate price change")
            return None
        if query_id not in self.prices:
            value_now = await datafeed.source.fetch_new_datapoint()

            if not value_now[0]:
                note = (
                    f"Unable to fetch data from API for {datafeed.query.descriptor}, to check if price threshold is met"
                )
                _ = error_status(note=note, log=logger.warning)
                return None

            self.prices[query_id] = value_now[0]

        return _get_price_change(previous_val=value_before_decoded, current_val=self.prices[query_id])

    def api_support_check(self, feeds: list[QueryIdandFeedDetails]) -> list[QueryIdandFeedDetails]:
        """Filter funded feeds where threshold is gt zero and no telliot catalog feeds support"""
        telliot_supported_with_api = []

        for feed in feeds:
            if feed.params.priceThreshold == 0:
                telliot_supported_with_api.append(feed)
            else:
                # check first if qtag in CATALOG_FEEDS which means a datafeed exists to check prices
                datafeed = feed_from_catalog_feeds(feed.query_data)
                # find query type in DATAFEEDBUILDER Mapping if qtype has generic source ie no manual entry required
                if datafeed is None:
                    qtype = decode_typ_name(feed.query_data)
                    if qtype in TYPES_WITH_GENERIC_SOURCE:
                        telliot_supported_with_api.append(feed)
                    else:
                        continue
                else:
                    telliot_supported_with_api.append(feed)

        return telliot_supported_with_api

    def filter_historical_submissions(self, feeds: list[QueryIdandFeedDetails]) -> list[QueryIdandFeedDetails]:
        """Check list of values for older submission would've been eligible for a tip
        if so the timestamps will be checked later to see if a tip for them has been claimed

        Args:
        - feeds

        Returns: filtered feeds list
        """
        for feed in feeds:
            # in case a query id has has none or too few to compare
            if len(feed.queryid_timestamps_values_list) < 2:
                continue
            for current, previous in zip(
                feed.queryid_timestamps_values_list[::-1], feed.queryid_timestamps_values_list[-2::-1]
            ):
                # if current timestamp is before feed start then no need to check
                if feed.params.startTime > current.timestamp:
                    feed.queryid_timestamps_values_list.remove(current)
                    continue
                in_eligibile_window = self.is_timestamp_first_in_window(
                    timestamp_before=previous.timestamp,
                    timestamp_to_check=current.timestamp,
                    feed_start_timestamp=feed.params.startTime,
                    feed_window=feed.params.window,
                    feed_interval=feed.params.interval,
                )
                if not in_eligibile_window:
                    if feed.params.priceThreshold == 0:
                        feed.queryid_timestamps_values_list.remove(current)
                    else:
                        try:
                            previous_value = int(int(previous.value.hex(), 16) / 1e18)
                        except ValueError:
                            _ = error_status("Error decoding current query id value")
                            continue

                        price_change = _get_price_change(previous_val=previous_value, current_val=current.value)

                        if price_change < feed.params.priceThreshold:
                            feed.queryid_timestamps_values_list.remove(current)

        return feeds

    def calculate_true_feed_balance(
        self, feeds: list[QueryIdandFeedDetails], unclaimed_timestamps_count: dict[tuple[bytes, bytes], int]
    ) -> list[QueryIdandFeedDetails]:
        """Reduce balance based on unclaimed count of reported timestamps

        Args:
        - feeds: list of feeds
        - unclaimed_timestamps_count: dict of queryid to unclaimed timestamps count

        Returns: list of feeds
        """
        for feed in list(feeds):
            key = (feed.feed_id, feed.query_id)
            if key not in unclaimed_timestamps_count:
                continue
            unclaimed_count = unclaimed_timestamps_count[key]
            feed.params.balance -= feed.params.reward * unclaimed_count
            # if remaining balance is zero filter out the feed from the list
            if feed.params.balance <= 0:
                feeds.remove(feed)
        return feeds

    async def window_and_priceThreshold_unmet_filter(
        self, feeds: list[QueryIdandFeedDetails], now_timestamp: int
    ) -> list[QueryIdandFeedDetails]:

        """Remove feeds from list that either submitting now won't be first in window
        or price threshold is not met

        Args:
        - feeds: list of feeds
        - now_timestamp: current timestamp used to check if first in window

        Returns: list of feeds that could possibly reward a tip
        """
        self.prices: dict[bytes, float] = {}
        for feed in list(feeds):
            # check if your timestamp will be first in window for
            # this feed if not discard feed_details
            # lesser node calls to make
            in_eligible_window, time_diff = self.is_timestamp_first_in_window(
                feed_interval=feed.params.interval,
                feed_start_timestamp=feed.params.startTime,
                feed_window=feed.params.window,
                timestamp_before=feed.current_value_timestamp,
                timestamp_to_check=now_timestamp,
            )

            balance = feed.params.balance
            price_threshold = feed.params.priceThreshold

            if in_eligible_window:
                sloped_reward = feed.params.rewardIncreasePerSecond * time_diff
                feed.params.reward += sloped_reward
                if balance < feed.params.reward:
                    feeds.remove(feed)
                continue
            elif price_threshold == 0 and not in_eligible_window:
                # if now_timestamp is not in eligible window, discard funded feed
                # remove feedId from feedId to queryId mapping
                # discard funded feed
                feeds.remove(feed)
                continue

            if price_threshold != 0 and not in_eligible_window:
                price_change = await self.price_change(
                    query_data=feed.query_data,
                    value_before=feed.current_queryid_value,
                )
                if price_change is None:
                    # unable to fetch price data
                    feeds.remove(feed)
                    continue
                if price_change < price_threshold:
                    feeds.remove(feed)
                    continue

        return feeds


def _get_price_change(previous_val: float, current_val: float) -> int:
    """Get percentage change

    Args:
    - previous value
    - current value

    Returns: int
    """
    if previous_val == 0:
        # if no before value set price change to 100 percent
        price_change = 10000
    elif current_val >= previous_val:
        price_change = int((10000 * (current_val - previous_val)) / previous_val)
    else:
        price_change = int((10000 * (previous_val - current_val)) / previous_val)

    return price_change
