"""
service-A

This script tracks the current Bitcoin price in a specified currency (default: USD).
It logs each price retrieval and reports an average.

"""

import requests
import time
import os
from datetime import datetime

# ====== Configuration ======
CURRENCY = "usd"          # Type of currency
INTERVAL = 60             # Interval in seconds between value retrieval (60 = 1 minute)
AVG_INTERVAL = 600        # Interval in seconds between average value retrieval (600 = 10 minute)

COINGECKO_API_URL = f"https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies={CURRENCY}"
API_KEY = os.environ.get("COINGECKO_API_KEY")



def get_timestamp():
    """
    Returns the current date and time.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(message):
    """
    Prints a timestamped log message.
    """
    print(f"[{get_timestamp()}] {message}")


def update_liveness():
    """
    Create a tmp file for readiness and liveliness probe check (for kubernetes).
    """
    try:
        with open("/tmp/alive", "w") as f:
            f.write(str(time.time()))
    except Exception as e:
        log(f"Failed to update liveness file: {e}")


def fetch_bitcoin_price():
    """
    Returns the bitcoin price from an API.
    """
    headers = {}
    if API_KEY:
        headers["x-cg-pro-api-key"] = API_KEY

    try:
        response = requests.get(COINGECKO_API_URL, headers=headers, timeout=10)
        response.raise_for_status() # raise an exception for any HTTP error codes
        data = response.json()
        return data["bitcoin"][CURRENCY]
    except (requests.RequestException, KeyError, ValueError) as e:
        log(f"Error fetching price: {e}")
        return None


def print_average(prices):
    """
    Calculates and logs the average price from a list of prices.
    """
    if prices:
        avg = sum(prices) / len(prices)
        log(f"Average Bitcoin price over last {AVG_INTERVAL // INTERVAL} minutes: ${avg:.2f}")
    else:
        log("No prices collected during interval.")


def main():
    log("Starting service-A")
    
    # Calculate how many price checks should occur before printing the average.
    # For example, with INTERVAL = 60s and AVG_INTERVAL = 600s, this will collect 10 prices (1 per minute for 10 minutes).
    num_cycles = AVG_INTERVAL // INTERVAL

    while True:
        # Store the last prices
        prices = []

        for i in range(num_cycles):
            price = fetch_bitcoin_price()
            if price is not None:
                prices.append(price)
                log(f"Bitcoin price in {CURRENCY.upper()}: ${price:.2f}")
                update_liveness()
            # Print the average in the last cycle    
            if i == num_cycles - 1:
                print_average(prices)

            # Wait between each value retrived    
            time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
