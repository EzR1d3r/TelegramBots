import redis
import time
import datetime as dt

import threading

from lib.Utils import RepeatTimer, s_cmd_splitter, dictToStr, utc_format
# from lib.UserDataManager import UserDataManager as UDM
# from lib.UserDataManager import DEF_USER_DATA


s_genUID     = "getUID"
s_timestamp  = "T"
s_note       = "N"
s_user       = "U"
s_user_notes = "UN"

max_td = dt.timedelta( hours = 14 )
min_td = dt.timedelta( hours = -12 )

format_data = "%d.%m.%Y %H:%M" # "07.07.2019 00:33"
format_time = "%H:%M"          # "00:33"

in_keywords = [ "in", "через" ]

mult = { 
            3600 : ["hou", "час"],
            60   : ["min", "мин"],
            1    : ["sec", "сек"],
        }

mult_dict = {}

for k, v in mult.items():
    for unit in v:
        mult_dict[unit] = k

class Note():
    s_ts      = "t"
    s_chat_id = "c"
    s_msg     = "m"
    s_rec     = "r"
    s_rec_i   = "ri"

    init_dict = {
                    s_ts      : "timestamp",
                    s_chat_id : "chat_id",
                    s_msg     : "message",
                    s_rec     : "recalls",
                    s_rec_i   : "rec_interval",
                }

    def __init__(self, timestamp = -1, chat_id = 0, message = "",
                        recalls = 0, rec_interval = 300):
        self.timestamp = timestamp
        self.chat_id = chat_id
        self.message = message
        self.recalls = recalls
        self.rec_interval = rec_interval

    def datetime(self, local_utc_sec = 0):
        return dt.datetime.fromtimestamp(self.timestamp) + dt.timedelta(seconds = local_utc_sec)

    def local(self, local_utc_sec):
        return self.timestamp + local_utc_sec

    def sdict(self):
        d = {
                self.s_ts     : self.timestamp,
                self.s_chat_id: self.chat_id,
                self.s_msg    : self.message,
                self.s_rec    : self.recalls,
                self.s_rec_i  : self.rec_interval,
            }

        return d

    @classmethod
    def from_dict(cls, _dict):
        kwargs = {}
        for k, v in _dict.items():
            v = int(v) if v.isdigit() else v
            kwargs[ cls.init_dict[k] ] = v

        return Note(**kwargs )

    def __bool__(self):
        return self.timestamp != -1

