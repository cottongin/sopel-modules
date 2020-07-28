import sopel.module
from sopel.formatting import *

import requests
import urllib.parse
import pendulum

API_URL = "https://www.sportsline.com/sportsline-web/service/v1/odds?league={league}&auth=3"
NHL_URL = "https://www.sportsline.com/sportsline-web/service/v1/picksheet?league=nhl&includeVideo=false&auth=3"

VALID_LEAGUES = {
    "cfb":   "ncaaf",
    "ncaaf": "ncaaf",
    "nfl":   "nfl",
    "mlb":   "mlb",
    "nba":   "nba",
    "nhl":   "nhl",
}

@sopel.module.commands('odds')
@sopel.module.example('.odds nfl ne')
def odds(bot, trigger):
    """Fetches odds for provided sport/team."""

    query = trigger.group(2)
    if not query:
        return bot.reply("You need to give me at least a league!")

    league = query.split()[0]
    if league.lower() not in VALID_LEAGUES:
        return bot.reply(f"{league} is not a valid league")
    if league.lower() == "nhl":
        # fetch NHL odds
        try:
            results = requests.get(NHL_URL).json()
        except:
            return bot.reply('ERROR: Something went wrong fetching odds')
    else:
        league = VALID_LEAGUES[league.lower()]
        try:
            url = API_URL.format(league=league)
            results = requests.get(url).json()
        except:
            return bot.reply('ERROR: Something went wrong fetching odds')

    team = []
    tmp = query.split()
    if len(tmp) > 1:
        # we have a team(s)
        for q in tmp[1:]:
            if q.lower() == 'wsh' and tmp[0].lower() == 'mlb':
                q = 'was'
            team.append(q)
    
    if league == "nhl":
        # parse NHL odds
        parsed = _parseNHLOdds(results)
    else:
        parsed = _parseOdds(results)

    if not parsed:
        return bot.reply("No odds found")
    if team or len(parsed) == 1:
        plucked = []
        if team:
            for tm in team:
                for game in parsed:
                    if tm.lower() == game["home"].lower() or tm.lower() == game["away"].lower():
                        plucked.append(game)
            if not plucked:
                for game in parsed:
                    if tm.lower() in game["home_full"].lower() or tm.lower() in game["away_full"].lower():
                        plucked.append(game)
        else:
            plucked = parsed
        if not plucked:
            return bot.reply("No results found for '{}'".format(' '.join(team)))
        for game in plucked:
            if game.get("spread_team"):
                if game["spread_team"] == game["home"]:
                    reply_string = "{} @ \x02{}[{}]({})\x02 (ml: {} {}) (o/u: {}) {}".format(
                        game["away_full"],
                        game["home_full"],
                        game["handicap"],
                        game["spread"],
                        game["ml_team"],
                        game["ml"],
                        game["ou"],
                        game["game_time"].in_tz("US/Eastern").format("ddd MMM Do h:mm A zz")
                    )
                else:
                    reply_string = "\x02{}[{}]({})\x02 @ {} (ml: {} {}) (o/u: {}) {}".format(
                        game["away_full"],
                        game["handicap"],
                        game["spread"],
                        game["home_full"],
                        game["ml_team"],
                        game["ml"],
                        game["ou"],
                        game["game_time"].in_tz("US/Eastern").format("ddd MMM Do h:mm A zz")
                    )
            else:
                reply_string = "{} @ {} (no odds yet) {}".format(
                    game["away_full"],
                    game["home_full"],
                    game["game_time"].in_tz("US/Eastern").format("ddd MMM Do h:mm A zz")
                )
            bot.say(reply_string)            
    else:
        reply_strings = []
        for game in parsed:
            if game.get("spread_team"):
                if game["spread_team"] == game["home"]:
                    rs = "{} @ \x02{}[{}]\x02 {}".format(
                        game["away"],
                        game["home"],
                        game["handicap"],
                        game["game_time"].in_tz("US/Eastern").format("M/DD hh:mmA zz")
                    )
                    reply_strings.append(rs)
                else:
                    rs = "\x02{}[{}]\x02 @ {} {}".format(
                        game["away"],
                        game["handicap"],
                        game["home"],
                        game["game_time"].in_tz("US/Eastern").format("M/DD hh:mmA zz")
                    )
                    reply_strings.append(rs)
            else:
                continue
        bot.say(" | ".join(reply_strings), max_messages=6)
    return

def _parseOdds(results):

    asof = pendulum.from_timestamp(results["lastUpdatedAt"]/1000)
    parsed = []
    for comp in results["competitions"]:
        tmpd = {}
        tmpd["home"] = comp["homeTeamAbbreviation"]
        tmpd["home_full"] = comp["homeTeamName"]
        tmpd["away"] = comp["awayTeamAbbreviation"]
        tmpd["away_full"] = comp["awayTeamName"]
        tmpd["game_time"] = pendulum.from_timestamp(comp["gameStartFullDate"]/1000)
        consensus = None
        if comp.get("sportsbookCompetitionOdds"):
            for sb in comp["sportsbookCompetitionOdds"]:
                if sb["sportsbook"] == "consensus":
                    consensus = sb
                    break
        if not consensus:
            tmpd["tbd"] = "No odds found"
        else:
            try:
                tmpd["ou"] = consensus["overUnder"]["total"]
            except:
                tmpd["ou"] = "Even"
            try:
                tmpd["ml"] = consensus["moneyLine"]["favoredTeamOdds"]
                tmpd["ml_team"] = consensus["moneyLine"]["favoredTeamAbbreviation"]
            except:
                tmpd["ml"] = ""
                tmpd["ml_team"] = ""
            try:
                tmpd["spread"] = consensus["spread"]["favoredTeamOdds"]
                tmpd["spread_team"] = consensus["spread"]["favoredTeamAbbreviation"]
                tmpd["handicap"] = consensus["spread"]["handicap"]
            except:
                tmpd["spread"] = ""
                tmpd["spread_team"] = ""
                tmpd["handicap"] = ""

        parsed.append(tmpd)

    return parsed

def _parseNHLOdds(results):

    asof = pendulum.from_timestamp(results["dataLastUpdated"]/1000)
    parsed = []
    for comp in results["picks"]:
        tmpd = {}
        tmpd["home"] = comp["homeTeamAbbrv"]
        tmpd["home_full"] = comp["homeTeamName"] + " " + comp["homeTeamNickName"]
        tmpd["away"] = comp["awayTeamAbbrv"]
        tmpd["away_full"] = comp["awayTeamName"] + " " + comp["awayTeamNickName"]
        tmpd["game_time"] = pendulum.from_timestamp(comp["gameStartFullDate"]/1000)
        try:
            tmpd["ou"] = comp["ouOddLabel"]
        except:
            tmpd["ou"] = "Even"
        try:
            tmpd["ml"] = comp["mlOddLabel"].split()[1]
            tmpd["ml_team"] = comp["mlOddLabel"].split()[0]
        except:
            tmpd["ml"] = ""
            tmpd["ml_team"] = ""
        try:
            tmpd["spread"] = consensus["spread"]["favoredTeamOdds"]
            tmpd["spread_team"] = consensus["spread"]["favoredTeamAbbreviation"]
            tmpd["handicap"] = consensus["spread"]["handicap"]
        except:
            tmpd["spread"] = tmpd["ml"]
            tmpd["spread_team"] = tmpd["ml_team"]
            tmpd["handicap"] = tmpd["ml"]

        parsed.append(tmpd)

    return parsed