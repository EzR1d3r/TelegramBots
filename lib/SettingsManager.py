import os

from .Utils import projectDir, MAIN_FNAME
from lib.JSONFileHandler import JSONFileHandler

SETT_DIR        = os.path.join( projectDir(), "settings" )
SETT_FULL_PATH  = os.path.join( SETT_DIR, f"{MAIN_FNAME}.json" )

DEF_BOT_SETT = { "net":
                        {
                            "use_proxy" : False,
                            "proxy_list": { "http":[], "https":[] },
                        }
                }

SettingsManager = JSONFileHandler( SETT_FULL_PATH,  DEF_BOT_SETT)