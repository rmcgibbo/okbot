import sys
from lib.models import *
from lib.database import db
from lib.settings import Settings
SETTINGS = Settings('settings.yml')


methods = ['threads']

def threads():
    for thread in db.query(Thread).all():
        for msg in thread.messages:
            if msg.sender == SETTINGS.okcupid['username']:
                print '[OkBot]:  %s' % msg.body.encode('utf-8').strip()
            else:
                print '[Suitor]: %s' % msg.body.encode('utf-8').strip()
        print


def print_usage():
    print >> sys.stderr, 'Usage: %s [%s]' % (sys.argv[0], ', '.join(methods))


if __name__ == '__main__':
    try:
        if sys.argv[1] in methods:
            globals()[sys.argv[1]]()
        else:
            print_usage()
    except IndexError:
        print_usage()
                