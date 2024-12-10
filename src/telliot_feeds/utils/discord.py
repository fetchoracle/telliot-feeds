"""Send text messages using Twilio."""
import os
from typing import Any
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Union

load_dotenv()

import click
from discordwebhook import Discord

def generic_alert(msg: str) -> None:
    """Send a Discord message via webhook."""
    send_discord_msg_telliot(msg)
    return
    
def timestamp_convert(timestamp: int) -> str:
    '''Convert timestamp to local time.'''
    local_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return local_date
    
def submit_or_not(notification_data: Union[dict, str]) -> Union[str, dict]:
    '''Send a Discord message when the reporter succeeds or fails to submit a report'''
    if isinstance(notification_data, dict):
        notification_data['last_report'] = timestamp_convert(notification_data.get('last_report', 0))
    return send_discord_msg_telliot(notification_data)

def get_alert_bot_4() -> Discord:
    """Read the Discord webhook url from the environment."""
    DISCORD_WEBHOOK_URL_4 = os.getenv("DISCORD_WEBHOOK_URL_4")
    if not DISCORD_WEBHOOK_URL_4:
        raise Exception("Webhook not set. Won't send nofitication.")
    return Discord(url=DISCORD_WEBHOOK_URL_4)


def send_discord_msg_telliot(notification_data: Union[dict, str]) -> str:
    """Send Discord notification with data from notification dictionary in tellor360."""
    MONITOR_NAME = os.getenv("MONITOR_NAME_TELLIOT", "Monitor")
    if isinstance(notification_data, str):
        message = f"❗ {MONITOR_NAME} Notification:\n\n {notification_data}"
    else:
        message =(
            f"ℹ️ {MONITOR_NAME} Notification:\n"
            f"**Query:** {notification_data.get('query', 'N/A')}\n"
            f"**Price Submitted:** {notification_data.get('price_submitted', 0.0):.7f}".rstrip('0').rstrip('.') + "\n"
            f"**Account:** {notification_data.get('account', 'N/A')}\n"
            f"**Last Report at:** {notification_data.get('last_report', 'N/A')}\n"
            f"**Reporter Interval:** ~{timedelta(seconds=int(notification_data.get('reporter_lock_time', 0)))}\n"
            f"**Transaction URL:** {notification_data.get('transaction_url', 'N/A')}\n"
            f"**Rewards + Tips received:** ~{notification_data.get('tbrtips', 0.0):.4f} FETCH\n"
            f"**Percent and USD profits:** ~{notification_data.get('percent_profit', 'N/A'):.2f} %  |  "\
            f"~{notification_data.get('usd_profit', 'N/A'):.2f} USD \n"
        )
    try:
        get_alert_bot_4().post(content=message)
        return f"Discord notification: Sent to webhook api set in .env"
    except Exception as e:
        return f"Discord Notification: {e}"

def dispute_notification(msg: str) -> str:
    '''Send a notification if a dispute (stake lowered) is detected'''
    MONITOR_NAME = os.getenv("MONITOR_NAME_TELLIOT", "Monitor")
    message =(
        f"‼️{MONITOR_NAME} Notification:\n"
        f"**Check your Reporter:** {msg}'\n"
    )
    try:
        get_alert_bot_4().post(content=message)
        return f"Discord notification: Sent to webhook api set in .env"
    except Exception as e:
        return f"Discord Notification: {e}"
