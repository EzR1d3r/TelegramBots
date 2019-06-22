#!/usr/bin/python3.7
#https://core.telegram.org/bots/api

from bots.WikiBot import WikiBot
from lib.BotProcessor import BotProcessor

def main():
    handler = WikiBot()
    processor = BotProcessor(handler)
    processor.process()

if __name__ == '__main__':  
    try:
        main()
    except KeyboardInterrupt:
        exit()