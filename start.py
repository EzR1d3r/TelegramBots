import requests
import datetime
import time



wiki_bot_token = "715818372:AAFPZmjThAvLEHqcjEXDaKwuFRW-PLjmvLs"
proxies =   {
                "http": "192.33.31.130:80",
                "https": "104.248.51.47:8080",
            }

class BotHandler:

    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}/"

        self.session = requests.Session()
        self.session.proxies = proxies

    def get_updates(self, offset=None, timeout=1000):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        query  = self.api_url + method
        resp = self.session.get(query, params=params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
        method = 'sendMessage'
        resp = self.session.post(self.api_url + method, params)
        return resp

    def get_last_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[-1]
        else:
            last_update = get_result[len(get_result)]

        return last_update

def main():

    new_offset = None
    now = datetime.datetime.now()
    hour = now.hour

    greet_bot = BotHandler(wiki_bot_token)  
    greetings = ('здравствуй', 'привет', 'ку', 'здорово')  
    
    while True:
        greet_bot.get_updates(new_offset)
        last_update = greet_bot.get_last_update()
        print( last_update )
        print( hour )

        last_update_id = last_update['update_id']
        last_chat_text = last_update['message']['text']
        last_chat_id = last_update['message']['chat']['id']
        last_chat_name = last_update['message']['chat']['first_name']

        if last_chat_text.lower() in greetings and 6 <= hour < 12:
            greet_bot.send_message(last_chat_id, 'Доброе утро, {}'.format(last_chat_name))

        elif last_chat_text.lower() in greetings and 12 <= hour < 17:
            greet_bot.send_message(last_chat_id, 'Добрый день, {}'.format(last_chat_name))

        elif last_chat_text.lower() in greetings and 17 <= hour <= 23:
            greet_bot.send_message(last_chat_id, 'Добрый вечер, {}'.format(last_chat_name))

        new_offset = last_update_id + 1
        time.sleep(1)

if __name__ == '__main__':  
    try:
        main()
    except KeyboardInterrupt:
        exit()