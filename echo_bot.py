#!/usr/bin/python3.7
#https://core.telegram.org/bots/api

from bots.EchoBot import EchoBot
from lib.BotProcessor import BotProcessor
from flask import Flask, request

app = Flask( __name__ )
# app.debug = False
resp = "<h1>Hello</h1>"
context = ('domain.pem', 'domain.key')

# openssl req -newkey rsa:2048 -sha256 -nodes -keyout YOURPRIVATE.key -x509 -days 365 -out YOURPUBLIC.pem
# curl --proxy 104.248.51.47:8080 -F "url=" -F "certificate=@domain.pem" https://api.telegram.org/bot***/setWebhook

# <html>
# <body>

# <form action="https://api.telegram.org/bot<BOT_TOCKEN>/setwebhook" method="post" enctype="multipart/form-data">
#     Select Certificate to upload:
#     <input type="file" name="certificate" id="fileToUpload">
# 	URL: <input type="text" name="url"  value="https://<YOURWEBSITE>/<YOUR_PHP_URL>"><br>
#     <input type="submit" value="Upload Certificate" name="submit">
# </form>

# </body>
# </html>

@app.route("/", methods=["POST", "GET"])
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
