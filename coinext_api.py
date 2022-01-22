import hashlib
import hmac
import json
import time
from datetime import datetime

import bcolors as bcolors
import numpy as np
import pandas as pd
import talib
import websocket

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_ID = 40
TRADE_QUANTITY = 0.05
INTERVAL = 60
URL = 'wss://api.coinext.com.br/WSGateway/'

closes = []
next_value = 0
should_buy = 0
should_sell = 0


def create_sha256_signature(key, message):
    encoding = 'latin-1'
    return hmac.new(bytes(key, encoding), msg=bytes(message, encoding), digestmod=hashlib.sha256).hexdigest()


def auth_payload(user_id, api_key, api_secret):
    nonce = int(time.time() * 10000)
    signature = create_sha256_signature(api_secret, '%s%s%s' % (nonce, user_id, api_key))
    result = {
        'APIKey': api_key,
        'Signature': signature,
        'UserId': "%s" % user_id,
        'Nonce': "%s" % nonce
    }
    return result


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
    print('[Sent]: %s' % frame)
    ws.send(json_frame)


def add_closes(closes_rcv):
    for close in closes_rcv:
        closes.append(float(close[4]))


def handle_subscribe_ticker(data):
    add_closes(data)
    pass


def main_logic():
    global should_buy
    global should_sell
    global closes

    if len(closes) == RSI_PERIOD:
        close = closes[-1]
        np_closes = np.array(closes)
        print(np_closes)

        # stochrsi
        fastk, fastd = talib.STOCHRSI(np_closes, timeperiod=RSI_PERIOD, fastk_period=5, fastd_period=3, fastd_matype=0)

        # macd
        ShortEMA = talib.EMA(np_closes, 7)
        LongEMA = talib.EMA(np_closes, 14)
        MACD = ShortEMA - LongEMA
        print(MACD, ShortEMA, LongEMA)
        signal = talib.EMA(MACD, 5)

        # bollinger bands
        upperband, middleband, lowerband = talib.BBANDS(np_closes, timeperiod=RSI_PERIOD, nbdevup=2, nbdevdn=2,
                                                        matype=0)

        upperband_crossed = np.where((np_closes > upperband), 1, 0)
        lowerband_crossed = np.where((np_closes < lowerband), 1, 0)
        last_upperband_crossed = upperband_crossed[-1]
        last_lowerband_crossed = lowerband_crossed[-1]
        last_macd = MACD[-1]
        last_signal = signal[-1]
        last_fastk = fastk[-1]
        last_fastd = fastd[-1]

        # decision trend : BUY OR SELL
        if last_macd > last_signal:
            should_buy += 1
        if last_lowerband_crossed:
            should_buy += 1
        if last_macd < last_signal:
            should_sell += 1
        if last_upperband_crossed:
            should_sell += 1
        if last_fastd > 90 and last_fastk > 90:
            should_buy += 1
        if last_fastd <= 20 and last_fastk <= 20:
            should_sell += 1

        if should_buy > 0:
            print("[ BUY ]", bcolors.OK, should_buy, bcolors.ENDC)
        if should_sell > 0:
            print("[ SELL ]", bcolors.FAIL, should_sell, bcolors.ENDC)

        # STRONG BUY/SELL, MEDIUM BUY/SELL, LOW BUY/SELL TRENDS:
        if should_buy == 2 and should_sell == 0:
            print("{}{}{}".format(bcolors.OK, "[LOW BUY]", bcolors.ENDC, " : ", close))
        elif should_buy == 2:
            print("{}{}{}".format(bcolors.OK, "[MEDIUM BUY ]", bcolors.ENDC, " : ", close))
        if should_sell == 2 and should_buy == 0:
            print("{}{}{}".format(bcolors.FAIL, "[MEDIUM SELL]", bcolors.ENDC, " : ", close))
        elif should_sell == 2:
            print("{}{}{}".format(bcolors.FAIL, "[LOW SELL]", bcolors.ENDC, " : ", close))
        if should_sell == 3:
            print("{}{}{}{}".format(bcolors.BOLD, bcolors.FAIL, "[STRONG SELL]", bcolors.ENDC, " : "))
        if should_buy == 3:
            print("{}{}{}{}".format(bcolors.BOLD, bcolors.OK, "[STRONG BUY]", bcolors.ENDC, " : "))


def handle_ticker_data_update(data):
    add_closes(data)
    main_logic()
    pass


def on_open(ws):
    call_service(ws, 'SubscribeTicker', {
        "OMSId": 1,
        "InstrumentId": TRADE_ID,
        "Interval": INTERVAL,
        "IncludeLastCount": 1
    })
    pass


def on_error(ws, error):
    print('[Message]: Unexpected error: %s' % error)
    pass


def on_close(ws):
    print('[Message]: Connection closed')
    pass


def on_message(ws, data):
    print('[Received]: %s' % data)
    msg = json.loads(data)
    payload_data = json.loads(msg['o'])
    service = msg['n']

    if service == 'SubscribeTicker':
        handle_subscribe_ticker(payload_data)
    elif service == 'TickerDataUpdateEvent':
        handle_ticker_data_update(payload_data)
    else:
        print('Unknown service: %s' % service)


def main():
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(URL,
                                on_error=on_error,
                                on_open=on_open,
                                on_close=on_close,
                                on_message=on_message)
    ws.run_forever()


if __name__ == '__main__':
    main()
