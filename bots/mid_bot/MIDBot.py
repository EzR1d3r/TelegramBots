from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional
from threading import Thread

from bots.mid_bot.request_generator import make_request_gen
from lib.BotProcessor import BotProcessor


@dataclass
class SpamData:
    id_: int
    url: str
    cookie: str
    referer: str
    chat_id: int
    active: bool = False


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
            "start": self.cmd_start,
            "stop": self.cmd_stop
        }
        self.current_update = None
        self.state = State.WORK
        self.current_id: int = 0
        self.spams: Dict[int, SpamData] = {}
        self.processor: Optional[BotProcessor] = None

        self.set_defaults()

    def set_defaults(self): # HACK
        self.state = State.SET_ID
        self.handle_text("49198")
        self.state = State.SET_URL
        self.handle_text("https://yerevan.kdmid.ru/queue/SPCalendar.aspx?bjo=49198")

    @property
    def chat_id(self):
        return self.current_update['message']['chat']['id'] if self.current_update else 0

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

        spam_data = self.spams.setdefault(self.current_id, SpamData(self.current_id, "", "", "", self.chat_id))

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
        activity = "".join([f"{spam.id_}: {spam.active}\n" for spam in self.spams.values()])
        return {"text": f"Current id: {self.current_id}\nState: {self.state}\n{activity}"}

    def cmd_current(self, val):
        spam_data = self.spams.setdefault(self.current_id, SpamData(self.current_id, "", "", "", self.chat_id))
        return {"text": f"Current spam: {spam_data}."}

    def cmd_start(self, val):
        sd = self.spams.get(self.current_id)

        if sd and sd.url:
            sd.active = True
            gen = make_request_gen(sd.url, sd.cookie, sd.referer)
            gen.send(None)

            def loop():
                while sd.active:
                    res = gen.send((sd.active, 5))
                    if res.has_changes or (res.find_res == -1):
                        self.processor.send_message(
                            chat_id = self.chat_id,
                            text = f"Has changes: {res.has_changes}\nFind res: {res.find_res}"
                        )
                    print(res.has_changes, res.find_res)

                gen.close()
                self.processor.send_message(chat_id = self.chat_id, text=f"Stop the loop {sd.id_}, quit.")

            t = Thread(target=loop, daemon=True)
            t.start()
            msg = {"text":f"Start {sd.id_}, OK."}
        else:
            msg = {"text":f"Cant start {sd.id_}, quit."}

        return msg

    def cmd_stop(self, val):
        sd = self.spams.get(self.current_id)
        if sd:
            sd.active = False
        return {"text": f"Recieved stop command for {self.current_id}"}

    def unknown(self, cmd):
        return {"text": f"Unknown command '{cmd}'"}
