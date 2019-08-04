import time
import datetime as dt

from .RedisDB_Manager import RedisDBManager
from .Note import Note
from lib.Utils import RepeatTimer, s_cmd_splitter, utc_format

###################################################################

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


###################################################################


class RemindBot:
    def __init__(self):

        #list of commands (have to be sent to FatherBot, look /setcommands)
        #start - Greetings
        #help - Description of available methods to make a note
        #timezone - Set your timezone
        #my_notes - List of your notes

        self.commands = {
                            "/start"       : self.cmd_start,
                            "/timezone"    : self.cmd_timezone,
                            "/help"        : self.cmd_help,
                            "/my_notes"    : self.cmd_my_notes,
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
            self.db.saveNote( note )
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

            note.uid = self.db.genUID()
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
        utc_offset = dt.timedelta( seconds = self.getUsrUTC() )
        date += utc_offset

        day_key = text_list[0][:3]
        delta_sec = mult_dict[ day_key ]
        time = dt.datetime.strptime( text_list[1], format_time )
        date = date.replace( hour = time.hour, minute = time.minute, second = 0 )
        date += dt.timedelta( seconds = delta_sec )

        note_dt_utc = date - utc_offset

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

    def cmd_my_notes(self, val=""):
        chat_id = self.current_update['message']['chat']['id']
        usr_utc = self.getUsrUTC( chat_id = chat_id )
        
        notes = self.db.getUsrNotes( chat_id )
        for note in notes: note.timestamp += usr_utc #для отображения в локальном времени пользователя
        
        notes_str = "\n".join(  [ str(note) for note in notes ]  )
        return {"text":f"{ notes_str }"}

    def unknown(self, cmd):
        return {"text":f"Unknown command {cmd}"}



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