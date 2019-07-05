import sys
import os
import datetime as dt
import __main__
import pythonping as pp #https://pypi.org/project/pythonping/

def projectDir():
    return sys.path[0]
    # return os.path.abspath( os.curdir ) + "/"

MAIN_FNAME = os.path.basename( __main__.__file__ ).replace( ".py", "" )
TOKEN_DIR = ".tokens"
TOKEN_DEF_PATH = os.path.join( projectDir(), TOKEN_DIR, f"{MAIN_FNAME}.token" )
s_cmd_splitter = " "

def date_std_format():
    date = dt.datetime.now()
    d = date.strftime('%d_%b_%Y')
    return d

def datetime_std_format(time_sep=":"):
    date = dt.datetime.now()
    return date.strftime(f'%d_%b_%Y_%H{time_sep}%M{time_sep}%S')

def time_std_format(t):
    print(t)
    return t.strftime( "%H:%M" )

def utc_format(time_delta):
    sec = round( time_delta.total_seconds() )
    sign = "-" if sec < 0 else "+"

    m = (abs(sec) // 60)
    h, m = m // 60, m % 60

    st = time_std_format( dt.time( hour = h, minute = m ) )
    return f"UTC{sign}{st}"

def min_ping_host( hosts, timeout = 0.5 ):
    # Attention! If proxy list or timeout is too large (or both),
    # application may starts pretty long time because of waiting timeout.
    min_ping, IP = (1000 * timeout), None
    
    for host in hosts:
        host = host.split(':')
        resList  = pp.ping(host[0], timeout = timeout, count = 2 )
        success  = [ res.success for res in resList._responses ]
        avg_ping = resList.rtt_avg_ms

        if True in success and avg_ping < min_ping:
            min_ping, IP = avg_ping, ':'.join( host )

    return IP

def dictToStr(d):
    s_dict = {}
    for k, v in d.items():
        s_dict[ str(k) ] = str(v)
    
    return s_dict