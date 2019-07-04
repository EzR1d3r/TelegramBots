#!/usr/bin/python3.7
#https://core.telegram.org/bots/api

from bots.RemindBot import RemindBot
from lib.BotProcessor import BotProcessor

def main():
    handler = RemindBot()
    processor = BotProcessor(handler)
    handler.processor = processor
    processor.process()

if __name__ == '__main__':  
    try:
        main()
    except KeyboardInterrupt:
        exit()