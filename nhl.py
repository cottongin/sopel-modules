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

API_BASE_URL = "https://statsapi.web.nhl.com"

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

@commands('nhlplayer', 'nhlplayerinfo', 'player')
@example('.nhlplayer bos 63')
def nhl_player_info(bot, trigger):
    """Fetches information for a provided team name and roster number from nhl.com"""
    user_input = trigger.group(2)
    if not user_input:
        return bot.reply("I need something to lookup!")
    try:
        team = user_input.split()[0].upper()
        roster_number = user_input.split()[1]
    except:
        return bot.reply("I couldn't parse your input")
    teams_api = "/api/v1/teams?expand=team.roster"
    teams = _fetch(bot, API_BASE_URL + teams_api)
    # user_input = user_input.split()
    found_team = None
    for tm in teams['teams']:
        if team == tm['abbreviation']:
            found_team = tm
            break
    if not found_team:
        return bot.reply("I couldn't find any team by that name ({})".format(team))
    roster = found_team["roster"]["roster"]
    found_player = None
    for player in roster:
        if player['jerseyNumber'] == roster_number:
            found_player = player
            break
    if not found_player:
        return bot.reply("I couldn't find any player by that number ({})".format(roster_number))
    player_info_url = found_player['person']['link']
    player_data = _fetch(bot, API_BASE_URL + player_info_url)
    player_info = player_data['people'][0]
    name = player_info['fullName']
    plays_for = player_info['currentTeam']['name']
    weight = player_info['weight']
    height = player_info['height']
    position = player_info['primaryPosition']['name']
    if "goalie" in position.lower():
        draft_url_pos = "goalie"
        handed_phrase = "catches"
    else:
        draft_url_pos = "skater"
        handed_phrase = "shoots"
    age = str(player_info['currentAge'])
    captain = " | Captain" if player_info['captain'] else ""
    alt_captain = " | Alt. Captain" if player_info['alternateCaptain'] else ""
    rookie = " | Rookie" if player_info['rookie'] else ""
    active = f" | {bold('Active')}" if player_info['active'] else ""

    # draft_info_url = "https://api.nhle.com/stats/rest/en/{}?reportType=basic&reportName=bios&cayenneExp=playerId={}".format(draft_url_pos, player_info['id'])
    # bot.say(draft_info_url)
    draft_info_url = (
        "https://api.nhle.com/stats/rest/en/{}/bios?isAggregate=false"
        "&isGame=false&sort=%5B%7B%22property%22:%22lastName%22,%22direction"
        "%22:%22ASC_CI%22%7D,%7B%22property%22:%22skaterFullName%22,"
        "%22direction%22:%22ASC_CI%22%7D%5D&start=0&limit=1"
        "&factCayenneExp=gamesPlayed%3E=1&cayenneExp=gameTypeId=3"
        "%20and%20playerId%20=%20{}".format(draft_url_pos, player_info['id'])
    )
    try:
        draft_info = _fetch(bot, draft_info_url)
    except:
        draft_info = {}

    if draft_info.get('data'):
        draft_year = draft_info['data'][0]['draftYear']
        draft_round = draft_info['data'][0]['draftRound']
        draft_overall = draft_info['data'][0]['draftOverall']
        if draft_year:
            draft_full_url = "https://statsapi.web.nhl.com/api/v1/draft/{}".format(draft_year)
            draft_full_info = _fetch(bot, draft_full_url)
            draft = draft_full_info['drafts'][0]['rounds']
            for rnd in draft:
                if rnd['roundNumber'] == draft_round:
                    for pick in rnd['picks']:
                        if pick['pickOverall'] == draft_overall:
                            drafted_team = pick['team']['name']
            drafted = f" | Drafted by the {drafted_team} in {str(draft_year)}, Round {str(draft_round)} (#{str(draft_overall)} overall)"
        else:
            drafted = ""
    else:
        drafted = ""

    handed = player_info['shootsCatches']
    if player_info.get('birthStateProvince'):
        state_prov = f", {player_info.get('birthStateProvince')}"
    else:
        state_prov = ""
    birth = f" | Born: {pendulum.parse(player_info['birthDate'], strict=False).format('MMM Do, YYYY')} ({bold(age)} yrs old) in {player_info['birthCity']}{state_prov}, {player_info['birthCountry']}"
    jersey_number = player_info['primaryNumber']

    reply = (
        f"{bold(color('[NHL]', 'blue'))} {bold(name)} - {plays_for} - #{jersey_number} - {position} ({handed_phrase} {handed}H) | {height} / {weight}lbs"
        f"{active}{captain}{alt_captain}{drafted}{rookie}{birth}"
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
        return {}


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