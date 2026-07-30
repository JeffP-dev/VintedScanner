#!/usr/bin/env python3
import argparse
import sys
import time
import json
import Config
import smtplib
import logging
import requests
import email.utils
from datetime import datetime
from email.message import EmailMessage
from logging.handlers import RotatingFileHandler


# Configure a rotating file handler to manage log files
handler = RotatingFileHandler("vinted_scanner.log", maxBytes=5000000, backupCount=5)

logging.basicConfig(handlers=[handler], 
                    format="%(asctime)s - %(filename)s - %(funcName)10s():%(lineno)s - %(levelname)s - %(message)s", 
                    level=logging.INFO)

# Timeout configuration for the requests
timeoutconnection = 30

# List to keep track of already analyzed items
list_analyzed_items = []

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-GPC": "1",
    "Priority": "u=0, i",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Search Vinted for new items and send the configured notifications."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "show new items without sending notifications; "
            "found items are still saved in the local database"
        ),
    )
    return parser.parse_args()


# Load previously analyzed item hashes to avoid duplicates
def load_analyzed_item():
    try:
        with open("vinted_items.txt", "r", errors="ignore") as f:
            for line in f:
                if line:
                    list_analyzed_items.append(line.rstrip())
    except IOError as e:
        logging.error(e, exc_info=True)
        sys.exit()

# Save a new analyzed item to prevent repeated alerts
def save_analyzed_item(hash):
    try:
        with open("vinted_items.txt", "a") as f:
            f.write(str(hash) + "\n")
    except IOError as e:
        logging.error(e, exc_info=True)
        sys.exit()

# Send notification e-mail when a new item is found
def send_email(item_title, item_price, item_url, item_image):
    try:
        # Create the e-mail message
        msg = EmailMessage()
        msg["To"] = Config.smtp_toaddrs
        msg["From"] = email.utils.formataddr(("Vinted Scanner", Config.smtp_from))
        msg["Subject"] = "Vinted Scanner - New Item"
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid()

        # Format message content
        body_lines = [item_title, str(item_price), f"🔗 {item_url}"]
        if item_image:
            body_lines.append(f"📷 {item_image}")
        body = "\n".join(body_lines)

        msg.set_content(body)
        
        # Securely opening the SMTP connection
        with smtplib.SMTP(Config.smtp_server, 587) as smtpserver:
            smtpserver.ehlo()
            smtpserver.starttls()
            smtpserver.ehlo()

            # Authentication
            smtpserver.login(Config.smtp_username, Config.smtp_psw)
            
            # Sending the message
            smtpserver.send_message(msg)
            logging.info("E-mail sent")
    
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error sending email: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"Error sending email: {e}", exc_info=True)


# Send a Slack message when a new item is found
def send_slack_message(item_title, item_price, item_url, item_image):
    webhook_url = Config.slack_webhook_url 

    # Format message content
    message_lines = [f"*{item_title}*", f"🏷️ {item_price}", f"🔗 {item_url}"]
    if item_image:
        message_lines.append(f"📷 {item_image}")
    message = "\n".join(message_lines)
    slack_data = {"text": message}

    try:
        response = requests.post(
            webhook_url, 
            data=json.dumps(slack_data),
            headers={"Content-Type": "application/json"},
            timeout=timeoutconnection
        )

        if response.status_code != 200:
            logging.error(f"Slack notification failed: {response.status_code}, {response.text}")
        else:
            logging.info("Slack notification sent")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Slack message: {e}")

# Send a Telegram message when a new item is found
def send_telegram_message(item_title, item_price, item_url, item_image):

    # Format message content
    message_lines = [f"<b>{item_title}</b>", f"🏷️ {item_price}", f"🔗 {item_url}"]
    if item_image:
        message_lines.append(f"📷 {item_image}")
    message = "\n".join(message_lines)

    try:
        url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"

        params = {
            "chat_id": Config.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML",
            "link_preview_options":  json.dumps({
                "is_disabled": True
            })
        }

        response = requests.post(url, params=params, headers=headers)
        if response.status_code != 200:
            logging.error(f"Telegram notification failed. Status code: {response.status_code}, Response: {response.text}")
        else:
            logging.info("Telegram notification sent")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Telegram message: {e}")


