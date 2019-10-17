from sopel.config.types import StaticSection, ChoiceAttribute, ValidatedAttribute
from sopel.module import commands, example
from sopel.formatting import *

from urllib.parse import quote_plus
import html
from html.parser import HTMLParser
import re

import requests

import pendulum


###
# Module config/setup/shutdown
###

API_CHANNELS_URL = "https://somafm.com/channels.json"
API_SONGS_URL = "https://somafm.com/songs/{}.json"


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


def configure(config):
    pass


def setup(bot):
    pass


def shutdown(bot):
    pass


###
# Commands
###

@commands('somafm', 'soma', 'somanp')
@example('.somafm groove salad')
def somafm_info(bot, trigger):
    """Fetches information for a provided station name from SomaFM"""
    user_input = trigger.group(2)
    if not user_input:
        return bot.reply("I need a station to lookup!")
    stations = _fetch(bot, API_CHANNELS_URL)
    # user_input = user_input.split()
    station = None
    for channel in stations['channels']:
        if user_input.strip().lower() == channel['title'].lower():
            station = channel
    if not station:
        return bot.reply("I couldn't find any station by that name ({})".format(user_input))
    channel_id = station["id"]
    tracks = _fetch(bot, API_SONGS_URL.format(channel_id))
    artist = tracks["songs"][0]["artist"] 
    song = tracks["songs"][0]["title"]
    album = tracks["songs"][0]["album"]
    reply = (f"[SomaFM] {bold(station['title'])} ({station['listeners']} listeners)"
             f" {station['description']} | {bold('DJ')}: {station['dj']} | {bold('Genre')}: {station['genre'].replace('|','/')}"
             f" | {bold('Playing')}: {song} by {artist} [{album}]"
    )
    return bot.say(reply)



###
# Internal Functions
###

def _fetch(bot, url, data=None, headers=None):
    try:
        response = requests.get(url, headers=headers).json()
        return response
    except:
        return None


def _shorten(bot, long_url):
    try:
        key = bot.config.podcasts.bitly_key
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer {}".format(key)
        }
        payload = {
            "long_url": long_url
        }
        url = "https://api-ssl.bitly.com/v4/shorten"
        response = requests.post(url, json=payload, headers=headers)
        short_url = response.json().get("link")
    except:
        short_url = long_url
    return short_url or long_url


# from Supybot/Limnoria utils.str
def _normalizeWhitespace(s, removeNewline=True, newLineChar=" "):
    r"""Normalizes the whitespace in a string; \s+ becomes one space."""
    if not s:
        return str(s) # not the same reference
    s = html.unescape(s)
    try:
        s = _strip_tags(s)
    except:
        pass
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
    return s


def _strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()