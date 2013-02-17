#!/usr/bin/env python
"""
A simple OkCupid bot that replies to messages with entries from
a twitter feed.
"""
import yaml
import logging
import time
import numpy as np


from lib import okcupid, twitter

logging.basicConfig(level=logging.INFO)

def setup(settings):
    """Load up an OkCupid object and a Tweeterator object, pulling startup info
    from the settings dict.
    """
    cupidbot = okcupid.OkCupid(settings['okcupid']['username'],
                      settings['okcupid']['password'])
    twitterstream = twitter.Tweeterator(app_key=settings['twitter']['consumer_key'],
                                 app_secret=settings['twitter']['consumer_secret'],
                                 oauth_token=settings['twitter']['access_key'],
                                 oauth_token_secret=settings['twitter']['access_secret'],
                                 tweet_id_fn=settings['tweet_id_fn'])
    return cupidbot, twitterstream


def responsd_to_messages(cupidbot, twitterstream):
    """Respond to all of the unreplied messages on the cupidbot with an
    entry from the twitterstream

    Parameters
    ----------
    cupidbot : okcupid.OkCupid
        An instance of the okcupid webdriver API, capable of interacting
        programmatically with the site
    twitterstream : twitter.Tweeterator
        An iterator that provides the text of tweets as a stream. Also needs
        to have a `pull` method asking it to load up some more tweets into
        its buffer
    """

    unreplied_convs = [t for t in cupidbot.get_threads() if t.cls != 'repliedMessage']
    logging.info('number of unreplied messages: %d', len(unreplied_convs))
    twitterstream.pull(len(unreplied_convs))
    for thread in unreplied_convs:
        cupidbot.reply_to_thread(thread.threadid, twitterstream.next(),
                                 dry_run=False)
        time.sleep(3)

def main():
    with open('settings.yml') as f:
        settings = yaml.load(f)

    cupidbot, twitterstream = setup(settings)
    cupidbot.login()
    while True:
        responsd_to_messages(cupidbot, twitterstream)
        cupidbot._browser.get('http://www.google.com')

        # random number close to 60 (seconds)
        r = 60 * (1 + 0.2*np.random.randn())
        time.sleep(settings['sleep_time_minutes'] * r)

if __name__ == '__main__':
    main()
