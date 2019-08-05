import os
import datetime as dt

import redis
from .Note import Note
from lib.Utils import MAIN_FNAME, BOTS_PATH

s_genUID     = "getUID"
s_timestamp  = "T"
s_note       = "N"
s_user       = "U"
s_user_notes = "UN"

SCRIPTS_DIR  = "scripts"
SCRIPTS_PATH = os.path.join( BOTS_PATH, MAIN_FNAME, SCRIPTS_DIR )

class RedisDBManager():
    def __init__(self):
        self.redisConn = redis.StrictRedis(host='localhost', port = 6379, db = 13,
                                            charset="utf-8", decode_responses=True)
        self.pipe = self.redisConn.pipeline()
        self.load_scripts()

    def load_scripts(self):
        get_ts_notes_path = os.path.join( SCRIPTS_PATH, "get_ts_notes.lua" )
        get_usr_notes_path = os.path.join( SCRIPTS_PATH, "get_usr_notes.lua" )

        with open( get_ts_notes_path ) as script_file:
            self.sha_get_notes = self.redisConn.script_load( script_file.read() )

        with open( get_usr_notes_path )  as script_file:
            self.sha_get_usr_notes = self.redisConn.script_load( script_file.read() )

    def saveNote( self, note ):
        note_key = f"{s_note}:{note.uid}"
        usr_notes_key = f"{s_user_notes}:{note.chat_id}"
        ts_key = f"{s_timestamp}:{note.timestamp}"
        ttl = self.gen_ttl( note.timestamp )

        d = note.sdict()
        del d[Note.s_uid]
        self.pipe.hmset( note_key, d )
        self.pipe.expire( note_key, ttl )
        
        self.pipe.sadd( usr_notes_key, note.uid )
        self.pipe.expire( usr_notes_key, ttl ) # могут накапливаться недействительные uid
        
        self.pipe.sadd( ts_key, note.uid )
        self.pipe.expire( ts_key, ttl )

        self.pipe.execute()

    def removeNote( self, uid ):
        note_key = f"{s_note}:{uid}"
        note = Note.from_dict( self.redisConn.hgetall( note_key ) )

        if note:
            self.pipe.delete( note_key )

            usr_notes_key = f"{s_user_notes}:{note.chat_id}"
            self.pipe.srem( usr_notes_key, uid )

            ts_key = f"{s_timestamp}:{note.timestamp}"
            self.pipe.srem( ts_key, uid )

            self.pipe.execute()

            return True

        return False

    def saveUsrSetting(self, chat_id, setting, value):
        hash_name = f"{s_user}:{chat_id}"
        self.redisConn.hset( hash_name, setting, value )

    def getUsrSetting( self, chat_id, setting ):
        hash_name = f"{s_user}:{chat_id}"
        return self.redisConn.hget( hash_name, setting )

    def getNotes(self, timestamp):
        notes = self.redisConn.evalsha( self.sha_get_notes, 0,
                                        s_timestamp, timestamp, s_note, Note.s_uid )
        return [ Note.from_list(note_l) for note_l in notes ]

    def getUsrNotes(self, chat_id):
        usr_notes_key = f"{s_user_notes}:{chat_id}"
        notes = self.redisConn.evalsha( self.sha_get_usr_notes, 1,
                                        usr_notes_key, s_note, Note.s_uid )
        return [ Note.from_list(note_l) for note_l in notes ]

    def gen_ttl(self, utc_timestamp):
        return round (utc_timestamp - dt.datetime.utcnow().timestamp() + 20)

    def genUID(self):
        return self.redisConn.incr( s_genUID, 1 )