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

API_SEARCH_URL = ("https://listen-api.listennotes.com/api/v2/"
                  "search?q={query}&type={type}&language=English"
                  "&only_in=title")
API_DETAIL_URL = ("https://listen-api.listennotes.com/api/v2/"
                  "{type}/{id}?sort={sort}")
API_GENRES_URL = "https://listen-api.listennotes.com/api/v2/genres"
API_BEST_URL = "https://listen-api.listennotes.com/api/v2/best_podcasts"
API_RANDOM_URL = "https://listen-api.listennotes.com/api/v2/just_listen"


class PodcastsSection(StaticSection):
    api_key = ValidatedAttribute('api_key', default=None)
    bitly_key = ValidatedAttribute('bitly_key', default=None)


class Error(Exception):
   """Base class for other exceptions"""
   pass
class APIKeyMissing(Error):
   """Raised when the API Key is missing"""
   pass


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
    config.define_section('podcasts', PodcastsSection, validate=False)
    config.podcasts.configure_setting('api_key', 'Listennotes.com API Key')
    config.podcasts.configure_setting('bitly_key', 'bit.ly API Key to shorten links')


def setup(bot):
    bot.config.define_section('podcasts', PodcastsSection)


def shutdown(bot):
    pass


###
# Commands
###

@commands('podcast', 'podinfo', 'pod')
@example('.podcast giant bombcast')
def podinfo(bot, trigger):
    """Fetches information for a provided podcast name"""
    # Input check
    # TODO: Return a random podcast if none provided? From top 10?
    user_input = trigger.group(2)
    if not user_input:
        return bot.reply("I need a podcast to lookup!")
    # Fetch
    try:
        results = _fetch(bot, API_SEARCH_URL.format(
            query = "\"{}\"".format(quote_plus(user_input)),
            type = "podcast"
        ))
        genres = _fetch(bot, API_GENRES_URL)
        genres = genres["genres"]
    except APIKeyMissing:
        return bot.reply("I'm missing the API Key")
    if not results["results"]:
        # broaden the search
        results = _fetch(bot, API_SEARCH_URL.format(
            query = quote_plus(user_input),
            type = "podcast"
        ).replace("&only_in=title",''))
        if not results["results"]:
            return bot.reply("Sorry, I couldn't find anything by that query")
    # Parse
    # for now let's assume first result is what we want
    result = results["results"][0]
    pod_id = result["id"] # let's get some details
    details = _fetch(bot, API_DETAIL_URL.format(
        type = "podcasts",
        id = pod_id,
        sort = "recent_first"
    ))
    if details:
        latest_ep_info = "{4} {1} ({0}) | published {2} | Listen @ {3}".format(
            pendulum.duration(seconds=details["episodes"][0]["audio_length_sec"]).in_words(),
            bold(details["episodes"][0]["title"]),
            pendulum.from_timestamp(details["episodes"][0]["pub_date_ms"]/1000).diff_for_humans(),
            _shorten(bot, details["episodes"][0]["listennotes_url"]),
            bold(color("[Latest Episode]", "orange"))
        )
    else:
        latest_ep_info = None
    name = result["title_original"]
    author = result["publisher_original"]
    desc = _normalizeWhitespace(result["description_original"]).strip()
    eps = result["total_episodes"]
    link = details.get("website") or result["listennotes_url"]
    pod_genres = []
    for id_ in result["genre_ids"]:
        for genre in genres:
            if id_ == genre["id"]:
                pod_genres.append(genre["name"])
    first_ep = pendulum.from_timestamp(result["earliest_pub_date_ms"]/1000)
    latest_ep = pendulum.from_timestamp(result["latest_pub_date_ms"]/1000)
    replies = []
    replies.append(f"{bold(color('[Podcast]', 'orange'))} {bold(name)} by {author} | {desc}")
    replies.append(f"{bold(color('[Info]', 'orange'))} {eps} episodes"
                   f" | Genre(s): {', '.join(pod_genres)}"
                   f" | First Published: {first_ep.format('YYYY')} | "
                   f"Most Recent: {latest_ep.format('M/D/YYYY')} | "
                   f"See more @ {_shorten(bot, link)}")
    if latest_ep_info:
        replies.append(latest_ep_info)
    for reply in replies:
        bot.say(reply, max_messages=2)
    return


@commands('bestpodcasts', 'bestpods', 'toppods')
@example('.bestpodcasts')
def bestpodcasts(bot, trigger):
    """Fetches the top 5 podcasts from Listennotes.com"""
    results = _fetch(bot, API_BEST_URL)
    podcasts = results.get("podcasts")
    if not podcasts:
        return bot.say("Sorry, I couldn't retreive anything from Listennotes.com")
    genres = _fetch(bot, API_GENRES_URL)
    genres = genres["genres"]
    replies = []
    link = results.get("listennotes_url")
    replies.append(f"{bold(color('[Top 5 Podcasts]', 'orange'))} via {link}")
    for idx,pod in enumerate(podcasts[:5]):
        desc = _normalizeWhitespace(pod["description"])
        if len(desc) >= 200:
            desc = desc[:199].strip() + "…" 
        pod_genres = []
        for id_ in pod["genre_ids"]:
            for genre in genres:
                if id_ == genre["id"]:
                    pod_genres.append(genre["name"])
        replies.append(f"{bold(color('[#' + str(idx+1) + ']', 'orange'))} "
                       f"{bold(pod['title'])} by {pod['publisher']}"
                       f" | {desc} {_shorten(bot, pod['listennotes_url'])} | "
                       f"{', '.join(pod_genres)}"
        )
    for reply in replies:
        bot.say(reply)
    return


@commands('randompodcast', 'randompod', 'randpod')
@example('.randompodcast')
def randompodcast(bot, trigger):
    """Fetches a random podcast episode from Listennotes.com"""
    result = _fetch(bot, API_RANDOM_URL)
    if not result:
        return bot.say("Sorry, I couldn't retreive anything from Listennotes.com")
    replies = []
    link = result.get("listennotes_url")
    desc = _normalizeWhitespace(result["description"])
    if len(desc) >= 100:
        desc = desc[:99].strip() + "…" 
    title = _normalizeWhitespace(result["title"])
    if len(title) >= 100:
        title = title[:99].strip() + "…" 
    replies.append(f"{bold(color('[Random Podcast]', 'orange'))} "
                   f"{bold(result['podcast_title'])} by {result['publisher']}"
                   f" | \x02Episode\x02: {title} ("
                   f"{pendulum.duration(seconds=result['audio_length_sec']).in_words()}"
                   f") | \x02Description\x02: {desc} | Listen @ {_shorten(bot, link)}"
    )
    for reply in replies:
        bot.say(reply)
    return


###
# Internal Functions
###

def _fetch(bot, url, data=None, headers=None):
    if not headers:
        # Auth check
        api_key = bot.config.podcasts.api_key
        if not api_key:
            raise APIKeyMissing
        headers = {
            "X-ListenAPI-Key": api_key
        }
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