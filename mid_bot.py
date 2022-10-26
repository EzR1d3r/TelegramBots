#!/usr/bin/python3.7
#https://core.telegram.org/bots/api

from bots.mid_bot.MIDBot import MIDBot
from lib.BotProcessor import BotProcessor

def main():
    handler = MIDBot()
    processor = BotProcessor(handler)
    processor.process()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()