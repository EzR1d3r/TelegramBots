import datetime as dt

class Note():
    s_uid     = "u"
    s_ts      = "t"
    s_chat_id = "c"
    s_msg     = "m"
    s_rec     = "r"
    s_rec_i   = "ri"

    init_dict = {
                    s_uid     : "uid",
                    s_ts      : "timestamp",
                    s_chat_id : "chat_id",
                    s_msg     : "message",
                    s_rec     : "recalls",
                    s_rec_i   : "rec_interval",
                }

    def __init__(self, uid = -1, timestamp = -1, chat_id = 0, message = "",
                        recalls = 0, rec_interval = 300):
        self.uid = uid 
        self.timestamp = timestamp
        self.chat_id = chat_id
        self.message = message
        self.recalls = recalls #пока не используется
        self.rec_interval = rec_interval #пока не используется

    def datetime(self, local_utc_sec = 0):
        return dt.datetime.fromtimestamp(self.timestamp) + dt.timedelta(seconds = local_utc_sec)

    def local(self, local_utc_sec):
        return self.timestamp + local_utc_sec

    def sdict(self):
        d = {
                self.s_uid    : self.uid,
                self.s_ts     : self.timestamp,
                self.s_chat_id: self.chat_id,
                self.s_msg    : self.message,
                self.s_rec    : self.recalls,
                self.s_rec_i  : self.rec_interval,
            }

        return d

    def __str__(self):
        return f"[UID: {self.uid}] {self.datetime().strftime('%d.%m.%Y  %H:%M:%S')} {self.message}"

    @classmethod
    def from_dict(cls, _dict):
        kwargs = {}
        for k, v in _dict.items(): #заменяем сокращенные ключи полными именами полей
            v = int(v) if v.isdigit() else v
            kwargs[ cls.init_dict[k] ] = v

        return Note(**kwargs )

    @classmethod
    def from_list(cls, _list):
        d = {}
        for i in range( 0, len(_list), 2 ):
            d[ _list[i] ] = _list[i+1]

        return cls.from_dict( d )

    def __bool__(self):
        return self.timestamp != -1
