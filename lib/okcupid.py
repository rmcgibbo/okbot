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

        while not 'Welcome' in self._browser.title:
            logging.info('Waiting on load...')
            sleep(2)

        logging.info('title: %s', self._browser.title)

        self._logged_in = True

    def get_threads(self, unique_by_user=True):
        """Get a summary of all of the current message threads from the main
        messages page.

        Return
        ------
        threads : list of dicts
            Each dict represents a current thread. It contains three keys, 'class',
            'text', and 'threadid'. Text is the last message in the thread -- the
            one displayed on http://www.okcupid.com/messages
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

    def scrape_thread(self, threadid):
        """Scrape all of the messages in a conversation thread
        
        Parameters
        ----------
        threadid : int
            The id of the thread to scrape
        
        Returns
        -------
        messages : list
            List of dicts, representing the messages. Each msg contains
            'id', 'sender', 'body', 'time'
        """
        thread_url = 'http://www.okcupid.com/messages' + \
            '?readmsg=true&threadid=%s&folder=1' % threadid
        self._browser.get(thread_url)
        sleep(2)
        
        collapse_btn = self._browser.find_element_by_xpath('//li[@id="collapse"]')
        if collapse_btn:
            collapse_btn.click()
        
        def parse_msg(elem):
            id = elem.get_attribute('id')

            # there are some elements in the thread list that actually aren't
            # messages, so we'll filter those out
            if not id.startswith('message_'):
                return None
            id = id.replace('message_', '')

            xpath = elem.find_element_by_xpath  # cache the method name
            body = xpath('.//div[@class="message_body"]').get_attribute('innerHTML')
            sender = xpath('./a[@class="photo"]').get_attribute('title')
            fancydate = xpath('.//span[@class="fancydate"]').get_attribute('innerHTML')
            
            body = body.replace('<em class="mobilemsg">Sent from the OkCupid app</em>', '')
            body = body.strip()
            
            return {'id': id, 'sender': sender, 'body': body, 'fancydate': fancydate}
        
        thread_items = self._browser.find_elements_by_xpath('//ul[@id="thread"]/li')
        # run parse_msg on each entry, but remove the None entries
        return [e for e in [parse_msg(e) for e in thread_items] if e is not None]
        

def test1():
    with open('settings.yml') as f:
        settings = yaml.load(f)
        username = settings['okcupid']['username']
        password = settings['okcupid']['password']

    bot = OkCupid(username, password)
    bot.login()
    sleep(2)

    threads = bot.get_threads()
    print bot.scrape_thread(threads[10].threadid)
    #bot.reply_to_thread(, 'message')

if __name__ == '__main__':
    test1()
