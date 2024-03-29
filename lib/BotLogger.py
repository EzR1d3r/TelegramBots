import os
import datetime
from .Utils import projectDir, datetime_std_format, date_std_format, MAIN_FNAME

class BotLogger():
    def __init__(self, dirPath = "logs"):
        dirPath =os.path.join( projectDir(), dirPath )
        self.path = dirPath

        if not os.path.exists(dirPath):
            os.makedirs(dirPath)

    def log(self, text, ext=".log"):
        dt = datetime_std_format()
        fPath = os.path.join( self.path, f"{MAIN_FNAME}_{ date_std_format() }{ ext }" )

        with open(fPath, 'a') as file:
            file.write( f"{dt}:\n{text}\n\n" )

    def log_error(self, text):
        text = f"ERROR: {text}"
        self.log(text, ext=".err_log")

    def log_warning(self, text):
        text = f"WARNING: {text}"
        self.log(text, ext=".err_log")