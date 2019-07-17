import json
import requests
import time
import os

from .BotLogger import BotLogger
from .Utils import min_ping_host
from lib.SettingsManager import SM
from .Utils import TOKEN_DEF_PATH

req_ex = requests.exceptions


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

        self.process_status = self.get_me() is not False

    def load_settings(self):
        if SM.https_proxy_it is not None:
            https_proxys = []
            while True:
                isLast, https = next(SM.https_proxy_it)
                https_proxys.append( https )
                if isLast: break
            
            https = min_ping_host( https_proxys, timeout=0.2 ) # remove ping???

            if https is not None: self.set_proxy( https = https )
            else: self.logger.log_warning( "[ All https proxys is not available ]" )

    def set_proxy(self, http = None, https = None):
        proxies = {}
        if http is not None: proxies["http"] = http
        if https is not None: proxies["https"] = https
        self.session.proxies = proxies
 
    def load_token(self, tokenPath = None):
        if tokenPath is None: tokenPath = TOKEN_DEF_PATH

        try:
            with open(tokenPath, 'r') as file:
                t = file.read()
            return t
        except:
            self.logger.log_error(f"[ Cant read token-file: {tokenPath} ]")
            raise

    def __get(self, url, **kwargs):
        
        resp = None
        
        try:
            resp = self.session.get( url, **kwargs) #TODO pick SSLError (msg: perhaps need proxy)
            resp.raise_for_status()

        except req_ex.SSLError as ex:
            msg = str(ex).replace( self.token, "*****" )
            msg += "\n[ Make sure the telegram was not blocked by your provider. Use proxy then. ]"
        
        except (req_ex.ConnectTimeout, req_ex.ProxyError ) as ex:
            msg = str(ex).replace( self.token, "*****" )
            if SM.https_proxy_it is not None:
                isLast, https = next( SM.https_proxy_it )
                self.set_proxy( https = https )
                if isLast:
                    msg += f"\n[ Using last proxy in the proxy list { https }. ]"
                else:
                    broken_https = self.session.proxies["https"]
                    msg += f"\n[ Problem with proxy { broken_https }. Trying to switch https proxy from on { https }. ]"

        except req_ex.HTTPError as ex:
            msg = str(ex).replace( self.token, "*****" )
            possibly_token_errs = [400, 401, 403, 404, 406, 407]

            if resp.status_code in possibly_token_errs:
                msg += "\n[ Possibly invalid bot token. ]"
                resp = False
                
        except Exception as ex:
            msg = str(ex).replace( self.token, "*****" )
        
        if not resp:
            self.logger.log_error( msg )
            print (msg)
        
        return resp


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
        updates = None

        try:
            updates = resp.json()['result']
            if len(updates): self.offset = updates[-1]['update_id'] + 1
        except Exception as ex:
            self.logger.log_error(resp)
            self.logger.log_error(ex)

        return updates

    def get_me(self):
        resp = self.__get(self.api.getMe)

        if not resp: return resp # None or False

        updates = resp.json()
        self.logger.log( f"getMe: {updates}" )
        return updates

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
        skip_passed_upd = SM.get( "common", "skip_passed_upd")
        while skip_passed_upd and self.get_updates() is None:
            pass #clear updates

        while self.process_status: #MAIN CYCLE
            updates = self.get_updates()
            if updates is not None: self.handle_updates( updates )
            time.sleep(1)

        msg = "Process_status set to False. Exit."
        self.logger.log( msg )
        print( f"{msg} Look for the log for details." )