import time
import re
import yaml
import logging
import random
from collections import namedtuple
from lxml.html import soupparser

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
BASE_URL = 'https://www.okcupid.com%s'

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

    def __init__(self, username, password, browser='chrome'):

        browser_switch = {'chrome': webdriver.Chrome,
                        'firefox': webdriver.Firefox}
        try:
            self._browser = browser_switch[browser]()
        except KeyError:
            raise KeyError('Browser must be one of %s' % browser_switch.keys())
        
        self.username = username
        self.password = password
        self._logged_in = False

        self._root_soup_element_url = None
        self._root_soup_element = None

    def __del__(self):
        self._browser.close()

    def navigate_to(self, url, force_refresh=False):
        "Move the browser to a new url"
        
        if not (url.startswith('http://') or url.startswith('https://')):
            url = BASE_URL % url
        
        logging.info('Nativating to: %s', url)
        if (self._browser.current_url != url) or force_refresh:
            self._browser.get(url)
        sleep()

    def xpath(self, selector, force_rebuild=False):
        """Run the LXML/BeautifulSoup xpath engine
        
        Parameters
        ----------
        selector : str
            An xpath selector, executed on the whole document
        force_rebuild : bool, optional
            Should we necessarily rebuild the element tree?

        Returns
        -------
        elem : [lxml.Element]
        """
        if force_rebuild or (self._root_soup_element_url != self._browser.current_url):
            self._root_soup_element = soupparser.fromstring(self._browser.page_source)

        return self._root_soup_element.xpath(selector)

    def xpath0(self, selector, force_rebuild=False):
        """Get a single element with xpath
        
        Returns
        -------
        elem : lxml.Element, or None
        
        """
        e = self.xpath(selector, force_rebuild)
        if len(e) > 0:
            return e[0]
        return None


    def login(self):
        """Log into the OKCupid site
        """

        logging.info('"%s" logging into OkCupid', self.username)
        self.navigate_to('/login')
        elem = self._browser.find_element_by_xpath('//*[@id="user"]')
        elem.send_keys(self.username)
        elem = self._browser.find_element_by_xpath('//*[@id="pass"]')
        elem.send_keys(self.password)
        elem = self._browser.find_element_by_xpath('//*[@id="login_form"]/p/a')
        elem.click()

        while not 'Welcome' in self._browser.title:
            logging.info('Waiting on load...')
            sleep(2)

        logging.info('title: %s', self._browser.title)

        self._logged_in = True

    def get_threads(self, classes=None):
        """Get a summary of all of the current message threads from the main
        messages page.

        Parameters
        ----------
        cls : list of classes or a single class

        Return
        ------
        thread_ids : list of strings
            List of thread_id for each thread
        """
        logging.info('Getting all threads')
        
        if not self._logged_in:
            raise LoginError('Not Logged In')
        self.navigate_to('/messages')
        
        if isinstance(classes, basestring):
            classes = [classes]
        
        def thread_ids_on_page():
            if classes is None:
                threads = self.xpath('//*[@id="messages"]/li//p/@onclick')
                
            threads = []
            for cls in classes:
                xstring = '//*[@id="messages"]/li[@class="%s"]//p/@onclick' % cls
                threads += self.xpath(xstring)

            return [re.search('\d+', e).group(0) for e in threads]
        
        
        all_ids = thread_ids_on_page()
        
        
        # need to deal with the pagination
        while True:
            # look for a next button
            next = self.xpath0('//li[@class="next"]/a')
            if next is None:
                break
            else:
                logging.info('Going to Next')
                self.navigate_to(next.attrib['href'])
                all_ids += thread_ids_on_page()

        return all_ids


    def reply_to_thread(self, thread_id, content, dry_run=False):
        """Reply to a message thread

        Parameters
        ----------
        thread_id : str
            The id of the thread to reply to. This is returned as part of the dict
            in get_threads()
        content : str
            These are the characters that will be typed into the message box
        """
        if not self._logged_in:
            raise LoginError('Not Logged In')

        thread_url = 'http://www.okcupid.com/messages' + \
            '?readmsg=true&threadid=%s&folder=1' % thread_id
        self.navigate_to(thread_url)

        message_box = self._browser.find_element_by_xpath('//*[@id="message_text"]')
        message_box.send_keys(content)

        send_button = self._browser.find_element_by_xpath('//*[@id="send_button"]/a')

        if not dry_run:
            send_button.click()

    def scrape_thread(self, thread_id):
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
            '?readmsg=true&threadid=%s&folder=1' % thread_id
        self.navigate_to(thread_url)

        def parse_msg(elem):
            id = elem.attrib['id']

            # there are some elements in the thread list that actually aren't
            # messages, so we'll filter those out
            if not id.startswith('message_'):
                return None
            id = id.replace('message_', '')

            body = elem.xpath('.//div[@class="message_body"]')[0].text_content()
            # get the last bit of the href in the photo on this post
            sender = elem.xpath('./a[@class="photo"]')[0].attrib['href'].rsplit('/')[-1]

            try:
                fancydate = elem.xpath('.//span[@class="fancydate"]')[0].text_content()
            except:
                # this doesn't work when it's the last message and the date sent
                # is "just now"
                fancydate = None


            body = body.replace('Sent from the OkCupid app', '')
            body.strip()

            return {'id': id, 'sender': sender, 'body': body, 'fancydate': fancydate}

        message_items = self.xpath('//ul[@id="thread"]/li')
        # run parse_msg on each entry, but remove the None entries
        return [e for e in [parse_msg(e) for e in message_items] if e is not None]


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
