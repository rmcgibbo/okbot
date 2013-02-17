import time
import re
import yaml
import logging
import random
from collections import namedtuple

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

Message = namedtuple('Message', ['cls', 'text', 'threadid', 'user'])


def sleep(seconds='random'):
    "Sleep a few seconds"

    if seconds is 'random':
        time.sleep(random.random())
    else:
        time.sleep(seconds)


def uniqueify(seq, key):
    """Get the items from a list that are unique, when compared on one
    attribute, `key`

    for each item, we're looking at `item.key` (getattr(item, key)) and asking
    for it to be unique.
    """
    keys = set([])
    nodups = []
    for elem in seq:
        if getattr(elem, key) not in keys:
            nodups.append(elem)
        keys.add(getattr(elem, key))
    return nodups


class LoginError(Exception):
    pass


class OkCupid(object):
    """
    Selenium-Webdriver based "programmatic" interface to okcupid, since they
    don't actually have an API. Currently, it has only minimal functionality.
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self._browser = webdriver.Firefox()
        self._logged_in = False

    def __del__(self):
        self._browser.close()

    def login(self):
        """Log into the OKCupid site
        """

        logging.info('"%s" logging into OkCupid', self.username)
        self._browser.get('https://www.okcupid.com/login')
        elem = self._browser.find_element_by_xpath('//*[@id="user"]')
        elem.send_keys(self.username)
        elem = self._browser.find_element_by_xpath('//*[@id="pass"]')
        elem.send_keys(self.password + Keys.RETURN)
        sleep(5)

        if not 'Welcome' in self._browser.title:
            logging.error('title is no good')

        logging.info('title: %s', self._browser.title)

        self._logged_in = True

    def get_threads(self, unique_by_user=True):
        """Get a summary of all of the current message threads

        Return
        ------
        threads : list of dicts
            Each dict represents a current thread. It contains three keys, 'class',
            'text', and 'threadid'.
        """
        if not self._logged_in:
            raise LoginError('Not Logged In')

        self._browser.get('http://www.okcupid.com/messages')
        sleep()

        messages = []
        # get all of the conversations
        threads = self._browser.find_elements_by_xpath('//*[@id="messages"]/li')


        for thread in threads:
            # classes are 'unreadMessage', 'readMessage', 'repliedMessage'
            # filteredReadMessage

            try:
                match = re.search('/profile/(.*)',
                    thread.find_element_by_tag_name('a').get_attribute('href'))
                user = match.group(1)
            except Exception:
                logging.error('error parsing username %s', thread)
                user = 0

            try:
                threadid = re.search('\d+', thread.get_attribute('id')).group(0)
            except:
                logging.error('error parsing threadid %s', thread)
                raise

            m = Message(cls=thread.get_attribute('class'),
                        text=thread.text, threadid=threadid, user=user)
            messages.append(m)

        if unique_by_user:
            messages = uniqueify(messages, 'user')
        return messages

    def reply_to_thread(self, threadid, content, dry_run=False):
        """Reply to a message thread

        Parameters
        ----------
        threadid : int
            The id of the thread to reply to. This is returned as part of the dict
            in get_threads()
        content : str
            These are the characters that will be typed into the message box
        """
        if not self._logged_in:
            raise LoginError('Not Logged In')

        thread_url = 'http://www.okcupid.com/messages' + \
            '?readmsg=true&threadid=%s&folder=1' % threadid
        self._browser.get(thread_url)
        sleep(2)

        message_box = self._browser.find_element_by_xpath('//*[@id="message_text"]')
        message_box.send_keys(content)

        send_button = self._browser.find_element_by_xpath('//*[@id="send_button"]/a')

        if not dry_run:
            send_button.click()



def test1():
    with open('settings.yml') as f:
        settings = yaml.load(f)
        username = settings['okcupid']['username']
        password = settings['okcupid']['password']

    bot = OkCupid(username, password)
    bot.login()

    threads = bot.get_threads()
    print threads
    bot.reply_to_thread(threads[0]['threadid'], 'message')

def test2():
    threads = {'text': u'Ineed2ndchance\nHi.....\nFeb 16, 2013', 'user': u'Ineed2ndchance', 'class': u'readMessage', 'threadid': u'4522490969368588762'}, {'text': u'Ineed2ndchance\nLets talk we miave something in common.....\nFeb 16, 2013', 'user': u'Ineed2ndchance', 'class': u'readMessage', 'threadid': u'4522653868888182249'}
    print uniqueify(threads, 'user')

if __name__ == '__main__':
    test2()
