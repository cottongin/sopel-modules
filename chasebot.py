# coding=utf-8

from __future__ import absolute_import, division, generator_stop, print_function, unicode_literals

import html
import json
from pathlib import Path
import traceback

import pendulum
import requests
from sopel_sopel_plugin_argparser import parseargs
import twython

from sopel import plugin, tools
from sopel.config.types import ListAttribute, StaticSection, ValidatedAttribute
# from sopel.formatting import color, bold
# from sopel.tools.time import (
#     format_time,
#     get_channel_timezone,
#     get_nick_timezone,
#     get_timezone,
#     validate_timezone
# )


sopel_instance = None
LOGGER = tools.get_logger("chasebot")

CHANNELS = ["#Chases", "#𝓉𝓌𝑒𝓇𝓀𝒾𝓃"]
FOLLOW_LIST = [
    '108746627',            # @PCALive
    '37162208',             # @LAPolicePursuit
    '768202337764597760',   # @ChaseAlertsOnly
    '3259117872',           # @LACoScanner
    '162814209',            # @Stu_Mundel
    '277899934',            # @damonheller (smokenscan)
    '34743251',             # @SpaceX
    '44196397',             # @elonmusk
    '1071963556567048192',  # @efnetchasebot
]

APP_PREFIX = "\x02[ChaseApp]\x02 "
BOT_PREFIX = "\x02[ChaseBot]\x02 "

APP_STORE_LINKS = [
    {"os": "Android", "url": "https://play.google.com/store/apps/details?id=com.carverauto.chaseapp"}
]

CHASES = {}


class ChaseAppSection(StaticSection):
    chaseapp_api_url = ValidatedAttribute("chaseapp_api_url", str)
    chaseapp_api_key = ValidatedAttribute("chaseapp_api_key", str)
    chaseapp_mods = ListAttribute("chaseapp_mods")
    twitter_consumer_token = ValidatedAttribute("twitter_consumer_token", str)
    twitter_consumer_secret = ValidatedAttribute("twitter_consumer_secret", str)
    twitter_access_token = ValidatedAttribute("twitter_access_token", str)
    twitter_access_secret = ValidatedAttribute("twitter_access_secret", str)
    pushover_token = ValidatedAttribute("pushover_token", str)
    pushover_user = ValidatedAttribute("pushover_user", str)


