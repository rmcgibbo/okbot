# OkBot
_Respond to OkCupid messages with random tweets. Inspired by [this](http://jezebel.com/5984752/horseebooks-okc-account-proves-sad-point-about-online-dating-interaction)._

## Idea

### Step 1
Create a generic female profile on OkCupid. Stock with hot pics from flikr. There's
a good template to use for generic profiles, [here](http://thoughtcatalog.com/2011/a-guide-to-writing-the-most-generic-okcupid-profile-ever/2/)

### Step 2
Set up a twitter account that receives super random tweets from luminaries like
[@NietzschiMinaj](https://twitter.com/NietzschiMinaj), [@shitgirlssay](https://twitter.com/shitgirlssay),
[@KimKierkegaard](https://twitter.com/KimKierkegaard) and [@STACEYNIGHTMARE](https://twitter.com/STACEYNIGHTMARE).

### Step 3
Automatically Respond to all incoming messages with the tweet stream.

### Step 4
Post to tumblr? We'll see how this turns out

## Technologies

There is no public OKC API, so there's not going to be a "clean" solution to
managing an OkCupid message stream. But it's easy enough to hack using [Selenium
webdriver](http://docs.seleniumhq.org/), which lets us automate the browser
programmatically.

Twitter has a great API. Here, we're using the [Twython bindings](https://github.com/ryanmcgrath/twython),
which as you might guess are written in python.

Unfortunately, there aren't any python bindings for the new tumblr API. There
are, however, ruby bindings, so we'll do that portion of the code in ruby.
