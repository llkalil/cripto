import json
from datetime import datetime

import numpy as np
import talib
import websocket
from matplotlib import pyplot as plt

import messages
from strategy import Strategy

data = []
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_ID = 40  # shib
TRADE_QUANTITY = 0.05
INTERVAL = 60

next_value = 0
is_bought = False


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


def on_open(ws):
    call_service(ws, 'SubscribeTicker', {
        "OMSId": 1,
        "InstrumentId": TRADE_ID,
        "Interval": INTERVAL,
        "IncludeLastCount": 400
    })
    pass


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


def exec_buy(payload_data):
    with open('cashbook.csv', 'a') as fd:
        data_csv = [str(x) for x in payload_data[0]]
        data_csv.append("Buy")
        fd.write(','.join(data_csv) + '\n')
    return True


def exec_sell(payload_data):
    with open('cashbook.csv', 'a') as fd:
        data_csv = [str(x) for x in payload_data[0]]
        data_csv.append("Sell")
        fd.write(','.join(data_csv) + '\n')
    return True


def process_data(data_payload):
    global is_bought

    open_time = [int(entry[0]) for entry in data]
    closes = [float(entry[4]) for entry in data]

    if len(closes) > RSI_PERIOD:
        strategy = Strategy('RSI', '7030', "SHIBBRL", RSI_PERIOD, data)
        buyOrSell = strategy.buyOrSell()
        if buyOrSell == "BUY":
            if is_bought:
                messages.warning_msg("DO NOTHING")
            else:
                is_bought = True
                messages.success_msg(f"BUY - {closes[-1]}")
        elif buyOrSell == "SELL":
            if is_bought:
                is_bought = False
                messages.error_msg(f"SELL {closes[-1]}")
            else:
                messages.warning_msg("DO NOTHING")

    else:
        messages.success_msg(f'Waiting for data [{len(closes)}/{RSI_PERIOD}]')
    pass


def handle_ticker_data_update(data):
    add_data(data)
    process_data(data)


def on_message(ws, data):
    messages.success_msg('Received event')
    msg = json.loads(data)
    payload_data = json.loads(msg['o'])
    service = msg['n']

    if service == 'SubscribeTicker':
        handle_subscribe_ticker(payload_data)
    elif service == 'TickerDataUpdateEvent':
        handle_ticker_data_update(payload_data)
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
