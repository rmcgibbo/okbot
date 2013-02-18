#!/usr/bin/env python
"""
A simple OkCupid bot that replies to messages with entries from
a twitter feed.
"""
import yaml
import logging
import time
import numpy as np

from lib import okcupid, twitter, models
from lib.settings import Settings
from lib.database import db, get_or_create, init_db
init_db()
SETTINGS = Settings('settings.yml')

logging.basicConfig(level=logging.INFO)

def setup():
    """Load up an OkCupid object and a Tweeterator object, pulling startup info
    from the settings dict.
    """
    cupidbot = okcupid.OkCupid(SETTINGS.okcupid['username'],
                      SETTINGS.okcupid['password'])
    twitterstream = twitter.Tweeterator(app_key=SETTINGS.twitter['consumer_key'],
                                 app_secret=SETTINGS.twitter['consumer_secret'],
                                 oauth_token=SETTINGS.twitter['access_key'],
                                 oauth_token_secret=SETTINGS.twitter['access_secret'],
                                 tweet_id_fn=SETTINGS.tweet_id_fn)
    return cupidbot, twitterstream


def respond_to_messages(cupidbot, twitterstream):
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

    threads = cupidbot.get_threads(['unreadMessage', 'readMessage'])
    logging.info('Replying to %s', threads)
    
    logging.info('number of unreplied messages: %d', len(threads))
    twitterstream.pull(len(threads))
    for tid in threads:
        cupidbot.reply_to_thread(tid, twitterstream.next(),
                                 dry_run=False)
        log_threads(cupidbot, [tid])
        okcupid.sleep()


def log_threads(cupidbot, thread_ids=None):
    """Open each thread and save it to the local database
    """
    if thread_ids is None:
        thread_ids = cupidbot.get_threads()

    logging.info('Logging thread ids: %s', thread_ids)
    
    for tid in thread_ids:
        logging.info('Logging thread %s', tid)
        thread = get_or_create(db, models.Thread, okc_id=tid)
        db.add(thread)
        db.flush()
        
        msgs = cupidbot.scrape_thread(tid)
        for msg in msgs:
            params = {'okc_id': msg['id'], 'thread_id': thread.id,
                      'sender': msg['sender'], 'body': msg['body'],
                      'fancydate': msg['fancydate']}
            message = get_or_create(db, models.Message, **params)
            logging.info(params)
            db.add(message)
    
        db.commit()
        logging.info('committed thread')
    

def main():
    cupidbot, twitterstream = setup()
    cupidbot.login()
    
    #log_threads(cupidbot)
    
    while True:
        respond_to_messages(cupidbot, twitterstream)
        cupidbot._browser.get('http://www.google.com')

        # random number close to 60 (seconds)
        r = 60 * (1 + 0.2*np.random.randn())
        okcupid.sleep(SETTINGS.sleep_time_minutes * r)


if __name__ == '__main__':
    main()