#!/usr/bin/python3.7

import requests
import time
import datetime
import os

wiki_bot_token = "715818372:AAFPZmjThAvLEHqcjEXDaKwuFRW-PLjmvLs"
proxies =   {
                "http": "192.33.31.130:80",
                "https": "104.248.51.47:8080",
            }

#list of commands (have to be sent to FatherBot for current bot)
# help - Description
# find - Find the article in wikipedia.org

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

    def get_updates(self, timeout=0):
        params = {'timeout': timeout, 'offset': self.offset}
        query  = f"{self.api_url}getUpdates"
        resp = self.session.get(query, params=params)
        result_json = resp.json()['result']
        if len(result_json): self.offset = result_json[-1]['update_id'] + 1
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
        resp = self.session.post( f"{self.api_url}sendMessage", params )
        return resp

    def handle_update(self, update):
        text     = update['message']['text']
        chat_id  = update['message']['chat']['id']
        if text == "ex": raise Exception('Test exception')

        if text.startswith('/'):
            l = text.split(' ')
            cmd = l[0]
            text = " ".join( l[1:] )

            response_txt = self.handler.exec_cmd( cmd, text )
        else:
            response_txt = self.handler.exec_text( text )


        if response_txt != "":
            self.send_message( chat_id, response_txt )

        self.logger.log( str(update) )
        self.logger.log( f"Response: {response_txt}" ) 

    def handle_updates(self, updates):
        for up in updates:
            try:
                self.handle_update(up)
            except Exception as ex:
                self.logger.log_error( f"{ex}:\n {str(up)}" )

    def process(self):
        while True:
            try:
                updates = self.get_updates()
                self.handle_updates( updates )
            except Exception as ex:
                self.logger.log_error( ex )


class WikiBot:
    def __init__(self):
        self.commands = {
                            "/help" : self.help,
                            "/find" : self.find,
                        }

    def exec_cmd(self, cmd, text):
        func = self.commands.get( cmd )
        result = self.unknown(cmd) if func is None else func(text)

        return result

    def exec_text(self, text):
        return f"https://ru.wikipedia.org/wiki/{text}"

    def help(self, text):
        return "WikiBot for searching articles direct from Telegram"

    def find(self, text):
        return f"https://ru.wikipedia.org/wiki/{text}"
        # return f"Searching for {text} in wiki..."

    def unknown(self, cmd):
        return f"Unknown command {cmd}"


def main():

    handler = WikiBot()
    processor = BotProcessor(wiki_bot_token, handler)
    processor.process()


if __name__ == '__main__':  
    try:
        main()
    except KeyboardInterrupt:
        exit()