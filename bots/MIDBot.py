from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict


@dataclass
class SpamData:
    id_: int
    url: str
    cookie: str
    referer: str


class State(Enum):
    SET_ID = auto()
    SET_URL = auto()
    SET_COOKIE = auto()
    SET_REFERER = auto()
    WORK = auto()


class MIDBot:
    def __init__(self):
        self.commands = {
            "status": self.cmd_status,
            "current": self.cmd_current,
        }
        self.current_update = None
        self.state = State.WORK
        self.current_id: int = 0
        self.spams: Dict[int, SpamData] = {}

    def handle(self, update):
        self.current_update = update
        text = update["message"]["text"]
        return self.handele_cmd(text[1:]) if text.startswith("/") else self.handle_text(text)

    def handele_cmd(self, cmd: str):
        try:
            self.state = State[cmd.upper()]
            result = {"text": "State confirmed"}
        except KeyError:
            cmd_func = self.commands.get(cmd)
            result = self.unknown(cmd) if cmd_func is None else cmd_func(cmd)
        return result

    def handle_text(self, text):
        if self.current_id == 0 and self.state != State.SET_ID:
            return {"text": "You must set the id at first."}

        if self.state == State.SET_ID:
            self.current_id = int(text)

        spam_data = self.spams.setdefault(self.current_id, SpamData(self.current_id, "", "", ""))

        result = {}

        if self.state == State.SET_URL:
            spam_data.url = text
        elif self.state == State.SET_COOKIE:
            spam_data.cookie = text
        elif self.state == State.SET_REFERER:
            spam_data.referer = text
        elif self.state == State.WORK:
            result = {"text": f"Nothing to do with: {text}. Check state."}

        self.state = State.WORK

        return result or self.cmd_status("")

    def cmd_status(self, val):
        return {"text": f"Current id: {self.current_id}\nState: {self.state}"}

    def cmd_current(self, val):
        spam_data = self.spams.setdefault(self.current_id, SpamData(self.current_id, "", "", ""))
        return {"text": f"Current spam: {spam_data}."}

    def unknown(self, cmd):
        return {"text": f"Unknown command '{cmd}'"}
