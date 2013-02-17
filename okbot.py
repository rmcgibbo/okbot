# main client
import yaml
import okcupid
import twitter
import logging
import time
logging.basicConfig(level=logging.INFO)

# load up the bots
with open('settings.yml') as f:
    settings = yaml.load(f)
cupidbot = okcupid.OkCupid(settings['okcupid']['username'],
                  settings['okcupid']['password'])
stream = twitter.Tweeterator(app_key=settings['twitter']['consumer_key'],
                 app_secret=settings['twitter']['consumer_secret'],
                 oauth_token=settings['twitter']['access_key'],
                 oauth_token_secret=settings['twitter']['access_secret'],
                 tweet_id_fn=settings['tweet_id_fn'])


cupidbot.login()
threads = cupidbot.get_threads()
logging.info(threads)
# count the number of messages we're going to send
n_replies = sum([1 for t in threads if t['class'] != 'repliedMessage'])

# load up that many tweets
stream.pull(n_replies)

for thread in threads:
    cupidbot.reply_to_thread(thread['threadid'], stream.next())

time.sleep(10)
