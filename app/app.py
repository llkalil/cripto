import hashlib
import hmac
import json
import time
from datetime import datetime

import numpy as np
import talib
import websocket
from matplotlib import pyplot as plt

import messages
from strategy import Strategy

data = []
STRATEGY_PERIOD = 14
TRADE_ID = 40  # shib
TRADE_QUANTITY = 100000  # SHIBS
INTERVAL = 60
STRATEGY = 'RSI'
INDICATOR = "7030"

next_value = 0
is_bought = False  # SEMPRE AJUSTAR
auth_data = {}


def call_service(ws, service_name, data, level=0):
    global next_value

    frame = {
        'm': level,
        'i': next_value,
        'n': service_name,
        'o': json.dumps(data)
    }
    next_value += 2
    json_frame = json.dumps(frame)
    messages.warning_msg('Sent: %s' % frame)
    ws.send(json_frame)


def get_keys():
    f = open('secret.json')
    keys = json.load(f)
    return keys["APIKey"], keys["APISecret"]
    pass


def authenticate(ws):
    key, secret = get_keys()
    payload = auth_payload(
        214404,
        api_key=key,
        api_secret=secret)  # prod
    call_service(ws, 'AuthenticateUser', payload)


def create_sha256_signature(key, message):
    encoding = 'latin-1'
    return hmac.new(bytes(key, encoding), msg=bytes(message, encoding), digestmod=hashlib.sha256).hexdigest()


def auth_payload(user_id, api_key, api_secret):
    nonce = int(time.time() * 10700)
    signature = create_sha256_signature(api_secret, '%s%s%s' % (nonce, user_id, api_key))

    result = {
        'APIKey': api_key,
        'Signature': signature,
        'UserId': "%s" % user_id,
        'Nonce': "%s" % nonce
    }
    return result


def on_open(ws):
    authenticate(ws)
    pass


def subscribe_ticker(ws):
    call_service(ws, 'SubscribeTicker', {
        "OMSId": 1,
        "InstrumentId": TRADE_ID,
        "Interval": INTERVAL,
        "IncludeLastCount": 400
    })


def on_error(ws, error):
    messages.error_msg(error)
    pass


def on_close(ws):
    messages.warning_msg("Connection closed")
    pass


def add_data(data_received):
    for close in data_received:
        data.append(close)


def handle_subscribe_ticker(data_received):
    add_data(data_received)


def get_quantity(ws):
    call_service(ws, 'GetAccountPositions', {
        "OMSId": 1,
        "AccountId": auth_data["User"]["AccountId"]
    })
    pass


def save_to_cashbook(action):
    with open('cashbook.csv', 'a') as fd:
        data_csv = [str(x) for x in data[-1]]
        data_csv.append(action)
        fd.write(','.join(data_csv) + '\n')
    pass


def execute_order(ws, action):
    save_to_cashbook(action)
    if auth_data["Authenticated"]:
        call_service(ws, 'SendOrder', {
            "AccountId": auth_data["User"]["AccountId"],
            "Quantity": TRADE_QUANTITY,
            "DisplayQuantity": 0,
            "UseDisplayQuantity": False,
            "OrderType": 1,
            "InstrumentId": TRADE_ID,
            "TrailingAmount": 1.0,
            "Side": (0 if action == "BUY" else 1),
            "TimeInForce": 1,
            "OMSId": 1
        })


def process_data(ws, data_payload):
    global is_bought

    closes = [float(entry[4]) for entry in data]

    if len(closes) > STRATEGY_PERIOD:
        strategy = Strategy(STRATEGY, INDICATOR, str(TRADE_ID), STRATEGY_PERIOD, data)
        buyOrSell = strategy.buyOrSell()
        if buyOrSell == "BUY":
            if is_bought:
                messages.warning_msg("DO NOTHING")
            else:
                is_bought = True
                messages.success_msg(f"BUY - {closes[-1]}")
                execute_order(ws, "BUY")
        elif buyOrSell == "SELL":
            if is_bought:
                is_bought = False
                messages.error_msg(f"SELL {closes[-1]}")
                execute_order(ws, "SELL")
            else:
                messages.warning_msg("DO NOTHING")

    else:
        messages.success_msg(f'Waiting for data [{len(closes)}/{STRATEGY_PERIOD}]')
    pass


def handle_ticker_data_update(ws, data):
    add_data(data)
    process_data(ws, data)


def on_message(ws, data):
    global auth_data
    messages.success_msg('Received event')
    msg = json.loads(data)
    payload_data = json.loads(msg['o'])
    service = msg['n']

    if service == 'AuthenticateUser':
        auth_data = payload_data
        print(auth_data)
        subscribe_ticker(ws)
    elif service == 'SendOrder':
        messages.success_msg("ORDER IS SUCCESS")
    elif service == 'SubscribeTicker':
        handle_subscribe_ticker(payload_data)
    elif service == 'TickerDataUpdateEvent':
        handle_ticker_data_update(ws, payload_data)
    else:
        messages.error_msg('Unknown service: %s' % service)


def initiate_websocket():
    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        'wss://api.coinext.com.br/WSGateway/',
        on_error=on_error,
        on_open=on_open,
        on_close=on_close,
        on_message=on_message
    )
    ws.run_forever()


def main():
    initiate_websocket()


if __name__ == "__main__":
    main()
