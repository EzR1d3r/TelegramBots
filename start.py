#!/usr/bin/python3.7

import requests
import time
import datetime
import os
import json

wiki_bot_token = "715818372:AAFPZmjThAvLEHqcjEXDaKwuFRW-PLjmvLs"
proxies =   {
                "http": "192.33.31.130:80",
                "https": "104.248.51.47:8080",
            }

class BotLogger():
    def __init__(self, folderPath = ".logs"):
        self.path = folderPath

        if not os.path.exists(folderPath):
            os.makedirs(folderPath)

    def log(self, text, ext=".log"):
        date = datetime.datetime.now()

        sDateTime = date.strftime('%d_%b_%Y_%H:%M:%S')
        fPath = f"{self.path}/{ date.strftime('%d_%b_%Y') }{ext}"

        with open(fPath, 'a') as file:
            file.write( f"{sDateTime}:\n{text}\n\n" )

    def log_error(self, text):
        text = f"ERROR:\n{text}"
        self.log(text, ext=".err_log")


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
        params = {'timeout': timeout, 'offset': self.offset}
        query  = f"{self.api_url}getUpdates"
        resp = self.session.get(query, params=params)
        result_json = resp.json()['result']
        if len(result_json): self.offset = result_json[-1]['update_id'] + 1
        return result_json

    def smart_message(self, **kwargs):
        resp = self.session.post( f"{self.api_url}sendMessage", kwargs )
        return resp

    def handle_update(self, update):
        text     = update['message']['text']
        chat_id  = update['message']['chat']['id']
        if text == "ex": raise Exception('Test exception')

        if text.startswith('/'):
            response = self.handler.exec_cmd( text, update )
        else:
            response = self.handler.exec_text( text, update )

        if len(response):
            self.smart_message( chat_id = chat_id, **response )

        print(update)

        self.logger.log( str(update) )
        self.logger.log( f"Response: {str(response)}" ) 

    def handle_updates(self, updates):
        for up in updates:
            try:
                self.handle_update(up)
            except Exception as ex:
                self.logger.log_error( f"{ex}:\n {str(up)}" )
                print( f"Exception {ex}")

    def process(self):
        while True:
            updates = self.get_updates()
            self.handle_updates( updates )


class WikiBot:
    def __init__(self):

    #list of commands (have to be sent to FatherBot, look /setcommands)
    # help - Description
    # language - Choose the language zone

        self.commands = {
                            "/start"    : self.cmd_start,
                            "/help"     : self.cmd_help,
                            "/language" : self.cmd_language,
                        }

        self.support_langs = ["ru", "en"]
        self.settings = { "default":{"language":"ru"} }
        self.update = None

    def exec_cmd(self, cmd, update):
        self.update = update

        cmd = cmd.split(":")
        func = self.commands.get( cmd[0] )
        val = cmd[1] if len(cmd) > 1 else ""

        result = self.unknown(cmd) if func is None else func(val)
        return result

    def exec_text(self, text, update):
        self.update = update
        return self.find(text)

    def cmd_start(self, val):
        return {"text":"Greetings! I am WikiBot.\nJust tell me what do you want to find."}

    def cmd_help(self, val):
        return {"text":"WikiBot for searching articles direct from Telegram"}

    def cmd_language(self, val):
        if val == "":
            keyboard_list = []
            for lang in self.support_langs:
                keyboard_list.append( {"text": "/language:" + lang} )

            return { "text":         "Choose the language zone.\nYou may set manually by /language:my_lang",
                     "reply_markup": json.dumps({   "keyboard": [keyboard_list],
                                                    "resize_keyboard":True })
                    }
        else:
            chat_id  = self.update['message']['chat']['id']
            self.update_setting(chat_id, "language", val)

            return { 
                     "text":         f"Choosed language: {val}",
                     "reply_markup": json.dumps({ "remove_keyboard": True })
                    }

    def update_setting(self, chat_id, setting, value):
        usr_st = self.settings.get(chat_id)
        if usr_st is not None:
            usr_st[setting] = value
        else:
            usr_st = {setting:value}
        
        self.settings[chat_id] = usr_st

    def get_setting(self, chat_id, setting):
        try:
            return self.settings[chat_id][setting]
        except:
            return None

    def find(self, text):
        chat_id  = self.update['message']['chat']['id']
        lang = self.get_setting(chat_id, "language")
        try:
            lang = self.update['message']['from']['language_code'] if lang is None else lang
        except:
            lang = self.get_setting("default", "language")

        S = requests.Session()
        URL = f"https://{lang}.wikipedia.org/w/api.php"
        SEARCHPAGE = text
        PARAMS = {
                    'action':"query",
                    'list':"search",
                    'srsearch': SEARCHPAGE,
                    'format':"json",
                    'srprop':'redirecttitle',
                }

        R = S.get(url=URL, params=PARAMS)
        DATA = R.json()
        # print(DATA)
        search_result =  DATA['query']['search']

        if not len(search_result):
            return {"text":f"Cant find something for {text} in wiki..."}
        
        title = search_result[0].get('title')
        title = title.replace(' ', '_')
        return {"text":f"https://{lang}.wikipedia.org/wiki/{title}"}

    def unknown(self, cmd):
        return {"text":f"Unknown command {cmd}"}

def main():
    handler = WikiBot()
    processor = BotProcessor(wiki_bot_token, handler)
    processor.process()

if __name__ == '__main__':  
    try:
        main()
    except KeyboardInterrupt:
        exit()