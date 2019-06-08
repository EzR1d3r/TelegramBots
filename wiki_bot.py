#!/usr/bin/python3.7
#https://core.telegram.org/bots/api

from bots.WikiBot import WikiBot
from lib.BotProcessor import BotProcessor

wiki_bot_token = "715818372:AAFPZmjThAvLEHqcjEXDaKwuFRW-PLjmvLs"

def main():
    handler = WikiBot()
    processor = BotProcessor(wiki_bot_token, handler)
    processor.process()

if __name__ == '__main__':  
    try:
        main()
    except KeyboardInterrupt:
        exit()