class MyStreamer(twython.TwythonStreamer):
    global CHANNELS
    global CHASES
    global sopel_instance

    def on_success(self, status):
        try:
            if not status.get('in_reply_to_status_id') and not status.get('in_reply_to_user_id_str'):
                if not status.get('retweeted') and 'RT @' not in status.get('text', ''):
                    if not status.get('user'):
                        pass
                    text = "\x02@{}\x02 ({}): {}".format(
                        status['user']['screen_name'],
                        status['user']['name'],
                        status.get('extended_tweet', {}).get('full_text') or status['text']
                    )
                    urls = status['entities'].get('urls')
                    try:
                        if status.get('quoted_status'):
                            text += " (\x02@{}\x02: {} - {})".format(
                                status['quoted_status']['user']['screen_name'],
                                status['quoted_status']['text'],
                                status['quoted_status_permalink'].get('url'),
                            )
                            urls = status['quoted_status']['entities'].get('urls')
                    except Exception as e:
                        LOGGER.error(f"Error parsing quoted status: {e}")

                    text = text.replace('\n', ' ')
                    text = text.strip()
                    text = html.unescape(text)

                    LOGGER.info(f"New Tweet! - {text}")

                    valid_tweets = ["chase", "pursuit"]
                    found_valid = True
                    if status['user']['id'] == 277899934:
                        found_valid = False
                        for word in valid_tweets:
                            if word in text.lower():
                                found_valid = True
                                break
                    if found_valid:
                        if status['user']['id'] == 3259117872:
                            if "ready?" in text.lower():

                                if not CHASES.get('current'):
                                    CHASES['current'] = {
                                        'active': True,
                                        'time': status['created_at']
                                    }
                                else:
                                    now = pendulum.now()
                                    if now.diff(pendulum.parse(CHASES['current']['time'], strict=False)).in_hours() >= 6:
                                        CHASES['current'] = {
                                            'active': True,
                                            'time': status['created_at']
                                        }
                        if status['user']['id'] not in FOLLOW_LIST[6:]:
                            chase = False
                            for word in valid_tweets:
                                if word in text.lower():
                                    chase = True
                            if CHASES.get('current', {}).get('active'):
                                if urls and chase:
                                    url = urls[0]['url']
                                    url = requests.get(url).url
                                    CHASES['current']['url'] = url
                                    CHASES['current']['name'] = "Chase"
                                    CHASES['current']['desc'] = text
                                    CHASES['current']['network'] = "TBD"
                                    CHASES['current']['first_run'] = True
                                if CHASES['current'].get('first_run'):
                                    headers = {
                                        'User-Agent': 'chasebot@efnet (via twitter) v1.0',
                                        'From': 'chasebot@cottongin.xyz',
                                        'X-ApiKey': sopel_instance.config.chaseapp.chaseapp_api_key
                                    }

                                    payload = {
                                        "name": CHASES['current']['name'],
                                        "url": CHASES['current']['url'],
                                        "desc": CHASES['current']['desc'],
                                        "URLs": [
                                            {"network": CHASES['current']['network'], "url": ""}
                                        ],
                                        "live": True
                                    }

                                    api_endpoint = sopel_instance.config.chaseapp.chaseapp_api_url + "/AddChase"

                                    data = requests.post(api_endpoint, headers=headers, json=payload)

                                    CHASES['current']['id'] = data.text
                                    LOGGER.info("UUID created for a new chase: {}".format(data.text))
                                    CHASES['current']['first_run'] = False

                        for channel in CHANNELS:
                            sopel_instance.say(text, channel)
        except Exception as e:
            LOGGER.error(f"Unhandled Tweet! - {e}")
            result = traceback.format_exc()
            result = "".join(result)
            if len(result) > 1024:
                result = result[-1024:]
            post_data = {
                'token': sopel_instance.config.chaseapp.pushover_token,
                'user': sopel_instance.config.chaseapp.pushover_user,
                'message': result,
                'title': 'Chasebot is BROKEN - Unhandled'
            }
            requests.post("https://api.pushover.net/1/messages.json", data=post_data)

    def on_error(self, status_code, data):
        LOGGER.error(f"Twitter ERROR: {status_code}")
        if len(data) > 1024:
            result = data[-1024:]
        post_data = {
            'token': sopel_instance.config.chaseapp.pushover_token,
            'user': sopel_instance.config.chaseapp.pushover_user,
            'message': result,
            'title': f'Chasebot is BROKEN - Twitter ({status_code})'
        }
        requests.post("https://api.pushover.net/1/messages.json", data=post_data)


api = None
myStream = None
myStreamListener = None
firstStart = True


def configure(config):
    config.define_section("chaseapp", ChaseAppSection, validate=False)
    config.chaseapp.configure_setting("chaseapp_api_url", "Root path of API service")
    config.chaseapp.configure_setting("chaseapp_api_key", "API key for ChaseApp")
    config.chaseapp.configure_setting("chaseapp_mods", "List of authorized users for sensitive commands")
    config.chaseapp.configure_setting("twitter_consumer_token", "Twitter API Consumer Token")
    config.chaseapp.configure_setting("twitter_consumer_secret", "Twitter API Consumer Secret")
    config.chaseapp.configure_setting("twitter_access_token", "Twitter API Access Token")
    config.chaseapp.configure_setting("twitter_access_secret", "Twitter API Access Token")
    config.chaseapp.configure_setting("pushover_token", "Pushover API Token")
    config.chaseapp.configure_setting("pushover_user", "Pushover API User Hash")


def setup(bot):
    bot.config.define_section("chaseapp", ChaseAppSection)
    global CHASES
    if not CHASES:
        try:
            with open(str(Path.home()) + '/chases_db.json', 'r') as handle:
                b = json.load(handle)
            CHASES = b
        except Exception as e:
            LOGGER.debug(e)
            pass


