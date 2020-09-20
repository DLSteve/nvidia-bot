import json
import time

import requests

# We pretend to be chrome
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko)' \
             ' Chrome/85.0.4183.102 Safari/537.36'

COMMON_HEADERS = {
    'user-agent': USER_AGENT,
    'Accept': 'application/json'
}


class CannotAddItemError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(self.message)


class ItemOutOfStockError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(self.message)


class DRWebAPI:
    def __init__(self, options, retry=False, retry_interval=30, max_retry=15):
        self.options = options
        self.retry = retry
        self.retry_attempts = 0
        self.retry_interval = retry_interval
        self.max_retry = max_retry

        if not options.get('session_token'):
            self.options['session_token'] = self._get_session_token()

    # API call for a "Guest" token for checkout. From what I can tell
    # the token is based on IP and possibly user agent. Token lasts 24
    # hours before needing to be renewed.
    def _get_session_token(self):
        params = {'format': 'json', 'apiKey': self.options['api_key'], 'currency': 'USD'}
        headers = COMMON_HEADERS
        r = requests.get('https://store.nvidia.com/store/nvidia/SessionToken', params=params, headers=headers)
        j = r.json()
        return j.get('access_token')

    def get_session_token(self):
        return self.options['session_token']

    def _add_item_to_cart(self, nv_product_id):
        params = {'token': self.options['session_token']}
        headers = {'Content-Type': 'application/json', **COMMON_HEADERS}
        payload = {
            'cart': {
                'ipAddress': self.options['ip_address'],
                'lineItems': {
                    'lineItem': [
                        {
                            'quantity': '1',
                            'product': {
                                'id': nv_product_id
                            }
                        }
                    ]
                },
                'termsOfSalesAcceptance': 'true'
            }
        }

        r = requests.post(self.options['api_uri'] + '/carts/active', params=params, headers=headers,
                          data=json.dumps(payload))

        if not r.status_code == requests.codes.ok:
            if r.status_code == requests.codes.conflict:
                resp = r.json()

                try:
                    code = resp.get('errors').get('error')[0].get('code')
                    msg = resp.get('errors').get('error')[0].get('description')
                except (AttributeError, IndexError):
                    code = 'unknown-error'
                    msg = 'Received unknown 409 error'

                if code == 'inventory-unavailable-error':
                    raise ItemOutOfStockError(code, msg)
                raise CannotAddItemError(code, msg)
            else:
                r.raise_for_status()

        return r.json()

    def add_item_to_cart(self, nv_product_id):
        self.retry_attempts = 0
        while True:
            try:
                return self._add_item_to_cart(nv_product_id)
            except ItemOutOfStockError:
                print("Item not available yet, waiting to try again...")
                time.sleep(self.options['check_interval'])
                continue
            except CannotAddItemError as e:
                print(e)
                if self.retry and (self.retry_attempts < self.max_retry or self.max_retry == -1):
                    print("Error occurred while adding product, retrying...")
                    self.retry_attempts = self.retry_attempts + 1
                    time.sleep(self.retry_interval)
                    continue
                else:
                    raise e  # Halt if unknown error happens

    def _submit_cart(self):
        params = {'token': self.options['session_token']}
        headers = {'Content-Type': 'application/json', **COMMON_HEADERS}
        payload = {
            'cart': {
                'ipAddress': self.options['ip_address'],
                'termsOfSalesAcceptance': 'true'
            }
        }

        r = requests.post(self.options['api_uri'] + '/carts/active/submit-cart', params=params, headers=headers,
                          data=json.dumps(payload))

        if not r.status_code == requests.codes.ok:
            r.raise_for_status()

        return r.json()

    def submit_cart(self):
        self.retry_attempts = 0
        while True:
            try:
                return self._submit_cart()
            except requests.HTTPError as e:
                print(e)
                if self.retry and (self.retry_attempts < self.max_retry or self.max_retry == -1):
                    print("Error occurred while checking out, retrying...")
                    self.retry_attempts = self.retry_attempts + 1
                    time.sleep(self.retry_interval)
                    continue
                else:
                    raise e  # Halt if unknown error happens
