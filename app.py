import json
import websocket
import time
import hmac
import hashlib
import base64
import binascii
import logging
import numpy as np
import talib

logging.basicConfig()

nextIvalue = 0

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

TRADE_ID = 40
TRADE_QUANTITY = 0.05

INTERVAL = 60

closes = []
in_position = False


def call_service(ws, service_name, data, level=0):
    global nextIvalue

    frame = {
        'm': level,
        'i': nextIvalue,
        'n': service_name,
        'o': json.dumps(data)
    }
    nextIvalue += 2
    str = json.dumps(frame)
    print(' - SND: ', str)
    ws.send(str)


def on_error(ws, error):
    print(error)


def show_info(ws, data):
    # print(' - RCV: ', data)
    ws.close()


def test_service(ws, data):
    global nextIvalue
    print(' - RCV: ', data)
    process_data(data, ws)


def process_data(data, ws):
    msg = json.loads(data)
    payload_data = json.loads(msg['o'])
    service = msg['n']

    if service == 'AuthenticateUser':
        if payload_data['Authenticated']:
            call_service(ws, 'SubscribeTicker', {
                "OMSId": 1,
                "InstrumentId": TRADE_ID,
                "Interval": INTERVAL,
                "IncludeLastCount": 1
            })
        else:

            on_error(ws, "Unauthenticated")

    elif service == 'SubscribeTicker':

        save_to_document(payload_data)
        process_numbers(payload_data)

    elif service == 'TickerDataUpdateEvent':

        save_to_document(payload_data)
        process_numbers(payload_data)

    else:
        on_error(ws, "Unknown service")
        ws.close()


def exec_sell(payload_data):
    with open('cashbook.csv', 'a') as fd:
        data = [str(x) for x in payload_data[0]]
        data.append("Sell")
        fd.write(','.join(data) + '\n')
    return True


def exec_buy(payload_data):
    with open('cashbook.csv', 'a') as fd:
        data = [str(x) for x in payload_data[0]]
        data.append("Buy")
        fd.write(','.join(data) + '\n')
    return True


def process_numbers(payload_data):
    global in_position
    print('===============Received Event===============')
    closes.append(float(payload_data[0][4]))
    # print(closes)

    if len(closes) > RSI_PERIOD:
        print('closes:')
        print(closes)
        np_closes = np.array(closes)
        rsi = talib.RSI(np_closes, RSI_PERIOD)

        print("all rsis calculated so far")
        print(rsi)
        last_rsi = rsi[-1]
        print("the current rsi is {}".format(last_rsi))

        if last_rsi > RSI_OVERBOUGHT:
            if in_position:
                print("Overbought! Sell! Sell! Sell!")
                # put binance sell logic here
                order_succeeded = exec_sell(payload_data)

                if order_succeeded:
                    in_position = False
            else:
                print("It is overbought, but we don't own any. Nothing to do.")

        if last_rsi < RSI_OVERSOLD:
            if in_position:
                print("It is oversold, but you already own it, nothing to do.")
            else:
                print("Oversold! Buy! Buy! Buy!")
                # put binance buy order logic here
                order_succeeded = exec_buy(payload_data)
                # order_succeeded = True
                if order_succeeded:
                    in_position = True


def save_to_document(payload_data):
    # print(payload_data[0])
    with open('result.csv', 'a') as fd:
        fd.write(','.join([str(x) for x in payload_data[0]]) + '\n')


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


def start_talking(ws):
    ws.on_message = test_service

    payload = auth_payload(
        214404,
        api_key='1507f9ef578f47330118dbbab5212833',
        api_secret='fc80edb9736fc3985893cc31e03e3ce0')  # prod

    call_service(ws, 'AuthenticateUser', payload)


def on_open(ws):
    print('opened connection')
    start_talking(ws)


def on_close(ws):
    print('closed connection')


def main():
    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp('wss://api.coinext.com.br/WSGateway/',
                                on_error=on_error,
                                on_open=on_open,
                                on_close=on_close)
    ws.run_forever()


if __name__ == "__main__":
    main()
