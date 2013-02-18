from tumblpy import Tumblpy
import yaml
settings_fn = 'settings.yml'

with open(settings_fn) as f:
    settings = yaml.load(f)

t = Tumblpy(app_key=settings['tumblr']['consumer_key'],
            app_secret=settings['tumblr']['consumer_secret'],
            oauth_token=settings['tumblr']['oauth_token'],
            oauth_token_secret=settings['tumblr']['oauth_secret'])

posts = t.get('posts', blog_url='okbot.tumblr.com')
print posts