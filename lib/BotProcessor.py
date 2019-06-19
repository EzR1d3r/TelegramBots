import json
import requests
import time

from .BotLogger import BotLogger

proxies =   {
                "http": "192.33.31.130:80",
                "https": "104.248.51.47:8080",
            }

class BotProcessor:
    def __init__(self, token, handler):
        self.token = token
        self.handler = handler
        self.logger = BotLogger()
        self.api_url = f"https://api.telegram.org/bot{token}/"

        self.session = requests.Session()
        self.session.proxies = proxies
        self.offset = 0

        self.get_updates() #clear updates

    def get_updates(self, timeout=0):
        query  = f"{self.api_url}getUpdates"
        params = {'timeout': timeout, 'offset': self.offset}
        resp = self.session.get(query, params=params)
        result_json = resp.json()['result']
        if len(result_json): self.offset = result_json[-1]['update_id'] + 1
        return result_json

    def smart_message(self, **kwargs):
        resp = self.session.post( f"{self.api_url}sendMessage", kwargs )
        return resp

    def handle_update(self, update):

        chat_id  = update['message']['chat']['id']
        response = self.handler.handle(update)

        if len(response):
            self.smart_message( chat_id = chat_id, **response )

        self.logger.log( str(update) )
        self.logger.log( f"Response: {str(response)}" ) 

    def handle_updates(self, updates):
        for upd in updates:
            try:
                self.handle_update(upd)
            except Exception as ex:
                self.logger.log_error( f"{ex}:\n {str(upd)}" )
                print( f"Exception {type(ex)} {ex}")

    def process(self):
        while True: #MAIN CYCLE
            updates = self.get_updates()
            self.handle_updates( updates )
            time.sleep(1)