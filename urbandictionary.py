from sopel import module

from sopel.formatting import *
from sopel.config.types import StaticSection, ValidatedAttribute

import pendulum
import requests
import re
import urllib.parse


def configure(config):
    pass

def setup(bot):
    pass


@module.commands('urbandictionary', 'ud', 'define')
@module.example('.urbandictionary hello world')
@module.example('.ud --worst hello world')
def urbandictionary(bot, trigger):
    """Fetches the top definition from Urban Dictionary for provided input. 
    (use --worst to fetch the last/worst rated definition)"""

    api = "https://api.urbandictionary.com/v0/define?term={}"

    # check for --worst
    try:
        args = trigger.group(2).split()
    except:
        args = ["--worst"]
    worst = False
    if "--worst" in args:
        worst = True
        args.remove("--worst")
        user_input = " ".join(args)
    else:
        user_input = trigger.group(2)
    
    # check for input
    if not user_input:
        api = "https://api.urbandictionary.com/v0/random"
        worst = False

    # sanitize and fetch input
    user_input = urllib.parse.quote_plus(user_input.lower())
    api = api.format(user_input)
    try:
        results = requests.get(api)
        # print(results.url)
        results = results.json()
    except:
        return bot.reply("I couldn't retreive anything from Urban Dictionary")

    if "list" not in results:
        return bot.reply("Nothing found")
    else:
        if not results["list"]:
            return bot.reply("Nothing found")
    
    replies = _parse_definition(results["list"], worst)
    
    for reply in replies:
        bot.say(reply, max_messages=3)

    return


def _parse_definition(results, worst=False):
    
    if worst:
        data = results[-1]
    else:
        data = results[0]

    word = data["word"]
    definition = _normalizeWhitespace(data["definition"]).strip()
    example = ""
    if data.get("example"):
        example = _normalizeWhitespace(data["example"], newLineChar="; ")
        example = example.replace(word, bold(word))
    likes = "👍{}".format(data["thumbs_up"])
    dislikes = "👎{}".format(data["thumbs_down"])
    link = data["permalink"]

    replies = []
    replies.append(f"({bold(word)}) {definition} | {likes}/{dislikes}")
    if example:
        replies.append(f"ex: {example}")
    replies.append(f"See more @ {link}")
    return replies


# from Supybot/Limnoria utils.str
def _normalizeWhitespace(s, removeNewline=True, newLineChar=" "):
    r"""Normalizes the whitespace in a string; \s+ becomes one space."""
    if not s:
        return str(s) # not the same reference
    starts_with_space = (s[0] in ' \n\t\r')
    ends_with_space = (s[-1] in ' \n\t\r')
    if removeNewline:
        newline_re = re.compile('[\r\n]+')
        s = newLineChar.join(filter(bool, newline_re.split(s)))
    s = ' '.join(filter(bool, s.split('\t')))
    s = ' '.join(filter(bool, s.split(' ')))
    if starts_with_space:
        s = ' ' + s
    if ends_with_space:
        s += ' '
    s = s.replace("[", "").replace("]", "")
    return s