#!/usr/bin/python3.7
#https://core.telegram.org/bots/api

from bots.EchoBot import EchoBot
from lib.BotProcessor import BotProcessor
from flask import Flask, request

app = Flask( __name__ )
resp = "<h1>Hello</h1>"

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        r = request.get_json()
        print(r, type(r))
    return resp


def main():
    app.run()
    # handler = EchoBot()
    # processor = BotProcessor(handler)
    # processor.process()

if __name__ == '__main__':  
    try:
        main()
    except KeyboardInterrupt:
        exit()