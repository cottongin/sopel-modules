import sopel.module
from sopel.formatting import *

import requests
import urllib.parse
import pendulum

API_URL = "https://www.sportsline.com/sportsline-web/service/v1/odds?league={league}&auth=3"

VALID_LEAGUES = {
    "cfb":   "ncaaf",
    "ncaaf": "ncaaf",
    "nfl":   "nfl",
    "mlb":   "mlb",
    "nba":   "nba",
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
    league = VALID_LEAGUES[league.lower()]
    team = []
    tmp = query.split()
    if len(tmp) > 1:
        # we have a team(s)
        for q in tmp[1:]:
            team.append(q)

    try:
        url = API_URL.format(league=league)
        results = requests.get(url).json()
    except:
        return bot.reply('ERROR: Something went wrong fetching odds')
    
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
            tmpd["spread"] = consensus["spread"]["favoredTeamOdds"]
            tmpd["spread_team"] = consensus["spread"]["favoredTeamAbbreviation"]
            tmpd["handicap"] = consensus["spread"]["handicap"]

        parsed.append(tmpd)

    if not parsed:
        return bot.reply("No odds found")
    if team:
        plucked = []
        for tm in team:
            for game in parsed:
                if tm.lower() == game["home"].lower() or tm.lower() == game["away"].lower():
                    plucked.append(game)
        if not plucked:
            for game in parsed:
                if tm.lower() in game["home_full"].lower() or tm.lower() in game["away_full"].lower():
                    plucked.append(game)
        if not plucked:
            return bot.reply("No results found for '{}'".format(team))
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
                        game["game_time"].in_tz("US/Eastern").format("ddd MMM DD h:mm A zz")
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
                        game["game_time"].in_tz("US/Eastern").format("ddd MMM DD h:mm A zz")
                    )
            else:
                reply_string = "{} @ {} (no odds yet) {}".format(
                    game["away_full"],
                    game["home_full"],
                    game["game_time"].in_tz("US/Eastern").format("ddd MMM DD h:mm A zz")
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
                rs = "{} @ {} (no odds yet) {}".format(
                    game["away"],
                    game["home"],
                    game["game_time"].in_tz("US/Eastern").format("M/DD hh:mmA zz")
                )
                reply_strings.append(rs)
        bot.say(" | ".join(reply_strings), max_messages=6)
    return