def shutdown(bot):
    try:
        with open(str(Path.home()) + '/chases_db.json', 'w') as handle:
            json.dump(CHASES, handle)
    except Exception as e:
        LOGGER.debug(e)
        pass


@plugin.interval(10)
@plugin.thread(True)
@plugin.output_prefix(BOT_PREFIX)
def twitter_thread(bot):
    global firstStart
    if not firstStart:
        return

    global sopel_instance
    global api
    global myStream
    global myStreamListener
    sopel_instance = bot

    LOGGER.info(f"{BOT_PREFIX} Started for channels: {', '.join(CHANNELS)}")
    firstStart = False

    consumer_token = bot.config.chaseapp.twitter_consumer_token
    consumer_secret = bot.config.chaseapp.twitter_consumer_secret
    access_token = bot.config.chaseapp.twitter_access_token
    access_token_secret = bot.config.chaseapp.twitter_access_secret

    # Authenticate to Twitter
    stream = MyStreamer(consumer_token, consumer_secret,
                        access_token, access_token_secret)

    try:
        twitter = twython.Twython(consumer_token, consumer_secret, oauth_version=2)
        api_token = twitter.obtain_access_token()
        api = twython.Twython(consumer_token, access_token=api_token)
    except Exception as e:
        LOGGER.error(f"I couldn't authorize with twitter (regular API): {e}")

    try:
        stream.statuses.filter(follow=FOLLOW_LIST)
    except Exception as e:
        stream.disconnect()
        LOGGER.error(f"{BOT_PREFIX} - Twiter Stream Error. Restarting. \n{e}")
        firstStart = True

    LOGGER.info(f"{BOT_PREFIX} Stopped")
    stream.disconnect()
    firstStart = True


@plugin.command('applinks', 'applink', 'app')
@plugin.example('.applinks')
@plugin.output_prefix(APP_PREFIX)
def send_links(bot, trigger):
    """Send links to the ChaseApp store pages"""
    return bot.say("Download ChaseApp here: {}".format(
        " | ".join("{}: {}".format(link['os'], link['url']) for link in APP_STORE_LINKS)
    ))


@plugin.command('listchases', 'list', 'lc', 'chases')
@plugin.example('.listchases')
@plugin.output_prefix(APP_PREFIX)
def list_chases(bot, trigger):
    """List active chases"""

    show_id = False
    list_live = False

    index = -1
    if trigger.group(2):
        args = parseargs(trigger.group(2))
        index = int(args.get('--index', 1)) * -1
        show_id = args.get('--showid')
        list_live = args.get('--showlive')

    headers = {
        'User-Agent': 'chasebot@efnet ({}) v1.0'.format(trigger.nick),
        'From': 'chasebot@cottongin.xyz'
    }

    api_endpoint = bot.config.chaseapp.chaseapp_api_url + "/ListChases"

    data = requests.get(api_endpoint, headers=headers).json()
    sorted_chases = sorted(data, key=lambda i: i['CreatedAt'])
    if list_live:
        sorted_chases = [chase for chase in sorted_chases if chase.get('Live')]
    else:
        sorted_chases = [sorted_chases[index]]

    if not sorted_chases:
        return bot.say("No chases found :(")

    for chase in sorted_chases:
        bot.say("({recent}{date}) \x02{name} - {desc}\x02 | {status} | {votes} votes".format(
            recent="\x1FMost Recent\x0F - " if chase == sorted_chases[-1] else "",
            name=chase['Name'],
            desc=chase['Desc'],
            date=pendulum.parse(chase['CreatedAt']).in_tz('US/Pacific').format("MM/DD/YYYY h:mm A zz"),
            votes=chase['Votes'],
            status="\x02\x0309LIVE\x03\x02" if chase['Live'] else "\x0304Inactive\x03",
        ))

        if chase['URL']:
            links = []
            links.append("(Primary) {}".format(chase['URL']))
            if chase['URLs']:
                for thing in chase['URLs']:
                    if thing.get('Network') and thing.get('URL'):
                        links.append("({}) {}".format(thing.get('Network'), thing.get('URL')))
            for link in links:
                bot.say(link)

        if show_id:
            bot.say(f"(ID) {chase['ID']}")


