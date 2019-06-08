import json
import requests

from lib.SettingsManager import SettingsManager as SM

class WikiBot:
    def __init__(self):

        #list of commands (have to be sent to FatherBot, look /setcommands)
        #help - Description
        #language - Choose the language zone

        self.commands = {
                            "/start"    : self.cmd_start,
                            "/help"     : self.cmd_help,
                            "/language" : self.cmd_language,
                        }

        self.support_langs = ["ru", "en"]
        self.current_update = None
        SM.load()

    def handle(self, update):
        self.current_update = update
        text = update['message']['text']
        return self.handele_cmd(text) if text.startswith('/') else self.handle_text(text)

    def handele_cmd(self, cmd):
        cmd = cmd.split(":")
        cmd_func = self.commands.get( cmd[0] )
        val = cmd[1] if len(cmd) > 1 else ""

        result = self.unknown(cmd) if cmd_func is None else cmd_func(val)
        return result

    def handle_text(self, text):
        return self.find(text)

    def cmd_start(self, val):
        return {"text":"Greetings! I am WikiBot.\nJust tell me what do you want to find."}

    def cmd_help(self, val):
        return {"text":"WikiBot for searching articles direct from Telegram"}

    def cmd_language(self, val):
        if val == "":
            btn_list = [ [ {"text": "/language:" + lang} for lang in self.support_langs ] ]
            keyboard = {"keyboard": btn_list, "resize_keyboard": True }
            text = "Choose the language zone.\nYou may set manually by /language:my_lang"
            
            return { "text":text, "reply_markup": json.dumps( keyboard ) }
        else:
            chat_id  = self.current_update['message']['chat']['id']
            SM.update_usr_setting(chat_id, "language", val)
            reply_markup = json.dumps({ "remove_keyboard": True })

            return { "text":f"Choosed language: {val}", "reply_markup": reply_markup}

    def find(self, text):
        chat_id  = self.current_update['message']['chat']['id']
        alt_val_expr = lambda : self.current_update['message']['from']['language_code']
        lang = SM.get_usr_setting(chat_id, "language", alt_val_expr=alt_val_expr )

        session = requests.Session()
        URL = f"https://{lang}.wikipedia.org/w/api.php"
        SEARCH_TEXT = text
        PARAMS = {
                    'action':"query",
                    'list':"search",
                    'srsearch': SEARCH_TEXT,
                    'format':"json",
                    'srprop':'redirecttitle',
                }

        response = session.get(url=URL, params=PARAMS)
        search_result =  response.json()['query']['search']

        if not len(search_result):
            return {"text":f"Cant find something for {text} in wiki...."}
        
        title = search_result[0].get('title')
        title = title.replace(' ', '_')
        return {"text":f"https://{lang}.wikipedia.org/wiki/{title}"}

    def unknown(self, cmd):
        return {"text":f"Unknown command {cmd}"}