# main client
import yaml
import logging
import time
import numpy as np


from lib import okcupid, twitter

logging.basicConfig(level=logging.INFO)

def setup(settings):
    # load up the bots
    cupidbot = okcupid.OkCupid(settings['okcupid']['username'],
                      settings['okcupid']['password'])
    twitterstream = twitter.Tweeterator(app_key=settings['twitter']['consumer_key'],
                                 app_secret=settings['twitter']['consumer_secret'],
                                 oauth_token=settings['twitter']['access_key'],
                                 oauth_token_secret=settings['twitter']['access_secret'],
                                 tweet_id_fn=settings['tweet_id_fn'])

    cupidbot.login()

    return cupidbot, twitterstream


def responsd_to_messages(cupidbot, twitterstream):
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
    while True:
        responsd_to_messages(cupidbot, twitterstream)
        cupidbot._browser.get('http://www.google.com')

        # random number close to 60 (seconds)
        r = 60 * (1 + 0.2*np.random.randn())
        time.sleep(settings['sleep_time_minutes'] * r)

if __name__ == '__main__':
    main()