import os

from .Utils import projectDir, MAIN_FNAME
from lib.JSONFileHandler import JSONFileHandler

SETT_DIR        = os.path.join( projectDir(), "settings" )
SETT_FULL_PATH  = os.path.join( SETT_DIR, f"{MAIN_FNAME}.json" )

DEF_BOT_SETT = { "net":
                            {
                                "use_proxy" : False,
                                "proxy_list": { "http":[], "https":[] },
                            },
                 "common":
                            {
                                "load_passed_upd": False
                            }
                }

class SettingsManager( JSONFileHandler ):
    def __init__(self, path, default:dict = None):
        super().__init__( path, default )

        if self.get( "net", "use_proxy" ):
            self.https_proxy_it = self.cycle_iterator( self.get( "net", "proxy_list", "https" ) )
        else:
            self.https_proxy_it = None

    @staticmethod
    def cycle_iterator( list_obj ):
        l = len( list_obj )
        if not l: raise StopIteration( "The list is empty" )
        idx = 0
        while True:
            try:
                isLast = (idx == l - 1)
                yield isLast, list_obj[idx]
                idx += 1
            except IndexError:
                idx = 0

SM = SettingsManager( SETT_FULL_PATH,  DEF_BOT_SETT)