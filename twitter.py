from sopel import module

from sopel.formatting import *
from sopel.config.types import StaticSection, ValidatedAttribute, ListAttribute

import pendulum
import tweepy
import re
import html
import humanfriendly

import math

millnames = ['','K','M','B','T']

def millify(n):
    nf = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if nf == 0 else math.log10(abs(nf))/3))))

    string = '{:,.1f}{}'.format(nf / 10**(3 * millidx), millnames[millidx])
    if string.endswith(".0"):
        return n
    else:
        return string

# from Supybot/Limnoria utils.str
def _normalizeWhitespace(s, removeNewline=True):
    r"""Normalizes the whitespace in a string; \s+ becomes one space."""
    if not s:
        return str(s) # not the same reference
    starts_with_space = (s[0] in ' \n\t\r')
    ends_with_space = (s[-1] in ' \n\t\r')
    if removeNewline:
        newline_re = re.compile('[\r\n]+')
        s = ' '.join(filter(bool, newline_re.split(s)))
    s = ' '.join(filter(bool, s.split('\t')))
    s = ' '.join(filter(bool, s.split(' ')))
    if starts_with_space:
        s = ' ' + s
    if ends_with_space:
        s += ' '
    return s

class APIKey(StaticSection):
    consumer_key = ValidatedAttribute('consumer_key', str)
    consumer_secret = ValidatedAttribute('consumer_secret', str)
    blacklist = ListAttribute('blacklist')

def configure(config):
    config.define_section('twitter', APIKey, validate=False)
    config.twitter.configure_setting('consumer_key', '')
    config.twitter.configure_setting('consumer_secret', '')
    # config.twitter.configure_setting('blacklist', '')

def setup(bot):
    bot.config.define_section('twitter', APIKey)
    regex = re.compile('.*(twitter.com\/.*\/status\/)([\w-]+).*')
    if 'url_callbacks' not in bot.memory:
        bot.memory['url_callbacks'] = {regex: tweetinfo}
    else:
        exclude = bot.memory['url_callbacks']
        exclude[regex] = tweetinfo
        bot.memory['url_callbacks'] = exclude

def _twitter_auth(bot):
    # Auth stuff
    consumer_key = bot.config.twitter.consumer_key
    consumer_secret = bot.config.twitter.consumer_secret
    if not consumer_key or not consumer_secret:
        return bot.say("I need proper Twitter API keys to work")
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    api = tweepy.API(auth)
    return api

def _parse_status(status, include_link=False):
    try:
        tweet_text = color("[RT @{}] ".format(status.retweeted_status.author.screen_name), "red") + status.retweeted_status.full_text
        rt = True
    except AttributeError:  # Not a Retweet
        tweet_text = status.full_text
        rt = False
    tweet_text = html.unescape(tweet_text)
    tweet_text = _normalizeWhitespace(tweet_text)
    user = color(status.author.screen_name, "cyan")
    created_at = pendulum.parse(str(status.created_at), strict=False)
    if status.author.verified:
        user += color("✓", "white", "blue")
    if "theKongfuzi" in user:
        user += color("✓", "white", "blue")
    user += " - {}".format(status.author.name)
    diff = created_at.diff_for_humans()#.in_words()
    try:
        # retweets, likes
        retweet = bold(color("🗘", colors.CYAN))
        likes = bold(color("❤", colors.RED))
        tag = " ({} {} / {} {})".format(
            retweet,
            millify(status.retweet_count if not rt else status.retweeted_status.retweet_count),
            likes,
            millify(status.favorite_count if not rt else status.retweeted_status.favorite_count),
        )
    except:
        tag = ""
    reply_string = f"\x02(@{user})\x02 {tweet_text} | {diff}{tag}"
    if include_link:
        reply_string += f" | https://twitter.com/{status.user.screen_name}/status/{status.id_str}"
    return reply_string

@module.commands('twitter', 'tw')
@module.example('.twitter realDonaldTrump')
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

@module.commands('tsearch', 'ts')
@module.example('.tsearch donald trump')
def tsearch(bot, trigger):
    """Searches twitter"""

    api = _twitter_auth(bot)

    user_input = trigger.group(2)
    if not user_input:
        return bot.reply("Uhhh... what do you want to search for?")

    result_type = "mixed"
    check_input = user_input.split()
    tmp = user_input.split()
    include_link = False
    for arg in tmp:
        if "--" in arg:
            check_input.remove(arg)
            arg = arg.replace("--", "").lower()
            if arg == "recent":
                result_type = "recent"
            elif arg == "popular":
                result_type = "popular"
            elif arg == "noretweets" or arg == "no-retweets":
                check_input.append("-filter:retweets")
            elif arg == "link" or arg == "include-link":
                include_link = True
    user_input = " ".join(check_input)
    # print(f'query={user_input}', f'result_type={result_type}') #TODO LOGGER this

    data = api.search(q=f"{user_input}", count=3, result_type=result_type, lang="en", tweet_mode="extended")
    if data:
        for status in data:
            bot.say(_parse_status(status, include_link=include_link))
    else:
        return bot.reply("I couldn't find any results for that query")

@module.rule('.*(twitter.com\/.*\/status\/)([\w-]+).*')
def tweetinfo(bot, trigger, found_match=None):
    try:
        blacklist = bot.config.twitter.blacklist
    except:
        blacklist = None
    if blacklist:
        if trigger.sender in blacklist:
            return
    match = found_match or trigger
    tweet_id = match.group(2)
    
    api = _twitter_auth(bot)

    try:
        status = api.get_status(id=f"{tweet_id}", tweet_mode="extended")
        bot.say(_parse_status(status))
    except:
        return bot.reply("I couldn't find that tweet (was it deleted?)")
