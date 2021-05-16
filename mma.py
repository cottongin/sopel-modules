import re
from urllib.parse import quote_plus


import flag
import pendulum
import requests
from sopel_sopel_plugin_argparser import parseargs

from sopel import module, tools
from sopel.formatting import bold, color, colors, underline


from sopel.tools.time import (
    format_time,
    get_channel_timezone,
    get_nick_timezone,
    get_timezone,
    validate_timezone
)

# import shlex

LOGGER = tools.get_logger("mma")

schedule_url = "https://www.espn.com/mma/schedule/_/year/2021?_xhr=pageContent"
event_url = (
    "https://site.web.api.espn.com/apis/common/v3/sports/mma/ufc"
    "/fightcenter/{event_id}?region=us&lang=en&contentorigin=espn"
    "&showAirings=buy%2Clive%2Creplay&buyWindow=1m"
)
fighter_search_url = (
    "https://site.api.espn.com/apis/common/v3/search?xhr=1&query={query}"
    "&limit=5&type=player&sport=mma&mode=prefix&lang=en&region=us"
)
fighter_search_news_url = (
    "https://site.api.espn.com/apis/common/v3/search?xhr=1&query={query}"
    "&limit=5&type=article&sport=mma&mode=prefix&lang=en&region=us"
)
fighter_news_url = (
    "https://api-app.espn.com/allsports/apis/v1/now?region=us&lang=en"
    "&contentorigin=espn&limit=3&content=story%2Cblog%2Crecap%2Ctheundefeated%2Cfivethirtyeight"
    "&contentcategories={player_id}"
    "&enable=peers%2Cheader"
)
fighter_bio_url = (
    "https://site.web.api.espn.com/apis/common/v3/sports/mma/athletes/{fighter_id}"
)
fighter_stats_url = (
    "https://site.web.api.espn.com/apis/common/v3/sports/mma/athletes/{fighter_id}/"
    "stats?region=us&lang=en&contentorigin=espn"
)

try:
    countries = requests.get("https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/slim-2/slim-2.json").json()
except:
    countries = []

