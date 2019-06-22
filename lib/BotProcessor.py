import json
import requests
import time
import os

from .BotLogger import BotLogger
from .Utils import min_ping_host
from lib.SettingsManager import SettingsManager as SM
from .Utils import projectDir, MAIN_FNAME, TOKEN_DIR

TOKEN_DEF_PATH = os.path.join( projectDir(), TOKEN_DIR, f"{MAIN_FNAME}.token" )

class BotProcessor:
    def __init__(self, handler, tokenPath = None):
        self.logger = BotLogger()
        self.handler = handler
        
        self.session = requests.Session()
        self.offset = 0

        self.load_settings()
        
        self.token = self.load_token()
        self.api_url = f"https://api.telegram.org/bot{self.token}/"

        self.get_updates() #clear updates

    def load_settings(self):
        if SM.get( "net", "use_proxy" ):
            proxies = {}
            http_proxys = SM.get( "net", "proxy_list", "http" )
            https_proxys = SM.get( "net", "proxy_list", "https" )

            http, https = min_ping_host( http_proxys ), min_ping_host( https_proxys )

            if http is not None: proxies["http"] = http
            else: self.logger.log_error( "WARNING: all http proxys is not available" )
            
            if https is not None: proxies["https"] = https
            else: self.logger.log_error( "WARNING: all https proxys is not available" )

            self.session.proxies = proxies

    def load_token(self, tokenPath = None):
        if tokenPath is None: tokenPath = TOKEN_DEF_PATH

        try:
            with open(tokenPath, 'r') as file:
                t = file.read()
            return t
        except:
            self.logger.log_error(f"cant read token-file: {tokenPath}")
            raise

    def get_updates(self, timeout=0):
        query  = f"{self.api_url}getUpdates" #TODO: const string
        params = {'timeout': timeout, 'offset': self.offset}
        resp = self.session.get(query, params=params)
        updates = resp.json()['result']
        if len(updates): self.offset = updates[-1]['update_id'] + 1
        return updates

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