@plugin.command('updatechase', 'update', 'uc')
@plugin.example('.updatechase')
@plugin.output_prefix(APP_PREFIX)
def update_chase(bot, trigger):
    """Update chases"""

    check = trigger.hostmask.split("!")[1]
    if check not in bot.config.chaseapp.chaseapp_mods:
        LOGGER.error("{} tried to update a chase".format(trigger.hostmask))
        return bot.reply("You're not authorized to do that!")

    if not trigger.group(2):
        return bot.reply("I need some info to update")

    args = parseargs(trigger.group(2))
    if not args:
        return bot.reply("Something went wrong parsing your input")

    if not (args.get('--id') or args.get('--last')):
        return bot.reply("I need a chase ID to reference")
    if not any(elem in args for elem in ('--name', '--desc', '--url', '--network', '--live', '--urls')):
        return bot.reply("Your input was missing some required information")

    headers = {
        'User-Agent': 'chasebot@efnet ({}) v1.0'.format(trigger.nick),
        'From': 'chasebot@cottongin.xyz',
        'X-ApiKey': bot.config.chaseapp.chaseapp_api_key
    }

    if not args.get('--id'):
        api_endpoint = bot.config.chaseapp.chaseapp_api_url + "/ListChases"
        data = requests.get(api_endpoint, headers=headers).json()
        sorted_chases = sorted(data, key=lambda i: i['CreatedAt'])
        update_id = sorted_chases[-1]['ID']
    else:
        update_id = args.get('--id')

    payload = {}
    for arg, value in args.items():
        if arg in ["extra_text", '--id', '--last']:
            continue
        elif arg == '--live':
            if value.lower() == 'false':
                value = False
            else:
                value = True
        elif arg == '--urls':
            try:
                json_data = json.loads(value.replace("'", '"'))
            except Exception as e:
                LOGGER.error(e)
                return bot.reply("Your syntax for --urls must be valid json")
            value = json_data
        payload[arg.replace('--', '')] = value
    payload['id'] = update_id

    api_endpoint = bot.config.chaseapp.chaseapp_api_url + "/UpdateChase"

    data = requests.post(api_endpoint, headers=headers, json=payload)
    if data.status_code != 200:
        return bot.say("Something went wrong")
    bot.say("Successfully Updated ({} - {})".format(data.status_code, update_id))


@plugin.command('addchase', 'add', 'ac')
@plugin.example('.addchase')
@plugin.output_prefix(APP_PREFIX)
def add_chase(bot, trigger):
    """Add a chase"""

    check = trigger.hostmask.split("!")[1]
    if check not in bot.config.chaseapp.chaseapp_mods:
        LOGGER.error("{} tried to add a chase".format(trigger.hostmask))
        return bot.reply("You're not authorized to do that!")

    if not trigger.group(2):
        return bot.reply("I need some info to add")

    args = parseargs(trigger.group(2))
    if not args:
        return bot.reply("Something went wrong parsing your input")

    if not all(elem in args for elem in ('--name', '--desc', '--url', '--live')):
        return bot.reply("Your input was missing some required information")

    headers = {
        'User-Agent': 'chasebot@efnet ({}) v1.0'.format(trigger.nick),
        'From': 'chasebot@cottongin.xyz',
        'X-ApiKey': bot.config.chaseapp.chaseapp_api_key
    }

    if args.get('--network'):
        urls = [
            {"network": args['--network'], "url": args['--url']}
        ]
    else:
        urls = [{}]
    if args.get('--urls'):
        value = args.get('--urls')
        try:
            json_data = json.loads(value.replace("'", '"'))
        except Exception as e:
            LOGGER.error(e)
            return bot.reply("Your syntax for --urls must be valid json")
        urls = json_data
    if args.get('--live'):
        if args['--live'] == 'false':
            args['--live'] = False
        else:
            args['--live'] = True
    payload = {
        "name": args['--name'],
        "url": args['--url'],
        "desc": args['--desc'],
        "URLs": urls,
        "live": args.get('--live')
    }

    api_endpoint = bot.config.chaseapp.chaseapp_api_url + "/AddChase"

    data = requests.post(api_endpoint, headers=headers, json=payload)
    if data.status_code != 200:
        return bot.say("Something went wrong")
    bot.say("Successfully Added ({})".format(data.text))


