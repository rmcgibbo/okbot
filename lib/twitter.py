import os
import yaml
import numpy as np
from twython import Twython  # twitter api
from ttp import ttp  # twitter text parsing, $ pip install twitter-text-python
import HTMLParser
import logging
HTML_PARSER = HTMLParser.HTMLParser()

class Tweeterator(object):
    def __init__(self, app_key, app_secret, oauth_token, oauth_token_secret,
                 tweet_id_fn):

        self.t = Twython(app_key=app_key, app_secret=app_secret,
                         oauth_token=oauth_token,
                         oauth_token_secret=oauth_token_secret)

        self.tweet_id_fn = tweet_id_fn
        self.seen_ids = []
        self.buffer = []

        if os.path.exists(self.tweet_id_fn):
            self.seen_ids = np.loadtxt(self.tweet_id_fn, dtype=int, ndmin=1).tolist()

    def pull(self, count=20):
        min_id = None
        if len(self.seen_ids) > 0:
            min_id = min(self.seen_ids) - 1

        self.buffer = self.t.getHomeTimeline(count=count, include_rts=False,
                                             max_id=min_id)
        logging.info('pulled %d tweets', count)

    def __iter__(self):
        return self

    def next(self):
        if len(self.buffer) <= 0:
            self.pull()

        tweet = self.buffer.pop(0)
        self.seen_ids.append(tweet['id'])
        with open(self.tweet_id_fn, 'a') as f:
            print >> f, tweet['id']
        return self._sanitize(tweet['text'])

    def _sanitize(self, text):
        """Remove links, hashtags and usernames from the tweet, and
        unescape HTML

        Parameters
        ----------
        text : str
            An input string, containing a raw tweet

        Returns
        -------
        text : str
            A santized version of the input, with stuff removed
        """

        text = ttp.URL_REGEX.sub('', text)
        text = ttp.HASHTAG_REGEX.sub('', text)
        text = ttp.USERNAME_REGEX.sub('', text)
        text = HTML_PARSER.unescape(text)
        return text


if __name__ == '__main__':
    with open('settings.yml') as f:
        settings = yaml.load(f)

    t = Tweeterator(app_key=settings['twitter']['consumer_key'],
                    app_secret=settings['twitter']['consumer_secret'],
                    oauth_token=settings['twitter']['access_key'],
                    oauth_token_secret=settings['twitter']['access_secret'],
                    tweet_id_fn=settings['tweet_id_fn'])

    for i in range(4):
        print t.next() + u'\n'

#oauth_token = auth_props['oauth_token']
#oauth_token_secret = auth_props['oauth_token_secret']
