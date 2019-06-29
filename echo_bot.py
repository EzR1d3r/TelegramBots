#!/usr/bin/python3.7
#https://core.telegram.org/bots/api

from bots.EchoBot import EchoBot
from lib.BotProcessor import BotProcessor

def main():
    handler = EchoBot()
    processor = BotProcessor(handler)
    processor.process()

if __name__ == '__main__':  
    try:
        main()
    except KeyboardInterrupt:
        exit()