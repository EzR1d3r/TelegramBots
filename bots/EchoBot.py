import json
import requests

from lib.UserDataManager import UserDataManager as UDM
from lib.UserDataManager import DEF_USER_DATA

class EchoBot:
    def __init__(self):

        self.commands = {
                            "/start"    : self.cmd_start,
                        }

        self.current_update = None

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
        return {"text":text}

    def cmd_start(self, val):
        return {"text":"Greetings! I am ezEchoBot.\n"}

    def unknown(self, cmd):
        return {"text":f"Unknown command {cmd}"}