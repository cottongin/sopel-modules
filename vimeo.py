from sopel.formatting import color, colors, bold
from sopel.module import commands, example, url
from sopel.tools import get_logger

import requests
import pendulum

import re
import datetime

LOGGER = get_logger(__name__)
ISO8601_PERIOD_REGEX = re.compile(
    r"^(?P<sign>[+-])?"
    r"P(?!\b)"
    r"(?P<y>[0-9]+([,.][0-9]+)?(?:Y))?"
    r"(?P<mo>[0-9]+([,.][0-9]+)?M)?"
    r"(?P<w>[0-9]+([,.][0-9]+)?W)?"
    r"(?P<d>[0-9]+([,.][0-9]+)?D)?"
    r"((?:T)(?P<h>[0-9]+([,.][0-9]+)?H)?"
    r"(?P<m>[0-9]+([,.][0-9]+)?M)?"
    r"(?P<s>[0-9]+([,.][0-9]+)?S)?)?$")
REGEX = re.compile(r'(vimeo\.com/)([\w-]+)')

@url(REGEX)
def vimeo_get_info(bot, trigger, match=None):
    """
    Get information about the latest vimeo video uploaded by the channel provided.
    """
    match = match or trigger
    _vimeo_say_result(bot, trigger, match.group(2), include_link=False)

def _vimeo_say_result(bot, trigger, id_, include_link=True):
    """
    Parse and say result
    """
    url = "http://vimeo.com/api/v2/video/{vid}.json".format(vid=id_)
    try:
        response = requests.get(url)
        LOGGER.info(response.url)
        response = response.json()
    except:
        LOGGER.error("something went wrong fetching {}".format(url))
        return

    data = response[0]
    reply = {}
    vimeo_tag = color("vimeo", "cyan")
    reply_string = bold("[{}] ".format(vimeo_tag))
    reply['title'] = bold(data['title'])
    reply['duration'] = _parse_duration(data['duration'])
    reply['channel'] = "Channel: {}".format(data['user_name'])
    reply['views'] = "{:,} views".format(data['stats_number_of_plays'])
    reply['uploaded'] = "Uploaded {}".format(
        _parse_published_at_relative(bot, trigger, data['upload_date'])
    )
    reply_string += " | ".join(reply.values())

    bot.say(reply_string)


def _parse_duration(duration):
    replace = {
        " days": "d",
        " hours": "h",
        " minutes": "m",
        " seconds": "s",
    }
    dur = pendulum.duration(seconds=duration).in_words()
    for k,v in replace.items():
        dur = dur.replace(k,v)
    return dur

def _parse_published_at_relative(bot, trigger, published):
    now = pendulum.now()
    try:
        pubdate = pendulum.parse(published, strict=False)
    except:
        try:
            pubdate = datetime.datetime.strptime(published, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            pubdate = datetime.datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ')
        return tools.time.format_time(bot.db, bot.config, nick=trigger.nick,
            channel=trigger.sender, time=pubdate)
    return "{} ago".format(now.diff_for_humans(pubdate, absolute=True))
