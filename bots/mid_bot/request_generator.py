from typing import NamedTuple
import requests as r
from time import sleep
from datetime import datetime


_ABSENT_MSG = "В настоящий момент на интересующее Вас консульское действие в системе предварительной записи нет свободного времени."
TIME_FORMAT = "%Y-%m-%d__%H_%M_%S"


# URL = "https://yerevan.kdmid.ru/queue/SPCalendar.aspx?bjo=49198"
# COOKIE_STR = "AlteonP=APQJQ46SL8HUmIxa1F0bCQ$$; __ddg1_=lgKur5ZTZBrpwI8G1yfX; w3qniias=queueid=2da2487d-72f3-4756-bd61-493a2aec544f; ASP.NET_SessionId=0h1iavirpjkpqxnkvaskwo45"
# REFERER = "https://yerevan.kdmid.ru/queue/OrderInfo.aspx?https%3a%2f%2fyerevan.kdmid.ru%2fqueue%2fOrderInfo.aspx%3fid=49198&ctl00%2524MainContent%2524txtID=49198&ctl00%2524MainContent%2524txtUniqueID=E1FD9D59&ctl00%2524MainContent%2524txtCode=988342&ctl00%2524MainContent%2524ButtonA=%25D0%2594%25D0%25B0%25D0%25BB%25D0%25B5%25D0%25B5&ctl00%2524MainContent%2524FeedbackClientID=0&ctl00%2524MainContent%2524FeedbackOrderID=0&ctl00%24MainContent%24txtID=49198&ctl00%24MainContent%24txtUniqueID=E1FD9D59&ctl00%24MainContent%24txtCode=954838&ctl00%24MainContent%24ButtonA=%u0414%u0430%u043b%u0435%u0435&ctl00%24MainContent%24FeedbackClientID=0&ctl00%24MainContent%24FeedbackOrderID=0"


class RequestResult(NamedTuple):
    has_changes: bool
    find_res: int
    html: str


def _parse_cookie_str(cookies: str) -> dict[str, str]:
    lines = cookies.split("; ")
    d = {}
    
    for l in lines:
        idx = l.find("=")
        name = l[:idx]
        val = l[idx+1:]
        d[name] = val
    
    return d


def make_request_gen(url: str, cookie: str, referer: str):
    cookies_dict = _parse_cookie_str(cookie)
    headers = {"referer": referer}
    old_res = ""

    is_active = True

    while is_active:
        try:
            res = r.get(url, headers=headers, cookies=cookies_dict)
        except r.RequestException as e:
            print(e) # TODO logging
        else:
            find_res = res.text.find(_ABSENT_MSG)
            has_changes = old_res != res.text
            old_res = res.text

            request_res = RequestResult(has_changes, find_res, res.text)
            
            is_active, sleep_time = yield request_res
            sleep(sleep_time)


if __name__ == "__main__":
    gen = make_request_gen(input("url\n"), input("cookie\n"), input("referer\n"))
    res = gen.send(None)

    for i in range(5):
        dt = datetime.now().strftime(TIME_FORMAT)
        if res.has_changes or (res.find_res == -1):
            with open(f"results/res_{dt}.html", "w") as f:
                f.write(res.html)
        gen.send(True, 2)

    gen.close()
