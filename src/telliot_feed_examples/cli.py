""" Telliot Feed Examples CLI

A simple interface for interacting with telliot example feed functionality.
"""
import asyncio
from typing import Tuple

import click
from click.core import Context
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.contract.contract import Contract
from telliot_core.directory.tellorx import tellor_directory
from telliot_core.model.endpoints import RPCEndpoint

from telliot_feed_examples.feeds import LEGACY_DATAFEEDS
from telliot_feed_examples.reporters.interval import IntervalReporter
from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


# Get default configs from ~/telliot/
cfg = TelliotConfig()


def get_tellor_contracts(
    private_key: str, chain_id: int, endpoint: RPCEndpoint
) -> Tuple[Contract, Contract]:
    """Get Contract objects per telliot configuration and
    CLI flag options."""
    endpoint.connect()

    tellor_oracle = tellor_directory.find(chain_id=chain_id, name="oracle")[0]
    oracle = Contract(
        address=tellor_oracle.address,
        abi=tellor_oracle.abi,
        node=endpoint,
        private_key=private_key,
    )
    oracle.connect()

    tellor_master = tellor_directory.find(chain_id=chain_id, name="master")[0]
    master = Contract(
        address=tellor_master.address,
        abi=tellor_master.abi,
        node=endpoint,
        private_key=private_key,
    )
    master.connect()

    return master, oracle


# Main CLI options
@click.group()
@click.option(
    "--private-key",  # flag option 1
    "-pk",  # flag option 2
    "private_key",  # variable name of user input
    help="override the config's private key",
    required=False,
    nargs=1,
    default=cfg.main.private_key,
    type=str,
)
@click.option(
    "--chain-id",
    "-cid",
    "chain_id",
    help="override the config's chain ID",
    required=False,
    nargs=1,
    default=cfg.main.chain_id,
    type=int,
)
@click.pass_context
def cli(ctx: Context, private_key: str, chain_id: int) -> None:
    """Telliot command line interface"""
    ctx.ensure_object(dict)
    ctx.obj["PRIVATE_KEY"] = private_key
    ctx.obj["CHAIN_ID"] = chain_id


# Report subcommand options
@cli.command()
@click.option(
    "--legacy-id",
    "-lid",
    "legacy_id",
    help="report to a legacy ID",
    required=True,
    nargs=1,
    type=str,
)
@click.option("--submit-once/--submit-continuous", default=False)
@click.pass_context
def report(ctx: Context, legacy_id: str, submit_once: bool) -> None:
    """Report values to Tellor oracle"""

    # Ensure valid legacy id
    if legacy_id not in LEGACY_DATAFEEDS:
        click.echo(
            f"Invalid legacy ID. Valid choices: {', '.join(list(LEGACY_DATAFEEDS))}"
        )
        return

    click.echo(f"Reporting legacy ID: {legacy_id}")

    private_key = ctx.obj["PRIVATE_KEY"]
    chain_id = ctx.obj["CHAIN_ID"]
    endpoint = cfg.get_endpoint()

    click.echo(f"Current chain ID: {chain_id}")

    master, oracle = get_tellor_contracts(
        private_key=private_key, endpoint=endpoint, chain_id=chain_id
    )

    chosen_feed = LEGACY_DATAFEEDS[legacy_id]

    legacy_reporter = IntervalReporter(
        endpoint=endpoint,
        private_key=private_key,
        master=master,
        oracle=oracle,
        datafeed=chosen_feed,
    )

    if submit_once:
        _, _ = asyncio.run(legacy_reporter.report_once())
    else:
        _, _ = asyncio.run(legacy_reporter.report())


if __name__ == "__main__":
    cli()