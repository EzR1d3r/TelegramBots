import sys
import os
import datetime
import __main__
import pythonping as pp #https://pypi.org/project/pythonping/

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

def min_ping_host( hosts, timeout = 0.5 ):
    min_ping, ip = 1000 * timeout, None
    
    for host in hosts:
        host = host.split(':')
        resList  = pp.ping(host[0], timeout = timeout, count = 2 )
        success  = [ res.success for res in resList._responses ]
        avg_ping = resList.rtt_avg_ms

        if True in success and avg_ping < min_ping:
            min_ping, ip = avg_ping, ':'.join( host )

    return ip