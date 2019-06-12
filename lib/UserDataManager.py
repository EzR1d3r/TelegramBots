import os

from .Utils import projectDir, MAIN_FNAME
from lib.JSONFileHandler import JSONFileHandler

USERS_DATA_DIR        = os.path.join( projectDir(), "users_data" )
DATA_FULL_PATH  = os.path.join( USERS_DATA_DIR, f"{MAIN_FNAME}_UD.json" )


DEF_USER_DATA = { "language":"ru" }

UserDataManager = JSONFileHandler( DATA_FULL_PATH )