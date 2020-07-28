###
# Adapted from https://github.com/dasu/syrup-sopel-modules/blob/master/twitch.py
###

#As of 09-14-2016, twitch API now requires Client-ID with all requests.  You will need to create one from here: 
# https://www.twitch.tv/settings/connections
# complete twitch.py rewrite coming soon™
import requests
import sopel
import re
from sopel.tools import SopelMemory
from sopel.config.types import StaticSection, ChoiceAttribute, ValidatedAttribute
from sopel.formatting import *
import datetime

# TODO: Make these config options c:
# twitchclientid = "clientIDgoeshere"
# announce_chan = "#pancakes"
# logchannel = "#whateverchannelyouwant" #used for live logging certain issues that plague this module
# streamers = [

# ]
#end config

class TwitchSection(StaticSection):
    client_id = ValidatedAttribute('client_id', default=None)


def configure(config):
    config.define_section('twitch', TwitchSection, validate=False)
    config.twitch.configure_setting('client_id', 'Twitch Client ID')

twitchregex = re.compile('.*https?:\/\/(?:(?:www\.)|(?:go\.))?twitch.tv\/(.*?)\/?(?:(?=[\s|\/])|$)')
mixerregex = re.compile('.*https?:\/\/(?:www\.)?mixer.com\/(.*?)\/?(?:(?=[\s])|$)')
twitchclipsregex = re.compile('.*https?:\/\/clips\.twitch.tv\/(.*?)\/?(?:(?=[\s])|$)')

def setup(bot):
    bot.config.define_section('twitch', TwitchSection)
    if 'url_callbacks' not in bot.memory:
        bot.memory['url_callbacks'] = SopelMemory()
    bot.memory['url_callbacks'][twitchregex] = twitchirc
    bot.memory['url_callbacks'][mixerregex] = mixerirc
    bot.memory['url_callbacks'][twitchclipsregex] = twitchclipsirc

def shutdown(bot):
    del bot.memory['url_callbacks'][twitchregex]
    del bot.memory['url_callbacks'][mixerregex]
    del bot.memory['url_callbacks'][twitchclipsregex]

currently_streaming = {}
currently_ystreaming = {}
tsep = lambda a : "{:,}".format(int(a))

def twitch_api(bot, stream_list):
    """ Returns the result of the http request from Twitch's api """
    twitchclientid = bot.config.twitch.client_id
    return requests.get('https://api.twitch.tv/kraken/streams', params={"channel": ",".join(stream_list)}, headers={"Client-ID": twitchclientid,"Accept":"application/vnd.twitchtv.v5+json"}).json()

def gettwitchuserid(bot, tuser):
    tuser = tuser.strip().lower()
    twitchclientid = bot.config.twitch.client_id
    tuid = requests.get("https://api.twitch.tv/kraken/users?login={}".format(tuser.lower()),headers={"Client-ID":twitchclientid,"Accept":"application/vnd.twitchtv.v5+json"}).json()
    if not tuid['users']:
        return None
    else:
        return [tuid['users'][0]['_id']]

