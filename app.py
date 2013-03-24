#!/usr/bin/env python
"""
A simple OkCupid bot that replies to messages with entries from
a twitter feed.
"""

##############################################################################
# Imports
##############################################################################

import sys
import logging
import numpy as np
from select import select

from lib import okcupid, models
from lib.twitter import SortedTweeterator
from lib.settings import Settings
from lib.database import db, get_or_create, init_db

##############################################################################
# Globals
##############################################################################

init_db()
SETTINGS = Settings('settings.yml')

# time to wait after annoucing a response so that a console user can
# veto it.
PROMPT_TIMEOUT = 2  # seconds

logging.basicConfig(level=logging.INFO)

##############################################################################
# Functions
##############################################################################


def setup():
    """Load up an OkCupid object and a Tweeterator object, pulling startup info
    from the settings dict.
    """
    cupidbot = okcupid.OkCupid(SETTINGS.okcupid['username'],
                      SETTINGS.okcupid['password'])
    twitterstream = SortedTweeterator(app_key=SETTINGS.twitter['consumer_key'],
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
        log_threads(cupidbot, [tid])
        thread = db.query(models.Thread).filter_by(okc_id=tid).first()
        target = thread.messages[-1].body

        get_tweet = True

        while get_tweet:
            response = twitterstream.next(target=target)
            try:
                print 'RESPONDING WITH: "%s"' % response
            except UnicodeEncodeError:
                print 'Unicode error. Getting new tweet'
                continue
                
            sys.stdout.flush()

            rlist, _, _ = select([sys.stdin], [], [], PROMPT_TIMEOUT)
            if len(rlist) == 0:
                get_tweet = False
            else:
                # the user entered something, get a new tweet
                get_tweet = True

        cupidbot.reply_to_thread(tid, response, dry_run=False)
        #log_threads(cupidbot, [tid])
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
