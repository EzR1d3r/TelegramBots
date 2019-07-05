import redis
import time
import datetime as dt
from threading import Timer

from lib.Utils import s_cmd_splitter, dictToStr, utc_format
# from lib.UserDataManager import UserDataManager as UDM
# from lib.UserDataManager import DEF_USER_DATA


s_genUID     = "getUID"
s_timestamp  = "T"
s_note       = "N"
s_user       = "U"
s_user_notes = "UN"

max_td = dt.timedelta( hours = 14 )
min_td = dt.timedelta( hours = -12 )


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
        self.redisConn = redis.StrictRedis(host='localhost', port = 6379, db = 13,
                                            charset="utf-8", decode_responses=True)

    def saveTimeStamp(self, timestamp, uid):
        ts = f"{s_timestamp}:{timestamp}"
        self.redisConn.sadd( ts, uid )

    def saveNote( self, note ):
        uid = self.redisConn.incr( s_genUID, 1 )
        note_key = f"{s_note}:{uid}"
        self.redisConn.hmset( note_key, note )

        chat_id = note["chat_id"]
        usr_notes_key = f"{s_user_notes}:{chat_id}"
        self.redisConn.sadd( usr_notes_key, uid )

        return uid

    def saveUsrSetting(self, chat_id, setting, value):
        hash_key = f"{s_user}:{chat_id}"
        self.redisConn.hset( hash_key, setting, value )

    def getNotes(self, timestamp):
        ts = f"{s_timestamp}:{timestamp}"
        uids = self.redisConn.smembers( ts )
        print(uids)

        notes = []
        if uids is not None:
            for uid in uids:
                notes.append( self.redisConn.hgetall( f"{s_note}:{uid}" ) )
            
        return notes

class RemindBot:
    def __init__(self):

        #list of commands (have to be sent to FatherBot, look /setcommands)
        #start - Description
        #timezone - Set your timezone

        self.commands = {
                            "/start"    : self.cmd_start,
                            "/timezone" : self.cmd_timezone,
                        }

        self.current_update = None
        self.current_cmd = ""
        self.db = RedisDBManager()
        self.timer = RepeatTimer(1, self.checkNotes)
        self.timer.start()
        self.processor = None

    def sendRemind(self, note):
        chat_id = note['chat_id']
        msg = { "chat_id": chat_id, "text": "ALARM!!!" }
        self.processor.send_message( **msg )

    def checkNotes(self):
        timestamp = round( time.time() )
        print( "check", timestamp )
        notes = self.db.getNotes( timestamp )
        
        for note in notes:
            self.sendRemind( note )

    def handle(self, update):
        self.current_update = update
        text = update['message']['text']

        text = f"{self.current_cmd} {text}" if self.current_cmd else text
        return self.handele_cmd(text) if text.startswith('/') else self.handle_text(text)

    def handele_cmd(self, cmd):
        cmd = cmd.split( s_cmd_splitter )
        cmd_func = self.commands.get( cmd[0] )
        val = cmd[1] if len(cmd) > 1 else ""

        result = self.unknown(cmd) if cmd_func is None else cmd_func(val)
        return result

    def handle_text(self, text):
        resp = {}
        timestamp, note_body = self.parseMsg( text )
        
        if timestamp:
            self.makeNote( timestamp, note_body )

        return resp

    def parseMsg(self, text):
        timestamp = 0

        try:
            timestamp = int(text)
        except ValueError:
            timestamp = round( time.time() ) + 5

        note_body = { "chat_id": self.current_update['message']['chat']['id'], "recalls":1 }
        note_body = dictToStr( note_body )

        return timestamp, note_body

    def makeNote(self, timestamp, note_body):
        print( "make", timestamp, note_body )

        uid = self.db.saveNote( note_body )
        self.db.saveTimeStamp( timestamp, uid )

    def parseUTC(self, val):
        val = val.split(":")
        l = len(val)
        utc = None

        if l == 2:
            h, m = [ int(i) for i in val ]
            m = - abs(m) if h < 0 else m
            
            utc = dt.timedelta( hours = h, minutes = m )
        elif l == 1:
            h = int(val[0])
            utc = dt.timedelta( hours = h )

        if not (min_td <= utc <= max_td): raise RuntimeError ( "Wrong UTC timezone." )

        return utc

    def cmd_start(self, val):
        return {"text":"Greetings! I am ezRemindBot.\n"}

    def cmd_timezone(self, val):
        if val == "":
            text = "Please, tell me your timezene." \
                    "Format is:\n" \
                    "'-3:00' (equal '-3'),\n" \
                    "'+5:45' (equal '5:45'),\n"\
                    "'+2:00' (equal '+2', '2')\n" \
                    "https://en.wikipedia.org/wiki/List_of_time_zones_by_country"

            self.current_cmd = "/timezone"
        else:
            try:
                utc = self.parseUTC( val )
                text = f"Timezone set as: { utc_format( utc ) }"
            except ValueError:
                text = f"Wrong timezone format: {val}"
            except RuntimeError as e:
                text = str(e)

            self.current_cmd = ""
        
        return {"text":text}

    def unknown(self, cmd):
        return {"text":f"Unknown command {cmd}"}