@module.commands("fighter")
@module.example(".fighter overeem")
def fighter(bot, trigger):
    """Fetches UFC/MMA Fighter information
    Requires a name to lookup.

    Use --last to find stats from their last fight.
    """
    if not trigger.group(2):
        return bot.reply("You need to provide me someone to look for.")

    options = parseargs(trigger.group(2))
    LOGGER.info(options)
    if options:
        if options.get('extra_text'):
            query = quote_plus(options.get('extra_text'))
        pass
    else:
        query = quote_plus(trigger.group(2).strip())

    f_data = None
    t_data = None
    try:
        data = requests.get(fighter_search_url.format(query=query))
        LOGGER.debug(data.url)
        data = data.json()
        if data.get('items'):
            t_data = data['items'][0]
    except:
        bot.reply("Something went wrong searching.")
    if not t_data:
        return bot.reply("I couldn't find anyone by that query!")

    try:
        data = requests.get(fighter_bio_url.format(fighter_id=t_data['id']))
        LOGGER.debug(data.url)
        data = data.json()
    except:
        return bot.reply("I couldn't fetch that player's info")
    f_data = data['athlete']

    fighter_data = {}
    fighter_data['name'] = f_data['displayName']
    flg_code = None
    try:
        if len(f_data['flag']['alt']) > 3:
            for country in countries:
                if f_data['flag']['alt'] == country['name']:
                    flg_code = country['alpha-2']
                    break
        else:
            flg_code = f_data['flag']['alt'][:2]
        if not flg_code:
            flg_code = f_data['flag']['alt'][:2]

        try:
            if flg_code.lower() == "en":
                fighter_data['flag'] = "\x02🏴󠁧󠁢󠁥󠁮󠁧󠁿\x02"
            else:
                fighter_data['flag'] = "{}".format(flag.flag(flg_code))
        except:
            if flg_code.lower() == "en":
                fighter_data['flag'] = "\x02🏴󠁧󠁢󠁥󠁮󠁧󠁿\x02"
            else:
                fighter_data['flag'] = f_data['flag']['alt']
    except:
        fighter_data['flag'] = ""
    fighter_data['id'] = f_data['id']
    fighter_data['status'] = f_data['status']['name']
    fighter_data['links'] = {}
    for link in f_data['links']:
        if link.get('text') == 'Player Card':
            fighter_data['links']['pc'] = link['href']
        elif link.get('text') == 'Fight History':
            fighter_data['links']['fh'] = link['href']
    try:
        fighter_data['division'] = ' - {}'.format(f_data['weightClass']['text'])
    except:
        fighter_data['division'] = ''
    fighter_data['ht/wt/rch'] = "{}, {} ({} reach)".format(
        f_data.get('displayHeight', "--"),
        f_data.get('displayWeight', "--"),
        f_data.get('displayReach', "--")
    )
    fighter_data['team'] = f_data['association']['name'] if f_data['association'].get('name') else "Unassociated"
    fighter_data['dob/age'] = "{} ({})".format(
        pendulum.from_format(f_data['displayDOB'], "D/M/YYYY").format("M/D/YYYY"),
        f_data['age']
    )
    fighter_data['nick'] = ' "{}"'.format(f_data['nickname']) if f_data.get('nickname') else ""
    fighter_data['stance'] = f_data['stance']['text']
    fighter_data['cstatline'] = "{}: {} | {}: {} | {}: {}".format(
        bold(f_data['statsSummary']['statistics'][0]['abbreviation']),
        f_data['statsSummary']['statistics'][0]['displayValue'],
        bold(f_data['statsSummary']['statistics'][1]['abbreviation']),
        f_data['statsSummary']['statistics'][1]['displayValue'],
        bold(f_data['statsSummary']['statistics'][2]['abbreviation']),
        f_data['statsSummary']['statistics'][2]['displayValue'],
    )

    overview = None
    try:
        overview = requests.get(fighter_bio_url.format(fighter_id=fighter_data['id']) + "/overview").json()
    except:
        pass

    news = None
    try:
        news = requests.get(fighter_news_url.format(player_id=f_data['guid']))
        LOGGER.debug(news.url)
        news = news.json()
    except Exception as e:
        LOGGER.error(e)
        pass

    upcoming = {}
    if overview:
        if overview.get("upcomingFight"):
            up_data = overview['upcomingFight']
            if up_data['league']['events'][0]['status'] == 'pre':
                upcoming['name'] = up_data['league']['events'][0]['name']
                upcoming['when'] = pendulum.parse(up_data['league']['events'][0]['date']).in_tz("US/Eastern").format('MMM Do h:mm A zz')
                try:
                    upcoming['desc'] = up_data['league']['events'][0]['types'][0]['text']
                except:
                    upcoming['desc'] = up_data['league']['events'][0]['type']['text']
                for comp in up_data['competitors']:
                    if fighter_data['id'] != comp['id']:
                        upcoming['vs'] = "{} ({})".format(
                            comp['displayName'], comp['record']
                        )
                        break

    append_news = []
    if news:
        if news['resultsCount'] > 0:
            for item in news['feed']:
                tmp = {}
                if item.get('byline'):
                    tmp['byline'] = "[{}]".format(item['byline'])
                else:
                    tmp['byline'] = "[ESPN]"
                tmp['headline'] = "{}".format(item['headline'])
                tmp['date'] = "{}".format(
                    pendulum.parse(item['published'], strict=False).format("MMM Do h:mm A")
                )
                tmp['link'] = "{}".format(item['links']['web']['short']['href'])
                append_news.append(tmp)


    lines = []
    lines.append(
        "{}{} {}{} - {}".format(
            bold(fighter_data['name']),
            fighter_data['nick'],
            fighter_data['flag'],
            fighter_data['division'],
            fighter_data['team']
        )
    )
    lines.append(
        "{} | DOB: {} | {} Stance".format(
            fighter_data['ht/wt/rch'],
            fighter_data['dob/age'],
            fighter_data['stance']
        )
    )
    lines.append(
        "[{}] {}".format(
            "Career Stats",
            fighter_data['cstatline']
        )
    )
    if upcoming:
        lines.append(
            "[Next Fight] {name} ({when}) - {desc} - vs {vs}".format(**upcoming)
        )

    if append_news:
        for item in append_news:
            lines.append(
                "\x02{byline}\x02 {date} - \x02{headline}\x02 - {link}".format(**item)
            )

    for line in lines:
        bot.write(['PRIVMSG', trigger.sender], line)

    return


