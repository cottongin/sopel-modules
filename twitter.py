import sopel.module
from sopel.formatting import *
from sopel.config.types import StaticSection, ValidatedAttribute

import pendulum
import tweepy
import re

class APIKey(StaticSection):
    consumer_key = ValidatedAttribute('consumer_key', str)
    consumer_secret = ValidatedAttribute('consumer_secret', str)

def setup(bot):
    bot.config.define_section('twitter', APIKey)
    regex = re.compile('.*(twitter.com\/.*\/status\/)([\w-]+).*')
    if 'url_callbacks' not in bot.memory:
        bot.memory['url_callbacks'] = {regex: tweetinfo}
    else:
        exclude = bot.memory['url_callbacks']
        exclude[regex] = tweetinfo
        bot.memory['url_callbacks'] = exclude

def configure(config):
    config.define_section('twitter', APIKey, validate=False)
    config.twitter.configure_setting('consumer_key', '')
    config.twitter.configure_setting('consumer_secret', '')

def _twitter_auth(bot):
    # Auth stuff
    consumer_key = bot.config.twitter.consumer_key
    consumer_secret = bot.config.twitter.consumer_secret
    if not consumer_key or not consumer_secret:
        return bot.say("I need proper Twitter API keys to work")
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    api = tweepy.API(auth)
    return api


def _parse_status(status):
    try:
        tweet_text = "RT " + status.retweeted_status.full_text
    except AttributeError:  # Not a Retweet
        tweet_text = status.full_text
    user = status.author.screen_name
    created_at = pendulum.parse(str(status.created_at), strict=False)
    if status.author.verified:
        user += color("✓", "white", "blue")
    diff = created_at.diff_for_humans()#.in_words()
    try:
        # retweets, likes
        tag = " | 🔃{} ❤️{}".format(
            status.retweet_count,
            status.favorite_count,
        )
    except:
        tag = ""
    reply_string = f"\x02(@{user})\x02 {tweet_text} | {diff}{tag}"
    return reply_string

@sopel.module.commands('twitter', 't')
@sopel.module.example('.twitter realDonaldTrump')
def twitter(bot, trigger):
    """Fetches most recent tweet from provided user"""

    api = _twitter_auth(bot)

    # check for input
    user_input = trigger.group(2)
    if not user_input:
        return bot.reply("Uhhh... who do you want me to lookup?")
    if len(user_input.split()) > 1:
        return bot.reply("I can only lookup one user at a time")

    data = tweepy.Cursor(api.user_timeline, id=f"{user_input}", tweet_mode="extended").items(1)
    try:
        for status in data:
            bot.say(_parse_status(status))
    except:
        return bot.reply("I couldn't find a twitter user by that handle ({})".format(user_input))

@sopel.module.commands('tsearch', 'ts')
@sopel.module.example('.tsearch donald trump')
def tsearch(bot, trigger):
    """Searches twitter"""

    api = _twitter_auth(bot)

    user_input = trigger.group(2)
    if not user_input:
        return bot.reply("Uhhh... what do you want to search for?")

    data = api.search(q=f"{user_input}", count=3, result_type="mixed", tweet_mode="extended")
    if data:
        for status in data:
            bot.say(_parse_status(status))
    else:
        return bot.reply("I couldn't find any results for that query")

@sopel.module.rule('.*(twitter.com\/.*\/status\/)([\w-]+).*')
def tweetinfo(bot, trigger, found_match=None):
    match = found_match or trigger
    tweet_id = match.group(2)
    
    api = _twitter_auth(bot)

    try:
        status = api.get_status(id=f"{tweet_id}", tweet_mode="extended")
        bot.say(_parse_status(status))
    except:
        return bot.reply("I couldn't find that tweet (was it deleted?)")