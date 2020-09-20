import sys
import pprint
import logging

import requests

from app import checkout, api
from selenium import webdriver

FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=FORMAT)


API_URI = 'https://api.digitalriver.com/v1/shoppers/me'
API_KEY = '9485fa7b159e42edb08a83bde0d83dia'
# NV_PRODUCT = '5438481700'  # RTX 3080
NV_PRODUCT = '5056110700'  # T-Shirt (Test Item)
SESSION_TOKEN = ''

USERNAME = 'example@email.com'
PASSWORD = 'password123'
CC_CODE = '999'

# WARNING: If set to True the bot will actually make a purchase!!
ACTIVE = False


def get_current_external_ip():
    return requests.get('https://api.ipify.org').text


def main():
    ip_address = get_current_external_ip()

    api_opt = {
        # 'session_token': SESSION_TOKEN,  # Use a fixed session if you wish to pre login
        'ip_address': ip_address,
        'api_uri': API_URI,
        'api_key': API_KEY,
        'check_interval': 30
    }

    dr = api.DRWebAPI(api_opt, retry=True)

    logging.info("Current External IP: " + ip_address)
    logging.info("Using session token: " + dr.get_session_token())

    logging.info("Adding item id " + NV_PRODUCT + " to shopping cart.")
    dr.add_item_to_cart(NV_PRODUCT)

    # Use Web UI to fill out billing and shipping information
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument(f'user-agent={api.USER_AGENT}')
    chrome = webdriver.Chrome(options=options)
    checkout.sign_in(chrome, f'{API_URI}/carts/active/web-checkout?token={dr.get_session_token()}',
                     USERNAME, PASSWORD)
    checkout.add_shipping_payment(chrome, CC_CODE)
    chrome.quit()

    if ACTIVE:
        logging.info("Submitting order.")
        order = dr.submit_cart()
        logging.info("Order placed...")
        logging.info(pprint.pprint(order))

    logging.info("yay!! You bought something!")


if __name__ == '__main__':
    main()
