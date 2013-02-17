import os
import yaml
import numpy as np
from twython import Twython  # twitter api
from ttp import ttp  # twitter text parsing, $ pip install twitter-text-python
import HTMLParser
import logging
HTML_PARSER = HTMLParser.HTMLParser()

class Tweeterator(object):
    """Iterator over the entries in a user's twitter home timeline.

    This uses the Twython interface to the twitter API to get the most recent
    tweets from your home screen and feed them out as an iterator.

    Additionally, we use some simple disk-based persistence to store the tweet
    ids in a file. This way, when you rerun this code, you won't keep getting
    the same tweets from the top of your feed.
    """
    def __init__(self, app_key, app_secret, oauth_token, oauth_token_secret,
                 tweet_id_fn):
        """Create the object

        Parameters
        ----------
        app_key : str
        app_secret : str
        oauth_token : str
        oauth_token_secret : str
            You need to get these to connect to the twitter API
        tweed_id_fn : str
            Filename for the flat text file that's going to hold the ids of the
            tweets that have been dispensed.
        """

        self.t = Twython(app_key=app_key, app_secret=app_secret,
                         oauth_token=oauth_token,
                         oauth_token_secret=oauth_token_secret)

        self.tweet_id_fn = tweet_id_fn
        self.seen_ids = []
        self.buffer = []

        if os.path.exists(self.tweet_id_fn):
            self.seen_ids = np.loadtxt(self.tweet_id_fn, dtype=int, ndmin=1).tolist()

    def pull(self, count=20):
        """Fetch some tweets

        The iterator will invoke this method automatically if you ask for the
        next tweet and it doesn't have any available, but for efficiency if you
        know exactly how many you want, you can 'preload' the buffer by asking
        for the right amount

        Parameters
        ----------
        count : int
            How many to fetch
        """

        min_id = None
        if len(self.seen_ids) > 0:
            min_id = min(self.seen_ids) - 1

        self.buffer = self.t.getHomeTimeline(count=count, include_rts=False,
                                             max_id=min_id)
        logging.info('pulled %d tweets', count)

    def __iter__(self):
        """Part of the iterator API"""
        return self

    def next(self):
        """Get the next tweet

        Returns
        -------
        text : str
            The text of the tweet, after being sanitized
        """
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
