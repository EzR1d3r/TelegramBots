import json
import requests
import time
import os

from .BotLogger import BotLogger
from .Utils import min_ping_host
from lib.SettingsManager import SettingsManager as SM
from .Utils import TOKEN_DEF_PATH

class TelegramBotAPI:
    def __init__ (self, telegram_api_url, token):
        #not all available commands
        #https://core.telegram.org/bots/api#available-methods
        
        self.getMe = f"{telegram_api_url}/bot{token}/getMe"
        self.getUpdates  = f"{telegram_api_url}/bot{token}/getUpdates"
        self.sendMessage = f"{telegram_api_url}/bot{token}/sendMessage"

class BotProcessor:
    def __init__(self, handler, tokenPath = None):
        self.logger = BotLogger()
        self.handler = handler
        
        self.session = requests.Session()
        self.offset = 0

        self.load_settings()
        
        self.token = self.load_token()
        self.api = TelegramBotAPI( telegram_api_url= "https://api.telegram.org", token = self.token )

        # self.process_status = self.get_me() is not False
        self.process_status = True

    def load_settings(self):
        if SM.get( "net", "use_proxy" ):
            proxies = {}
            http_proxys = SM.get( "net", "proxy_list", "http" )
            https_proxys = SM.get( "net", "proxy_list", "https" )

            http, https = min_ping_host( http_proxys ), min_ping_host( https_proxys )

            if http is not None: proxies["http"] = http
            else: self.logger.log_warning( "all http proxys is not available" )
            
            if https is not None: proxies["https"] = https
            else: self.logger.log_warning( "all https proxys is not available" )
            
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

    def __get(self, url, **kwargs):
        try:
            return self.session.get( url, **kwargs)
        except Exception as ex:
            msg = str(ex).replace( self.token, "*****" )
            self.logger.log_error( msg )
            print (msg)

    def __post(self, url, data=None, json=None, **kwargs):
        try:
            return self.session.post( url=url, data=data, json=json, **kwargs)
        except Exception as ex:
            msg = str(ex).replace( self.token, "*****" )
            self.logger.log_error( msg )
            print (msg)

    def get_updates(self, timeout=0):
        params = {'timeout': timeout, 'offset': self.offset}
        resp = self.__get( self.api.getUpdates, params=params)
        updates = []

        try:
            updates = resp.json()['result']
            if len(updates): self.offset = updates[-1]['update_id'] + 1
        except Exception as ex:
            self.logger.log_error(resp)
            self.logger.log_error(ex)

        return updates

    def get_me(self):
        resp = self.__get(self.api.getMe)
        if resp is None: return None

        if resp: #checking for error codes
            updates = resp.json()
            self.logger.log( f"getMe: {updates}" )
            return updates
        else:
            possibly_token_errs = [400, 401, 403, 404, 406, 407]
            msg = f"{resp} Possibly invalid bot token." if (resp.status_code in possibly_token_errs) else f"{resp}"
            self.logger.log_error(msg)
            return False

    def send_message(self, **kwargs):
        resp = self.__post( self.api.sendMessage, data=kwargs )
        return resp

    def handle_update(self, update):

        chat_id  = update['message']['chat']['id']
        response = self.handler.handle(update)

        if len(response):
            self.send_message( chat_id = chat_id, **response )

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
        self.get_updates() #clear updates

        while self.process_status: #MAIN CYCLE
            updates = self.get_updates()
            self.handle_updates( updates )
            time.sleep(1)

        msg = "Process_status set to False. Exit."
        self.logger.log( msg )
        print( f"{msg} Look for the log for details." )