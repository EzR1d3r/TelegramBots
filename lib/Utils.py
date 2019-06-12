import sys
import os
import datetime
import __main__

MAIN_FNAME      = os.path.basename( __main__.__file__ ).replace( ".py", "" )

def projectDir():
    return sys.path[0]
    # return os.path.abspath( os.curdir ) + "/"

def date_std_format():
    date = datetime.datetime.now()
    d = date.strftime('%d_%b_%Y')
    return d

def datetime_std_format(time_sep=":"):
    date = datetime.datetime.now()
    dt = date.strftime(f'%d_%b_%Y_%H{time_sep}%M{time_sep}%S')
    return dt