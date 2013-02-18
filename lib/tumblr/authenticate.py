from flask import Flask, session, redirect, url_for, escape, request
import oauth2 as oauth
import yaml
import urlparse
import urllib

app = Flask(__name__)

request_token_url = "http://www.tumblr.com/oauth/request_token"
authorize_url = "http://www.tumblr.com/oauth/authorize"
access_token_url = "http://www.tumblr.com/oauth/access_token"
my_callback_url = 'http://127.0.0.1:5000/auth'
settings_fn = 'settings.yml'

@app.route("/")
def index():
    with open(settings_fn) as f:
        settings = yaml.load(f)
        consumer = oauth.Consumer(settings['tumblr']['consumer_key'],
                                  settings['tumblr']['consumer_secret'])

    # adapted from https://github.com/simplegeo/python-oauth2
    client = oauth.Client(consumer)

    # using idea from http://stackoverflow.com/a/6040041/1079728
    # to provide the callback_url
    resp, content = client.request(request_token_url, "POST",
        body=urllib.urlencode({'oauth_callback': my_callback_url}))
    if resp['status'] != '200':
        raise Exception("Invalid response %s." % resp['status'])

    request_token = dict(urlparse.parse_qsl(content))

    return redirect("%s?oauth_token=%s" % (authorize_url,
        request_token['oauth_token']))


@app.route('/auth')
def auth(*args, **kwargs):
    with open(settings_fn) as f:
        settings = yaml.load(f)

    settings['tumblr']['oauth_token'] = request.args.get('oauth_token', None)
    settings['tumblr']['oauth_secret'] = request.args.get('oauth_verifier', None)

    with open(settings_fn, 'w') as f:
        yaml.safe_dump(settings, f, default_flow_style=True)

    return 'wrote tumblr oauth key to %s' % settings_fn

if __name__ == "__main__":
    app.run(debug=True)