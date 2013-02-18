# OkBot
_Respond to OkCupid messages with random tweets. Inspired by [this](http://jezebel.com/5984752/horseebooks-okc-account-proves-sad-point-about-online-dating-interaction)._

## Technologies

There is no public OKC API, so there's not going to be a "clean" solution to
managing an OkCupid message stream. But it's easy enough to hack using [Selenium
webdriver](http://docs.seleniumhq.org/), which lets us automate the browser
programmatically.

Twitter has a great API. Here, we're using the [Twython bindings](https://github.com/ryanmcgrath/twython),
which as you might guess are written in python.