@module.commands("ufc", "mma")
@module.example(".mma --prelim --search ufc249")
def fight(bot, trigger):
    """Fetches UFC/MMA fight event information
    By default, with no parameters, will fetch the next or in-progress event.
    
    Use --search text/"text to search"  to find a specific event.
    Use --prelim                        to fetch the preliminary card if there is one.
    Use --prev                          to find the previous completed event.
    Use --schedule/sched                to fetch the next 5 events.
    Use --date YYYYMMDD                 to fetch events on a specific date.
    """
    options = parseargs(trigger.group(2))
    try:
        schedule = requests.get(schedule_url + "&league=ufc" if 'ufc' in trigger.group(1).lower() else schedule_url)
        schedule = schedule.json()
    except:
        return bot.say("I couldn't fetch the schedule")

    pv_fight = options.get('--prev') or False
    if any(key.startswith('--prelim') for key in options):
        card_type = options.get('--prelim') or options.get('--prelims')
    elif any(key.startswith('--fullcard') for key in options):
        card_type = 'all'
    else:
        card_type = 'main'
    if card_type == 'early':
        card_type = 'prelims2'
    elif card_type == True:
        card_type = 'prelims1'
    search = True if options.get('--search') else False
    search_string = options.get('--search')
    date_search = options.get('--date', '')
    
    if options.get('--utc'):
        zone = "UTC"
    else:
        zone = options.get('--tz') or None
        if zone == True:
            zone = "US/Eastern"
        channel_or_nick = tools.Identifier(trigger.nick)
        zone = zone or get_nick_timezone(bot.db, channel_or_nick)
        if not zone:
            channel_or_nick = tools.Identifier(trigger.sender)
            zone = get_channel_timezone(bot.db, channel_or_nick)

    if not zone:
        zone = "US/Eastern"


    event_blacklist = [
        "401210113",
        "401223006",
        "401210554",
        "401223027",
        "401223444",
        "600002600",
        "600004344",
        "600004560",
    ]

    now = pendulum.now()
    inp_fut = []
    previous = []
    date_event = []
    for date,event in schedule['events'].items():
        for ev in event:
            if not ev['completed'] and ev['status']['detail'] not in ['Canceled', 'Postponed']:
                if 'Bellator 238' in ev['name'] or ev['id'] in event_blacklist:
                    continue
                inp_fut.append(ev)
            if ev['completed'] and ev['status']['detail'] not in ['Canceled', 'Postponed']:
                previous.append(ev)
        if date == date_search:
            for ev in event:
                date_event.append(ev)

    if date_event:
        events = {
            "curr": date_event,
            "prev": []
        }
    else:
        events = {
            "curr": inp_fut,
            "prev": previous[::-1],
        }

    if options.get('--sched') or options.get('--schedule'):
        schd = []
        for sched_event in inp_fut[:5]:
            venue = ""
            if sched_event.get('venue'):
                venue = " - {}".format(sched_event['venue']['fullName'])
                if sched_event['venue']['address'].get('state'):
                    venue += " - {}, {}".format(
                        sched_event['venue']['address']['city'],
                        sched_event['venue']['address']['state'],
                    )
                else:
                    venue += " - {}, {}".format(
                        sched_event['venue']['address']['city'],
                        sched_event['venue']['address']['country'],
                    )
            schd.append(
                "{} - {}{}".format(
                    bold(sched_event['name']),
                    pendulum.parse(sched_event['date']).in_tz(zone).format('MMM Do h:mm A zz'),
                    "{}".format(venue)
                )
            )
        for line in schd:
            bot.say(line)
        return

    if not events['curr']:
        if not events['prev']:
            return bot.say("I couldn't find any past, current, or future events!")
        else:
            event_id = [events['prev'][0]['id']]
    else:
        if len(events['curr']) > 1:
            event_id = [events['curr'][0]['id']]
            date1 = pendulum.parse(events['curr'][0]['date'], strict=False)
            for ev in events['curr'][1:]:
                tmp_date = pendulum.parse(ev['date'], strict=False)
                if date1.is_same_day(tmp_date):
                    event_id.append(ev['id'])
        else:
            event_id = [events['curr'][0]['id']]

    if pv_fight:
        event_id = [events['prev'][0]['id']]

    if search:
        all_events = previous + inp_fut
        for event in all_events:
            tmp_name = event['name'].lower().replace(" ", "")
            if search_string.lower().replace(" ", "") in tmp_name:
                event_id = [event['id']]
                break


    for id_ in event_id:
        try:
            data = requests.get(event_url.format(event_id=id_))
            data = data.json()
        except:
            return bot.say("I couldn't fetch current event JSON")

        event_name = data['event']['name']
        event_time = pendulum.parse(data['event']['date']).in_tz(zone)
        event_loc = " - {}".format(data['venue']['displayNameLocation']) if \
            data.get('venue') else ""

        strings = []
        strings.append(f"\x02{event_name}\x02 - {event_time.format('MMM Do h:mm A zz')}{event_loc}")

        card_names = {
            'main':     "-- Main Card --",
            'prelims1': "-- Prelims --",
            'prelims2': "-- Early Prelims --"
        }

        if data.get('cards'):
            if card_type == 'all':
                cards = ['prelims2', 'prelims1', 'main']
            else:
                cards = [card_type]
            for card in cards:
                if not data['cards'].get(card):
                    continue
                decisions = []
                divisions = []
                left_strings = []
                right_strings = []
                strings.append(card_names.get(card, "-- Unknown --"))
                if pv_fight or data['cards'][card]['competitions'][0]['status']['type']['completed']:
                    # fight over
                    fights = data['cards'][card]['competitions'][::-1]
                    for fight in fights:
                        left_fighter = {}
                        right_fighter = {}
                        flg_code = None
                        for fighter in fight['competitors']:
                            if fighter['order'] == 1:
                                left_fighter['name'] = bold(fighter['athlete']['displayName']) if fighter['winner'] else fighter['athlete']['displayName']
                                left_fighter['winner_or_loser'] = color("W", 'green') if fighter['winner'] else color("L", 'red')
                                flg_code = None
                                if "TBA" not in left_fighter['name']:
                                    try:
                                        if len(fighter['athlete']['flag']['alt']) > 3:
                                            for country in countries:
                                                if fighter['athlete']['flag']['alt'] == country['name']:
                                                    flg_code = country['alpha-2']
                                                    break
                                        else:
                                            flg_code = fighter['athlete']['flag']['alt'][:2]
                                        if not flg_code:
                                            flg_code = fighter['athlete']['flag']['alt'][:2]

                                        try:
                                            if flg_code.lower() == "en":
                                                left_fighter['flag'] = "\x02🏴󠁧󠁢󠁥󠁮󠁧󠁿\x02"
                                            else:
                                                left_fighter['flag'] = "{}".format(flag.flag(flg_code))
                                        except:
                                            if flg_code.lower() == "en":
                                                left_fighter['flag'] = "\x02🏴󠁧󠁢󠁥󠁮󠁧󠁿\x02"
                                            else:
                                                left_fighter['flag'] = fighter['athlete']['flag']['alt']
                                    except:
                                        left_fighter['flag'] = ""
                                else:
                                    left_fighter['flag'] = "🏳️"
                                left_fighter['record'] = fighter.get('displayRecord', "-")

                            else:
                                right_fighter['name'] = bold(fighter['athlete']['displayName']) if fighter['winner'] else fighter['athlete']['displayName']
                                right_fighter['winner_or_loser'] = color("W", 'green') if fighter['winner'] else color("L", 'red')
                                flg_code = None
                                if "TBA" not in right_fighter['name']:
                                    try:
                                        if len(fighter['athlete']['flag']['alt']) > 3:
                                            for country in countries:
                                                if fighter['athlete']['flag']['alt'] == country['name']:
                                                    flg_code = country['alpha-2']
                                                    break
                                        else:
                                            flg_code = fighter['athlete']['flag']['alt'][:2]
                                        if not flg_code:
                                            flg_code = fighter['athlete']['flag']['alt'][:2]

                                        try:
                                            if flg_code.lower() == "en":
                                                right_fighter['flag'] = "\x02🏴󠁧󠁢󠁥󠁮󠁧󠁿\x02"
                                            else:
                                                right_fighter['flag'] = "{}".format(flag.flag(flg_code))
                                        except:
                                            if flg_code.lower() == "en":
                                                right_fighter['flag'] = "\x02🏴󠁧󠁢󠁥󠁮󠁧󠁿\x02"
                                            else:
                                                right_fighter['flag'] = fighter['athlete']['flag']['alt']
                                    except:
                                        right_fighter['flag'] = ""
                                else:
                                    right_fighter['flag'] = "🏳️"
                                right_fighter['record'] = fighter.get('displayRecord', "-")
                        left_string = "[{}] {} {} ({})".format(
                            left_fighter['winner_or_loser'],
                            left_fighter['name'],
                            left_fighter['flag'],
                            left_fighter['record'],
                        )
                        right_string = "[{}] {} {} ({})".format(
                            right_fighter['winner_or_loser'],
                            right_fighter['name'],
                            right_fighter['flag'],
                            right_fighter['record'],
                        )
                        left_strings.append(left_string)
                        right_strings.append(right_string)
                        try:
                            decisions.append(
                                " | {} - {} ({}) [R{}, {}]".format(
                                    fight['status']['type']['shortDetail'],
                                    fight['status']['result']['shortDisplayName'],
                                    fight['judgesScores'] if fight.get('judgesScores') else fight['status']['result']['description'],
                                    fight['status']['period'], fight['status']['displayClock']
                                )
                            )
                        except:
                            pass
                        divisions.append(
                            " | {}".format(
                                fight['note']
                            ) if fight.get('note') else ""
                        )
                else:
                    # fight not over
                    fights = data['cards'][card]['competitions'][::-1]
                    for fight in fights:
                        left_fighter = {}
                        right_fighter = {}
                        flg_code = None
                        round_status = None
                        for fighter in fight['competitors']:
                            if fighter['order'] == 1:
                                left_fighter['name'] = bold(fighter['athlete']['displayName']) if fighter['winner'] else fighter['athlete']['displayName']
                                if fight['status']['type']['completed']:
                                    left_fighter['winner_or_loser'] = color("W", 'green') if fighter['winner'] else color("L", 'red')
                                else:
                                    left_fighter['winner_or_loser'] = ""
                                if fight.get('status', {}).get('type', {}).get('state', '') != "pre":
                                    round_status = fight.get('status', {}).get('type', {}).get('shortDetail', '')
                                flg_code = None
                                if "TBA" not in left_fighter['name']:
                                    try:
                                        if len(fighter['athlete']['flag']['alt']) > 3:
                                            for country in countries:
                                                if fighter['athlete']['flag']['alt'] == country['name']:
                                                    flg_code = country['alpha-2']
                                                    break
                                        else:
                                            flg_code = fighter['athlete']['flag']['alt'][:2]
                                        if not flg_code:
                                            flg_code = fighter['athlete']['flag']['alt'][:2]

                                        try:
                                            if flg_code.lower() == "en":
                                                left_fighter['flag'] = "\x02🏴󠁧󠁢󠁥󠁮󠁧󠁿\x02"
                                            else:
                                                left_fighter['flag'] = "{}".format(flag.flag(flg_code))
                                        except:
                                            if flg_code.lower() == "en":
                                                left_fighter['flag'] = "\x02🏴󠁧󠁢󠁥󠁮󠁧󠁿\x02"
                                            else:
                                                left_fighter['flag'] = fighter['athlete']['flag']['alt']
                                    except:
                                        left_fighter['flag'] = ""
                                else:
                                    left_fighter['flag'] = "🏳️"
                                left_fighter['record'] = fighter.get('displayRecord', "-")

                            else:
                                right_fighter['name'] = bold(fighter['athlete']['displayName']) if fighter['winner'] else fighter['athlete']['displayName']
                                if fight['status']['type']['completed']:
                                    right_fighter['winner_or_loser'] = color("W", 'green') if fighter['winner'] else color("L", 'red')
                                else:
                                    right_fighter['winner_or_loser'] = ""
                                if fight.get('status', {}).get('type', {}).get('state', '') != "pre":
                                    round_status = fight.get('status', {}).get('type', {}).get('shortDetail', '')
                                flg_code = None
                                if "TBA" not in right_fighter['name']:
                                    try:
                                        if len(fighter['athlete']['flag']['alt']) > 3:
                                            for country in countries:
                                                if fighter['athlete']['flag']['alt'] == country['name']:
                                                    flg_code = country['alpha-2']
                                                    break
                                        else:
                                            flg_code = fighter['athlete']['flag']['alt'][:2]
                                        if not flg_code:
                                            flg_code = fighter['athlete']['flag']['alt'][:2]

                                        try:
                                            if flg_code.lower() == "en":
                                                right_fighter['flag'] = "\x02🏴󠁧󠁢󠁥󠁮󠁧󠁿\x02"
                                            else:
                                                right_fighter['flag'] = "{}".format(flag.flag(flg_code))
                                        except:
                                            if flg_code.lower() == "en":
                                                right_fighter['flag'] = "\x02🏴󠁧󠁢󠁥󠁮󠁧󠁿\x02"
                                            else:
                                                right_fighter['flag'] = fighter['athlete']['flag']['alt']
                                    except:
                                        right_fighter['flag'] = ""
                                else:
                                    right_fighter['flag'] = "🏳️"
                                right_fighter['record'] = fighter.get('displayRecord', "-") 
                        left_string = "{}{} {} ({})".format(
                            "{}".format('[' + left_fighter['winner_or_loser'] + '] ' if left_fighter['winner_or_loser'] else ''),
                            left_fighter['name'],
                            left_fighter['flag'],
                            left_fighter['record'],
                        )
                        right_string = "{}{} {} ({})".format(
                            "{}".format('[' + right_fighter['winner_or_loser'] + '] ' if right_fighter['winner_or_loser'] else ''),
                            right_fighter['name'],
                            right_fighter['flag'],
                            right_fighter['record'],
                        )
                        left_strings.append(left_string)
                        right_strings.append(right_string)
                        try:
                            decisions.append(
                                " | {} - {} ({}) [R{}, {}]".format(
                                    fight['status']['type']['shortDetail'],
                                    fight['status']['result']['shortDisplayName'],
                                    fight['judgesScores'] if fight.get('judgesScores') else fight['status']['result']['description'],
                                    fight['status']['period'], fight['status']['displayClock']
                                )
                            )
                        except:
                            if round_status:
                                decisions.append(
                                    " | {} {}".format(
                                        bold(color("LIVE", colors.GREEN)),
                                        round_status)
                                )
                            else:
                                pass
                        divisions.append(
                            " | {}".format(
                                fight['note']
                            ) if fight.get('note') else ""
                        )

                replies = []
                l_padding = 0
                r_padding = 0
                for string in left_strings:
                    if len(_stripFormatting(string)) >= l_padding:
                        l_padding = len(string)
                for string in right_strings:
                    if len(_stripFormatting(string)) >= r_padding:
                        r_padding = len(string)

                l_padding += 6
                r_padding += 6

                for idx, string in enumerate(left_strings):
                    if "[" not in string:
                        ppad = 6
                    else:
                        ppad = 2

                    try:
                        dec = decisions[idx]
                    except:
                        dec = ""

                    strings.append(
                        "{:{l_padding}} vs {:{r_padding}}{}{}".format(
                            left_strings[idx], right_strings[idx], dec, divisions[idx] if divisions else "",
                            l_padding=l_padding if "\x02" in left_strings[idx] else l_padding-ppad,
                            r_padding=r_padding if "\x02" in right_strings[idx] else r_padding-ppad
                        )
                    )
                
            for string in strings:
                bot.write(['PRIVMSG', trigger.sender], string)
    return

@module.commands("brittney", "britt", "brit", "bp")
def bp(bot, trigger):
    """Thank you Brittney"""
    return bot.say("Thank you Brittney")

def _stripBold(s):
    """Returns the string s, with bold removed."""
    return s.replace('\x02', '')

def _stripItalic(s):
    """Returns the string s, with italics removed."""
    return s.replace('\x1d', '')

_stripColorRe = re.compile(r'\x03(?:\d{1,2},\d{1,2}|\d{1,2}|,\d{1,2}|)')
def _stripColor(s):
    """Returns the string s, with color removed."""
    return _stripColorRe.sub('', s)

def _stripReverse(s):
    """Returns the string s, with reverse-video removed."""
    return s.replace('\x16', '')

def _stripUnderline(s):
    """Returns the string s, with underlining removed."""
    return s.replace('\x1f', '')

def _stripFormatting(s):
    """Returns the string s, with all formatting removed."""
    # stripColor has to go first because of some strings, check the tests.
    s = _stripColor(s)
    s = _stripBold(s)
    s = _stripReverse(s)
    s = _stripUnderline(s)
    s = _stripItalic(s)
    return s.replace('\x0f', '')
