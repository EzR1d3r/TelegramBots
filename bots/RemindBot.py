import json
import requests
import redis
import time
from threading import Timer

from lib.UserDataManager import UserDataManager as UDM
from lib.UserDataManager import DEF_USER_DATA


s_genUID    = "getUID"
s_timestamp = "timestamp"
s_note      = "note"



class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait( self.interval ):
            if not self.finished.is_set():
                self.function(*self.args, **self.kwargs)
        
    def cancel( self ):
        super().cancel()
        self.function = None # для корректного завершения, чтобы не сохранились циклические ссылки на self владельца таймера


class RedisDBManager():
    def __init__(self):
        self.redisConn = redis.StrictRedis(host='localhost', port = 6379, db = 13)

    def saveTimeStamp(self, timestamp):
        uid = self.redisConn.incr( s_genUID, 1 )
        ts = f"{s_timestamp}:{timestamp}"
        self.redisConn.set( ts, uid )
        return uid

    def saveNote( self, uid, settings ):
        k = f"{s_note}:{uid}"
        self.redisConn.hmset( k, settings )

    def getNote(self, timestamp):
        ts = f"{s_timestamp}:{timestamp}"
        uid = self.redisConn.get( ts )

        if uid is not None:
            uid = uid.decode()
            note = self.redisConn.hgetall( f"{s_note}:{uid}" )
            return note

class RemindBot:
    def __init__(self):

        self.commands = {
                            "/start"    : self.cmd_start,
                        }

        self.current_update = None
        self.db = RedisDBManager()
        self.timer = RepeatTimer(1, self.checkNotes)
        self.timer.start()
        self.processor = None

    def sendRemind(self, note):
        chat_id = note[b'chat_id'].decode()
        msg = { "chat_id": chat_id, "text": "ALARM!!!" }
        self.processor.send_message( **msg )

    def checkNotes(self):
        timestamp = round( time.time() )
        print( "check", timestamp )
        note = self.db.getNote( timestamp )
        print(note)
        if note is not None:
            self.sendRemind( note )

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
        resp = {}
        timestamp, prepared_settings = self.parseMsg( text )
        
        if timestamp:
            self.makeNote( timestamp, prepared_settings )

        return resp

    def parseMsg(self, text):
        timestamp = 0

        try:
            timestamp = int(text)
        except ValueError:
            timestamp = round( time.time() ) + 5

        settings = { "chat_id": self.current_update['message']['chat']['id'], "recalls":1 }
        prepared_settings = self.dictToStr( settings )

        return timestamp, prepared_settings

    def makeNote(self, timestamp, settings):
        print( "make", timestamp, settings )
        uid = self.db.saveTimeStamp( timestamp )
        self.db.saveNote( uid, settings )

    def dictToStr(self, d):
        s_dict = {}
        for k, v in d.items():
            s_dict[ str(k) ] = str(v)
        
        return s_dict

    def cmd_start(self, val):
        return {"text":"Greetings! I am ezRemindBot.\n"}

    def unknown(self, cmd):
        return {"text":f"Unknown command {cmd}"}