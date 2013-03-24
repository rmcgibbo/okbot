##############################################################################
# Imports
##############################################################################

from __future__ import division
import os
import yaml
import numpy as np
import logging

import HTMLParser
from twython import Twython  # twitter api
from ttp import ttp  # twitter text parsing, $ pip install twitter-text-python

##############################################################################
# Globals
##############################################################################

HTML_PARSER = HTMLParser.HTMLParser()
__all__ = ['Tweeterator', 'SortedTweeterator']

##############################################################################
# Functions
##############################################################################


def levenshtein(a,b):
    """Calculates the Levenshtein distance between a and b.

    http://hetland.org/coding/python/levenshtein.py
    """
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n

    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)

    return current[n]


def sanitize(text):
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


##############################################################################
# Classes
##############################################################################


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
            Filename for the flat text file that's going to hold the ids of
            the tweets that have been dispensed.
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

        buf = self.t.getHomeTimeline(count=count, include_rts=False, max_id=min_id)
        if len(buf) == 0:
            raise RuntimeError('Zero tweets sucessfully pulled from twitter API. :(')
        
        # add new tweets to old buffer
        self.buffer.extend([{'id': b['id'], 'text': sanitize(b['text'])} for b in buf])

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
        return tweet['text']


class SortedTweeterator(Tweeterator):
    ideal_buffer_len = 100
    large_number = 1e10
    
    def next(self, target=None):
        if target is None:
            return super(SortedTweeterator, self).next()
        
        if len(self.buffer) <= self.ideal_buffer_len / 2:
            self.pull(self.ideal_buffer_len)
        
        lower_target = target.lower()
        def normalized_distance(tweet):
            text = tweet['text']
            if len(text) == 0:
                return self.large_number
            dist = levenshtein(text.lower(), lower_target) / len(text)
            return dist
        
        # sort by distance to target
        self.buffer.sort(key=normalized_distance)
        # print [b['text'] for b in self.buffer]
        return super(SortedTweeterator, self).next()
            

##############################################################################
# Tests
##############################################################################


if __name__ == '__main__':
    with open('settings.yml') as f:
        settings = yaml.load(f)

    t = SortedTweeterator(app_key=settings['twitter']['consumer_key'],
                    app_secret=settings['twitter']['consumer_secret'],
                    oauth_token=settings['twitter']['access_key'],
                    oauth_token_secret=settings['twitter']['access_secret'],
                    tweet_id_fn=settings['tweet_id_fn'])

    prompts = ['What was your name', 'Want to fuck', 'What is your name', 'DTF?']
    for i in range(10):
        a = t.next(prompts[i])
        print 'Q:"%s". A:"%s"' % (prompts[i], a)
        prompts.append(a)