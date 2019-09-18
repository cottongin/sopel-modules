import sopel.module
from sopel.formatting import *

import requests
import urllib.parse
import pendulum

import re

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

def _parse_results(data, desc=None):
    # parses data from API
    data = data["results"][0]
    name = bold(data['name'])
    location = data['pad']['name']
    when = pendulum.parse(data['net'], tz="UTC")
    status = data['status']['name']
    if "Go" in status:
        status = color(status, "green")
    if data['probability']:
        prob = f" ({data['probability']}%)" if data['probability'] > 0 else ""
    else:
        prob = ""
    try:
        mission = f"{bold(data['mission']['name'])}: {_normalizeWhitespace(data['mission']['description'])}"
    except:
        mission = None

    landing = None
    rocket = None
    if data['pad']['agency_id'] == 121:
        # SpaceX Landing Attempt?
        rockets = data['rocket']['launcher_stage']
        if len(rockets) == 1:
            # Falcon 9 Block 5
            landing = rockets[0]['landing']['attempt']
            # reused = rockets[0]['reused']
            # if reused:
            rocket = "Flight #{} for this booster.".format(rockets[0]['launcher_flight_number'])
            if landing:
                landing = rockets[0]['landing']['description']
        else:
            # Falcon Heavy
            #TBD
            pass
    lines = []
    lines.append(f"{name} from {location}")
    lines.append(f"{when.format('MMMM Do, YYYY - h:mm A z')}")
    if mission: lines.append(mission)
    if rocket:
        if landing:
            lines.append(rocket + " " + landing)
        else:
            lines.append(rocket)
    if status != "TBD":
        lines.append(f"\x02Status\x02: {status}{prob}")
    if data.get('vidURLs'):
        vid = " | {}".format(', '.join(data['vidURLs']))
    else:
        vid = ""
    lines.append(f"T-{when.diff().in_words()}{vid}")

    return lines


@sopel.module.commands('launch', 'space')
@sopel.module.example('.launch')
def launch(bot, trigger):
    """Fetches next scheduled rocket launch."""

    b_url = "https://spacelaunchnow.me/api/3.3.0/launch/upcoming/?format=json&limit=1"
    try:
        data = requests.get(b_url).json()
    except:
        return bot.reply("I couldn't fetch data from the API")
    
    if not data.get("results"):
        return bot.reply("No results returned from the API")

    parsed_data = _parse_results(data)

    for line in parsed_data:
        bot.say(line)

@sopel.module.commands('spacex')
@sopel.module.example('.spacex')
def spacex(bot, trigger):
    """Fetches next scheduled SpaceX rocket launch."""

    b_url = "https://spacelaunchnow.me/api/3.3.0/launch/upcoming/?format=json&limit=1&search=spacex"
    try:
        data = requests.get(b_url).json()
    except:
        return bot.reply("I couldn't fetch data from the API")
    
    if not data.get("results"):
        return bot.reply("No results returned from the API")

    parsed_data = _parse_results(data, "SpaceX")

    for line in parsed_data:
        bot.say(line)