def get_catalog_items(session, params):
    """Return the catalog items, or an empty list if Vinted returns an error."""
    catalog_url = f"{Config.vinted_url}/api/v2/catalog/items"

    try:
        response = session.get(
            catalog_url,
            params=params,
            headers=headers,
            timeout=timeoutconnection,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error("Vinted catalog request failed: %s", e)
        return []

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        logging.error(
            "Vinted returned a non-JSON response (HTTP %s): %.200s",
            response.status_code,
            response.text,
        )
        return []

    if not isinstance(data, dict):
        logging.error(
            "Unexpected Vinted response type: expected an object, got %s",
            type(data).__name__,
        )
        return []

    items = data.get("items")
    if not isinstance(items, list):
        error_message = data.get("message") or data.get("error") or "unknown error"
        logging.error(
            "Vinted response does not contain a valid 'items' list "
            "(HTTP %s, message: %s, keys: %s)",
            response.status_code,
            error_message,
            ", ".join(sorted(data.keys())),
        )
        return []

    return items


def print_dry_run_item(item_title, item_price, item_url, item_image):
    print(f"Title: {item_title}")
    print(f"Price: {item_price}")
    print(f"URL: {item_url}")
    if item_image:
        print(f"Image: {item_image}")
    print()


def main(dry_run=False):
    # Load the list of previously analyzed items
    load_analyzed_item()

    # Initialize session and obtain session cookies from Vinted
    session = requests.Session()
    try:
        response = session.get(
            Config.vinted_url,
            headers=headers,
            timeout=timeoutconnection,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error("Unable to initialize the Vinted session: %s", e)
        return

    # Loop through each search query defined in Config.py
    for params in Config.queries:
        # Request and validate items returned by the Vinted API
        for item in get_catalog_items(session, params):
            if not isinstance(item, dict):
                logging.warning("Skipping an invalid catalog item: %r", item)
                continue

            item_id = item.get("id")
            item_title = item.get("title")
            required_keyword = params.get('required_keyword')
            if required_keyword and required_keyword.lower() not in item_title.lower():
               continue
            item_url = item.get("url")
            if item_id is None or not item_title or not item_url:
                logging.warning(
                    "Skipping an incomplete catalog item (id: %r)",
                    item_id,
                )
                continue

            item_id = str(item_id)
            item_price_data = item.get("price") or {}
            if not isinstance(item_price_data, dict):
                item_price_data = {}
            item_amount = item_price_data.get("amount")
            item_currency = item_price_data.get("currency_code")
            if item_amount is not None and item_currency:
                item_price = f"{item_amount} {item_currency}"
            else:
                item_price = "N/D"

            item_photo = item.get("photo") or {}
            if not isinstance(item_photo, dict):
                item_photo = {}
            item_image = item_photo.get("full_size_url")

            # Check if the item has already been analyzed to prevent duplicates
            if item_id not in list_analyzed_items:

                if dry_run:
                    print_dry_run_item(
                        item_title,
                        item_price,
                        item_url,
                        item_image,
                    )
                else:
                    # Send e-mail notifications if configured
                    if Config.smtp_username and Config.smtp_server:
                        send_email(item_title, item_price, item_url, item_image)

                    # Send Slack notifications if configured
                    if Config.slack_webhook_url:
                        send_slack_message(
                            item_title,
                            item_price,
                            item_url,
                            item_image,
                        )

                    # Send Telegram notifications if configured
                    if Config.telegram_bot_token and Config.telegram_chat_id:
                        send_telegram_message(
                            item_title,
                            item_price,
                            item_url,
                            item_image,
                        )

                # Mark item as analyzed and save it
                list_analyzed_items.append(item_id)
                save_analyzed_item(item_id)


if __name__ == "__main__":
    args = parse_arguments()
    main(dry_run=args.dry_run)