class RedisDBManager():
    def __init__(self):
        self.redisConn = redis.StrictRedis(host='localhost', port = 6379, db = 13,
                                            charset="utf-8", decode_responses=True)

    def saveTimeStamp(self, timestamp, uid):
        ts = f"{s_timestamp}:{timestamp}"
        # print( "SET", ts, threading.current_thread().getName() )
        self.redisConn.sadd( ts, uid )

    def saveNote( self, note ):
        uid = self.redisConn.incr( s_genUID, 1 )
        note_key = f"{s_note}:{uid}"
        usr_notes_key = f"{s_user_notes}:{note.chat_id}"
        
        self.redisConn.hmset( note_key, note.sdict() )
        self.redisConn.sadd( usr_notes_key, uid )

        return uid

    def saveUsrSetting(self, chat_id, setting, value):
        hash_name = f"{s_user}:{chat_id}"
        self.redisConn.hset( hash_name, setting, value )

    def getUsrSetting( self, chat_id, setting ):
        hash_name = f"{s_user}:{chat_id}"
        return self.redisConn.hget( hash_name, setting )

    def getNotes(self, timestamp):
        ts = f"{s_timestamp}:{timestamp}"
        uids = self.redisConn.smembers( ts )
        # print( "GET", ts, uids, threading.current_thread().getName() )

        notes = []
        if uids is not None:
            for uid in uids:
                notes.append( self.redisConn.hgetall( f"{s_note}:{uid}" ) ) # TODO pipeline
            
        return [ Note.from_dict(note_d) for note_d in notes]


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

    def handle(self, update):
        self.current_update = update
        text = update['message']['text']
        text = f"{self.current_cmd} {text}" if self.current_cmd else text
        resp = self.handele_cmd(text) if text.startswith('/') else self.handle_text(text)
        self.current_update = None

        return resp

    def handele_cmd(self, cmd):
        cmd = cmd.split( s_cmd_splitter )
        cmd_func = self.commands.get( cmd[0] )
        val = cmd[1] if len(cmd) > 1 else ""
        result = self.unknown(cmd) if cmd_func is None else cmd_func(val)
        
        return result

    def handle_text(self, text):
        note = self.parseMsg( text )        
        if note:
            self.pushNote( note )
            date = note.datetime( local_utc_sec = self.getUsrUTC() )
            msg = f"Note set to { date.strftime(f'%d.%b.%Y  %H:%M:%S') }"
        else:
            msg = "Something goes wrong"

        return {"text":msg}

    def sendRemind(self, note):
        chat_id = note.chat_id
        msg = { "chat_id": chat_id, "text": note.message }
        self.processor.send_message( **msg )

    def checkNotes(self):
        timestamp = round( dt.datetime.utcnow().timestamp() )
        notes = self.db.getNotes( timestamp )
        
        for note in notes:
            self.sendRemind( note )

    ## utils funcs

    def parseMsg(self, text):
        text_list = text.lower().split( " " )
        try:
            if (text_list[0] in in_keywords):
                note = self.parse_InMsgType( text_list, text )
            else:
                note = self.parse_DateMsgType(text_list, text)
        except:
            note = Note()

        return note

    def parse_InMsgType(self, text_list, original_text):
        t = text_list[1:]
        msg = ""
        time, idx = 0, 0

        while idx < len(t):
            if t[idx].isdigit():
                time += float( t[idx] ) * mult_dict[ t[idx+1][:3] ]
                idx+=2
            else:
                msg = t[idx]
                idx+=1

        if time <= 0: raise ValueError
        
        delta = dt.timedelta( seconds = time )
        note_dt_utc = dt.datetime.utcnow() + delta

        chat_id = self.current_update['message']['chat']['id']
        timestamp = round( note_dt_utc.timestamp() )

        return Note( timestamp = timestamp, chat_id = chat_id, message = msg )

    def parse_DateMsgType(self, text_list, original_text):
        date_s = " ".join( text_list[:2]  )
        msg    = " ".join( text_list[2:] )

        date = dt.datetime.strptime( date_s, format_data )
        note_dt_utc = date - dt.timedelta( seconds = self.getUsrUTC())

        chat_id = self.current_update['message']['chat']['id']
        timestamp = round( note_dt_utc.timestamp() )

        return Note( timestamp = timestamp, chat_id = chat_id, message = msg )

    def getUsrUTC(self, chat_id = None):
        if chat_id is None:
            chat_id = self.current_update['message']['chat']['id']
        utc_delta_sec = self.db.getUsrSetting( chat_id, "UTC" )
        utc_delta_sec = int ( utc_delta_sec )
        return utc_delta_sec

    def pushNote(self, note):
        uid = self.db.saveNote( note )
        self.db.saveTimeStamp( note.timestamp, uid )

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


    ## commands

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
                chat_id = self.current_update['message']['chat']['id']
                utc_sec = round(utc.total_seconds())
                self.db.saveUsrSetting( chat_id, "UTC", utc_sec )
            except ValueError:
                text = f"Wrong timezone format: {val}"
            except RuntimeError as e:
                text = str(e)

            self.current_cmd = ""
        
        return {"text":text}

    def unknown(self, cmd):
        return {"text":f"Unknown command {cmd}"}



# def local_UsrDateTime(self, chat_id):
#     date = dt.datetime.utcnow()
#     utc = self.db.getUsrSetting( chat_id, "utc" )

#     delta = dt.timedelta( seconds = int(utc) )

#     return date + delta

# class UTC(dt.tzinfo):
#     def __init__(self, utc, name="", dst=0):
#         self.__utc = utc
#         self.__name = name
#         self.__dst = dst

#     def tzname(self, dt):
#         return self.__name

#     def utcoffset(self, dt):
#         "datetime -> timedelta, positive for east of UTC, negative for west of UTC"
#         return dt.timedelta( seconds = self.__utc )

#     def dst(self, dt):
#         return dt.timedelta( seconds = self.__dst)