@plugin.command('deletechase', 'delete', 'dc')
@plugin.example('.deletechase')
@plugin.output_prefix(APP_PREFIX)
def delete_chase(bot, trigger):
    """delete chases"""

    check = trigger.hostmask.split("!")[1]
    if check not in bot.config.chaseapp.chaseapp_mods:
        LOGGER.error("{} tried to delete a chase".format(trigger.hostmask))
        return bot.reply("You're not authorized to do that!")

    if not trigger.group(2):
        return bot.reply("I need a ChaseApp ID or `--last` to delete")

    args = parseargs(trigger.group(2))
    if not args:
        return bot.reply("Something went wrong parsing your input")

    if not (args.get('--id') or args.get('--last')):
        return bot.reply("I need a chase ID to reference (or pass in `--last` to delete the most recent chase)")

    delete_id = args.get('--id')
    if not delete_id:
        headers = {
            'User-Agent': 'chasebot@efnet ({}) v1.0'.format(trigger.nick),
            'From': 'chasebot@cottongin.xyz'
        }

        api_endpoint = bot.config.chaseapp.chaseapp_api_url + "/ListChases"

        data = requests.get(api_endpoint, headers=headers).json()
        sorted_chases = sorted(data, key=lambda i: i['CreatedAt'])
        delete_id = sorted_chases[-1]['ID']

    headers = {
        'User-Agent': 'chasebot@efnet ({}) v1.0'.format(trigger.nick),
        'From': 'chasebot@cottongin.xyz',
        'X-ApiKey': bot.config.chaseapp.chaseapp_api_key
    }

    payload = {
        "id": delete_id
    }

    api_endpoint = bot.config.chaseapp.chaseapp_api_url + "/DeleteChase"

    data = requests.post(api_endpoint, headers=headers, json=payload)
    if data.status_code != 200:
        return bot.say("Something went wrong")
    bot.say("Successfully Deleted ({} - {})".format(data.status_code, delete_id))


@plugin.command('following')
@plugin.example('.following')
@plugin.output_prefix(BOT_PREFIX)
def say_following(bot, trigger):
    """Who am I following?"""
    if not api:
        return
    try:
        users = api.lookup_user(user_id=",".join(FOLLOW_LIST))
        prefix = "I'm following: @{}".format(', @'.join(item.get('screen_name') for item in users))
        return bot.say(prefix)
    except Exception:
        traceback.print_exc()
        return bot.say("Hm, something went wrong!")


@plugin.command('lastseen')
@plugin.example('.lastseen')
@plugin.output_prefix(BOT_PREFIX)
def say_last(bot, trigger):
    """Fetch the last tweet I saw"""
    try:
        twitter_list = api.get_list_statuses(
            owner_screen_name='efnetchasebot',
            slug='last',
            count=1
        )
        last_tweet = twitter_list[0].get('extended_tweet', {}).get('full_text') or twitter_list[0].get('text')
        last_tweet = _sanitize(last_tweet)
        last_tweet_seen = twitter_list[0]['created_at']
        last_tweet_seen = pendulum.parse(last_tweet_seen, strict=False)
        last_tweet_seen = last_tweet_seen.diff_for_humans()
        last_tweet_name = twitter_list[0]['user'].get('screen_name')
        resp = "Last tweet I've seen: ({}) \x02@{}\x02: {}".format(last_tweet_seen, last_tweet_name, last_tweet)
        return bot.say(resp)
    except Exception:
        traceback.print_exc()
        return bot.say('Hm, something went wrong!')


def _sanitize(text):
    text = text.replace('\n', '')
    text = text.strip()
    text = html.unescape(text)
    return text
