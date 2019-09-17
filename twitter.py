import sopel.module
from sopel.formatting import *
from sopel.config.types import StaticSection, ValidatedAttribute

import pendulum
import tweepy

class APIKey(StaticSection):
    consumer_key = ValidatedAttribute('consumer_key', str)
    consumer_secret = ValidatedAttribute('consumer_secret', str)

def setup(bot):
    bot.config.define_section('twitter', APIKey)

def configure(config):
    config.define_section('twitter', APIKey, validate=False)
    config.twitter.configure_setting('consumer_key', '')
    config.twitter.configure_setting('consumer_secret', '')

@sopel.module.commands('twitter', 't')
@sopel.module.example('.twitter realDonaldTrump')
def twitter(bot, trigger):
    """Fetches most recent tweet from provided user"""

    # Auth stuff
    consumer_key = bot.config.twitter.consumer_key
    consumer_secret = bot.config.twitter.consumer_secret
    if not consumer_key or not consumer_secret:
        return bot.say("I need proper Twitter API keys to work")
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    api = tweepy.API(auth)

    # check for input
    user_input = trigger.group(2)
    if not user_input:
        return bot.reply("Uhhh... who do you want me to lookup?")
    if len(user_input.split()) > 1:
        return bot.reply("I can only lookup one user at a time")

    data = tweepy.Cursor(api.user_timeline, id=f"{user_input}", tweet_mode="extended").items(1)
    try:
        for status in data:
            try:
                tweet_text = status.retweeted_status.full_text
            except AttributeError:  # Not a Retweet
                tweet_text = status.full_text
            user = status.author.screen_name
            created_at = pendulum.parse(str(status.created_at), strict=False)
            if status.author.verified:
                user += " " + color("✓", "white", "blue")
            diff = created_at.diff_for_humans()#.in_words()
            reply_string = f"\x02@{user}:\x02 {tweet_text} | {diff}"
            bot.say(reply_string)
    except:
        return bot.reply("I couldn't find a twitter user by that handle ({})".format(user_input))