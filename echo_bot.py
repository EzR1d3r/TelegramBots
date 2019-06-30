#!/usr/bin/python3.7
#https://core.telegram.org/bots/api

from bots.EchoBot import EchoBot
from lib.BotProcessor import BotProcessor
from flask import Flask, request
# from flask_sslify import SSLify

from OpenSSL import SSL
context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('yourserver.key')
context.use_certificate_file('yourserver.crt')

app = Flask( __name__ )
# sslify = SSLify(app)

# app.debug = False
resp = "<h1>Hello</h1>"

@app.route("/qwerty", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        r = request.get_json()
        print(r, type(r))
    return resp


def main():
    app.run(host="0.0.0.0", port="443", ssl_context=context)
    # handler = EchoBot()
    # processor = BotProcessor(handler)
    # processor.process()

if __name__ == '__main__':  
    try:
        main()
    except KeyboardInterrupt:
        exit()