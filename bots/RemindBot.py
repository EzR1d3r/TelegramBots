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

in_keywords  = [ "in", "через" ]
day_keywords = [ "today", "tomorrow", "сегодня", "завтра" ]

mult = {
            0    : ["tod", "сег"], #today
            86400: ["tom", "зав"], #tomorrow
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
        for k, v in _dict.items(): #заменяем сокращенные ключи полными именами полей
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
        self.redisConn.expire( ts, self.gen_ttl( timestamp ) )

    def saveNote( self, note ):
        uid = self.redisConn.incr( s_genUID, 1 )
        note_key = f"{s_note}:{uid}"
        usr_notes_key = f"{s_user_notes}:{note.chat_id}"
        
        self.redisConn.hmset( note_key, note.sdict() )
        self.redisConn.expire( note_key, self.gen_ttl(note.timestamp) )

        self.redisConn.sadd( usr_notes_key, uid ) # TODO remove uid from set after ttl
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

    def gen_ttl(self, utc_timestamp):
        return round (utc_timestamp - dt.datetime.utcnow().timestamp() + 20)


class RemindBot:
    def __init__(self):

        #list of commands (have to be sent to FatherBot, look /setcommands)
        #start - Greetings
        #help - Description of available methods to make a note
        #timezone - Set your timezone

        self.commands = {
                            "/start"       : self.cmd_start,
                            "/timezone"    : self.cmd_timezone,
                            "/help"        : self.cmd_help,
                            # "/my_notes"    : self.cmd_my_notes,
                            # "/remove"      : self.cmd_remove,
                            # "/my_settings" : self.cmd_my_settings,
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
            responce_msg = f"Note '{note.message}' set to { date.strftime(f'%d.%m.%Y  %H:%M:%S') }"
        else:
            responce_msg = "Something goes wrong.\nMake sure that you set your timezone."

        return {"text":responce_msg}

    def sendRemind(self, note):
        chat_id = note.chat_id
        msg = { "chat_id": chat_id, "text": f"Remind: {note.message}" }
        self.processor.send_message( **msg )

    def checkNotes(self):
        timestamp = round( dt.datetime.utcnow().timestamp() )
        notes = self.db.getNotes( timestamp )
        
        for note in notes:
            self.sendRemind( note )

    ## utils funcs

    def parseMsg(self, text):
        text_list_lower = text.lower().split( " " )
        text_list_orig = text.split( " " )
        try:
            if (text_list_lower[0] in in_keywords):
                note = self.parse_InMsgType( text_list_lower, text_list_orig )
            elif (text_list_lower[0] in day_keywords):
                note = self.parse_DayMsgType( text_list_lower, text_list_orig )
            else:
                note = self.parse_DateMsgType(text_list_lower, text_list_orig)
        except:
            note = Note()

        return note

    def parse_InMsgType(self, text_list, text_list_orig):
        msg = ""
        time, idx = 0, 1

        while idx < len(text_list):
            if text_list[idx].isdigit():
                time += float( text_list[idx] ) * mult_dict[ text_list[idx+1][:3] ]
                idx+=2
            else:
                msg += f"{text_list_orig[idx]} "
                idx+=1

        if time <= 0: raise ValueError
        
        delta = dt.timedelta( seconds = time )
        note_dt_utc = dt.datetime.utcnow() + delta

        chat_id = self.current_update['message']['chat']['id']
        timestamp = round( note_dt_utc.timestamp() )

        return Note( timestamp = timestamp, chat_id = chat_id, message = msg )

    def parse_DateMsgType(self, text_list, text_list_orig):
        date_s = " ".join( text_list[:2]  )
        msg    = " ".join( text_list_orig[2:] )

        date = dt.datetime.strptime( date_s, format_data )
        note_dt_utc = date - dt.timedelta( seconds = self.getUsrUTC() )

        chat_id = self.current_update['message']['chat']['id']
        timestamp = round( note_dt_utc.timestamp() )

        return Note( timestamp = timestamp, chat_id = chat_id, message = msg )

    def parse_DayMsgType(self, text_list, text_list_orig):
        date = dt.datetime.utcnow()
        delta_sec = mult_dict[ text_list[0][:3] ]
        time = dt.datetime.strptime( text_list[1], format_time )
        date = date.replace( hour = time.hour, minute = time.minute, second = 0 )
        date += dt.timedelta( seconds = delta_sec )

        note_dt_utc = date - dt.timedelta( seconds = self.getUsrUTC() )

        chat_id = self.current_update['message']['chat']['id']
        timestamp = round( note_dt_utc.timestamp() )
        msg = " ".join( text_list_orig[2:] )

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
        chat_id = self.current_update['message']['chat']['id']
        msg = { "chat_id": chat_id, "text":"Greetings! I am ezRemindBot." }
        self.processor.send_message( **msg )
        return self.cmd_timezone()

    def cmd_help(self, val=""):
        msg =   "You can set the note by next methods:\n"\
                "In 15 minutes[hours, seconds] Call mom\n"\
                "In 1 hour 15 min Wake up!\n"\
                "Today[Tomorrow] 15:30 Send e-mail\n"\
                "7.7.2019 11:00 Feed fishes\n\n"\
                "Please configure your timezone (/timezone)\n"

        return {"text":msg}

    def cmd_timezone(self, val=""):
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