def twitch_generator(streaming):
    for streamer in streaming["streams"]:
        streamer_dict = {}
        streamer_dict["name"] = streamer["channel"]["name"]
        streamer_dict["game"] = streamer["channel"]["game"]
        streamer_dict["status"] = streamer["channel"]["status"]
        streamer_dict["url"] = streamer["channel"]["url"]
        streamer_dict["starttime"] = datetime.datetime.strptime(streamer['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        streamer_dict["viewers"] = streamer["viewers"]
        yield streamer_dict

# @sopel.module.interval(20)
# def monitor_streamers(bot):
#   streaming_names = []
#   try:
#     streaming = twitch_api(streamers)
#   except Exception as  e:
#     return print("There was an error reading twitch API  {0}".format(e))
#   results = []
#   if streaming.get("streams"):
#     twitch_gen = twitch_generator(streaming)
#     for streamer in twitch_gen:
#       if streamer["name"] not in currently_streaming:
#         currently_streaming[streamer["name"]] = streamer["game"], {'cooldown': 0, 'starttime': streamer["starttime"]}
#         results.append("%s just went live playing %s! [%s] (%s - %s viewer%s)" % (streamer["name"],
#                                                                                   streamer["game"],
#                                                                                   streamer["status"],
#                                                                                   streamer["url"],
#                                                                                   tsep(streamer["viewers"]),
#                                                                                   "s" if streamer["viewers"] != 1 else ""))
#       streaming_names.append(streamer["name"])

#   if results:
#     bot.msg(announce_chan, ", ".join(results))

#   # Remove people who stopped streaming
#   for streamer in list(currently_streaming):
#     if streamer not in streaming_names:
#       currently_streaming[streamer][1]['cooldown'] += 10
#     if currently_streaming[streamer][1]['cooldown'] > 130:
#       #bot.msg(logchannel,'{0} was removed from currently_streaming for reaching a cooldown of {1}'.format(streamer,currently_streaming[streamer][1]['cooldown']))
#       del currently_streaming[streamer]

@sopel.module.commands('twitchtv','twitch','tv')
@sopel.module.example('.twitch <twitch user name>')
def streamer_status(bot, trigger):
    streamer_name = trigger.group(2)
    if not streamer_name:
        return bot.say("I need someone to lookup!")
    query = gettwitchuserid(bot, streamer_name)
    if query is None:
        return bot.say("{} isn't currently streaming".format(streamer_name))
    try:
        streaming = twitch_api(bot, query)
    except Exception as  e:
        return print("There was an error reading twitch API  {0}".format(e))
    results = []
    if streaming.get("streams"):
        twitch_gen = twitch_generator(streaming)
        for streamer in twitch_gen:
            results.append(f"{bold(color('[Twitch]', 'purple'))} "
                           f"{streamer['name']} is playing {bold(streamer['game'])} "
                           f"{bold(streamer['status'])} for "
                           f"{tsep(streamer['viewers'])} viewer{'s' if streamer['viewers'] != 1 else ''}"
                           f" | Watch @ {streamer['url']}"
            )
    if results:
        return bot.say(", ".join(results))
    else:
        return bot.say(f"{streamer_name} isn't currently streaming.")

@sopel.module.rule('.*https?:\/\/(?:(?:www\.)|(?:go\.))?twitch.tv\/(.*?)\/?(?:(?=[\s|\/])|$)')
def twitchirc(bot, trigger, match = None):
    match = match or trigger
    streamer_name = match.group(1)
    query = streamers if streamer_name is None else gettwitchuserid(bot, streamer_name)
    try:
        streaming = twitch_api(bot, query)
    except Exception as  e:
        return print("There was an error reading twitch API  {0}".format(e))
    results = []
    if streaming.get("streams"):
        twitch_gen = twitch_generator(streaming)
        for streamer in twitch_gen:
            results.append(f"{bold(color('[Twitch]', 'purple'))} "
                           f"{streamer['name']} is playing {bold(streamer['game'])} "
                           f"{bold(streamer['status'])} for "
                           f"{tsep(streamer['viewers'])} viewer{'s' if streamer['viewers'] != 1 else ''}"
            )
    if results:
        bot.say(", ".join(results))
    else:
        pass

@sopel.module.rule('.*https?:\/\/(?:www\.)?mixer.com\/(.*?)\/?(?:(?=[\s])|$)')
def mixerirc(bot, trigger, match = None):
    match = match or trigger
    streamer_name = match.group(1)
    streaming = requests.get('https://mixer.com/api/v1/channels/{}'.format(streamer_name)).json()
    results = []
    if streaming:
        streamer_name = streaming["token"]
        if streaming.get("type"):
            streamer_game = streaming["type"]["name"]
            streamer_status = streaming["name"]
            streamer_viewers = streaming["viewersCurrent"]
        else:
            streamer_game = "a game"
            streamer_status = streaming["name"]
            streamer_viewers = streaming["viewersCurrent"]

    tag = bold(color("[Mixer]", "blue"))
    results.append("%s %s is playing %s [%s] for %s viewer%s" % (tag, streamer_name,
                                                                 streamer_game,
                                                                 streamer_status,
                                                                 tsep(streamer_viewers),
                                                                 "s" if streamer_viewers != 1 else "" ))
    if results:
        bot.say(", ".join(results))
    else:
        pass

@sopel.module.rule('.*(?:https?:\/\/clips\.twitch.tv\/(.*?)\/?(?:(?=[\s])|$))|.*(?:https?:\/\/(?:www)?\.twitch\.tv\/.*?\/clip\/(.*?)\/?(?:(?=[\s])|$))')
def twitchclipsirc(bot,trigger, match = None):
    twitchclientid = bot.config.twitch.client_id
    match = match or trigger
    slug = match.group(1) or match.group(2)
    clips = requests.get("https://api.twitch.tv/kraken/clips/{}".format(slug), headers={"Client-ID":twitchclientid,"Accept":"application/vnd.twitchtv.v5+json"}).json()
    name = clips['broadcaster']['display_name']
    title = clips['title']
    game = clips['game']
    views = clips['views']
    tag = bold(color("[Twitch]", "purple"))
    bot.say("{} {} [{}] | {} | {} views".format(tag, title, game, name, tsep(views)))

# @sopel.module.commands('debugtv')
# def debug(bot, trigger):
#     bot.msg(logchannel,"currently_streaming: {}".format(", ".join(currently_streaming)))