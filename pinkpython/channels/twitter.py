from configparser import ConfigParser
import tweepy

from inbox import inbox_queue
from messages.message import Message
from credentials import consumer_key, consumer_secret, access_token, \
        access_token_secret


class TwitterChannel:
    def __init__(self, inbox_queue=inbox_queue):
        self.auth = None
        self.api = None
        self.username = 'pinkpythonbot'

        self.inbox_queue = inbox_queue
        self.listener = None
        self.stream = None

        self.__load_auth()
        self.__load_config()

    def __load_auth(self):
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(self.auth)

    def __load_config(self):
        config = ConfigParser()
        config.read('configuration.conf')
        self.username = config.get('twitter', 'username')

    def put_tweet(self, tweet):
        self.api.update_status(status=tweet)

    def send_response(self, message):
        reply_id, tweet = message.get_tweet_reply()
        self.api.update_status(tweet, reply_id)

    def init_listener(self):
        self.listener = TwitterListener(self.inbox_queue)
        self.stream = tweepy.Stream(auth=self.auth, listener=self.listener)
        self.stream.filter(track=[self.username], async=True)


class TwitterListener(tweepy.StreamListener):
    """
    Stream twitter mentions and put each mention message in the inbox queue
    """
    def __init__(self, inbox_queue):
        super().__init__()
        self.inbox_queue = inbox_queue

    def on_status(self, status):
        # logger.info('@[' + status.user.screen_name + ']:' + status.text)
        message = Message(status.text, platform='twitter', original=status)
        self.inbox_queue.put(message)

    def on_error(self, status_code):
        print('ERROR', status_code)
        if status_code == 420:
            logger.error("[420]:\tEnhance Your Calm!")
            return False


twitter_channel = TwitterChannel()


if __name__ == '__main__':
    from inbox import InboxConsumer
    from outbox import OutboxConsumer

    twitter_channel.init_listener()

    inbox_consumer = InboxConsumer()
    outbox_consumer = OutboxConsumer()
    inbox_consumer.start()
    outbox_consumer.start()
