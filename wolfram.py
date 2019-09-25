import sopel.module
from sopel.formatting import *
from sopel.config.types import StaticSection, ValidatedAttribute

import requests
import urllib.parse
import shlex

class APIKey(StaticSection):
    api_key = ValidatedAttribute('api_key', str)

def setup(bot):
    bot.config.define_section('wolfram', APIKey)

def configure(config):
    config.define_section('wolfram', APIKey, validate=False)
    config.wolfram.configure_setting('api_key',
                                     'Wolfram Alpha API Key')


@sopel.module.commands('wolfram', 'wa')
@sopel.module.example('.wa tallest building in the world')
def wolfram(bot, trigger):
    """Query the Wolfram Alpha API. Use --full (or -f) in your query to show how the API is interpreting your input."""
    api_key = bot.config.wolfram.api_key
    if api_key == "Wolfram Alpha API Key":
        return bot.say("I need a proper Wolfram Alpha API key to work")
    user_input = trigger.group(2)
    if not user_input:
        return bot.reply("Uhhh... what do you want me to lookup?")
    try:
        args = user_input.split()
    except:
        return bot.reply("Check your input")
    show_full = False
    options = ["--full", "-f"]
    for idx,arg in enumerate(args):
        if arg in options:
            show_full = True
            args.pop(idx)
    user_input = " ".join(args)
    user_input = urllib.parse.quote(user_input)
    api_url = f"https://api.wolframalpha.com/v2/query?appid={api_key}&input={user_input}&format=plaintext&output=json&location=New%20York"
    print("[Wolfram] URL >> " + api_url)

    try:
        data = requests.get(api_url).json()
    except:
        return bot.say("Something went wrong querying Wolfram Alpha!")
    
    if not data:
        return bot.say("Something went wrong querying Wolfram Alpha!")

    if data["queryresult"]["error"]:
        return bot.say("Something went wrong querying Wolfram Alpha!")
    elif not data["queryresult"]["success"]:
        return bot.reply("Wolfram API failed to parse your query")

    try:
        results = data["queryresult"]["pods"]   
    except:
        return bot.say("Something went wrong parsing data")

    interp = None
    result = None
    rank = 100000
    for pod in results:
        if not pod.get("id"):
            continue
        else:
            if pod["id"] == "Input":
                interp = pod
            elif pod.get("primary"):
                if pod["position"] < rank:
                    result = pod
                    rank = pod["position"]

    if not result:
        return bot.reply(f"I couldn't find an answer for your query! ({interp['subpods'][0]['plaintext']})")

    tmp = []
    for t in result['subpods']:
        t['plaintext'] = t['plaintext'].replace("\n", " $%$ ")
        if "|" in t['plaintext']:
            pipes = t['plaintext'].split()
            for idx,word in enumerate(pipes):
                if word == "|":
                    pipes[idx-1] = bold("({})".format(pipes[idx-1]))
                    pipes.pop(idx)
            tmp.append(" ".join(pipes).replace("$%$", "|"))
        else:
            tmp.append(t['plaintext'].replace("$%$", "|"))

    if show_full:
        bot.say(f"{bold(interp['title'])}: {interp['subpods'][0]['plaintext']}")
    output = f"{bold(result['title'])}: {' | '.join(tmp)}"
    bot.say(output, max_messages=2)
