import sopel.module
from sopel.formatting import *

import requests

@sopel.module.commands('exchange', 'xe', 'x')
@sopel.module.example('.exchange 20 usd to cad')
def exchange(bot, trigger):
    """Converts first provided currency to second provided currency."""
    user_input = trigger.group(2)
    if not user_input:
        return bot.reply("You need to give me some currencies to convert!")
    
    user_input = user_input.split()
    # print(user_input)
    if not user_input[0].replace(".", "").replace(",", "").isdigit():
        return bot.reply("I'm expecting a number as my first input (e.g. 20 usd to cad)")
    if 2 < len(user_input) < 4: # len(user_input) != 4:
        return bot.reply("I'm expecting your input to be something like: 20 usd to cad")
    try:
        amt = float(user_input[0].replace(",", "."))
    except:
        try:
            amt = float(user_input[0].replace(",", ""))
        except:
            return bot.reply("I couldn't parse your input!")
    base = user_input[1].upper()
    if user_input[2].lower() == "to" or user_input[2].lower() == "in":
        conv = user_input[3].upper()
    else:
        conv = user_input[2].upper()

    b_url = "https://api.exchangeratesapi.io/latest?base={}"
    try:
        data = requests.get(b_url.format(base)).json()
    except:
        return bot.reply("I couldn't fetch data from the exchange API")
    
    if data.get("error"):
        return bot.reply("Error: {}".format(data["error"]))

    if conv not in data["rates"]:
        return bot.reply("Error: I couldn't find {} to convert".format(conv))

    conv_amt = amt * data["rates"][conv]
    conv_amt = "{:.2f}".format(conv_amt)

    bot.say("{:.2f} {} is {} {}".format(
        amt, base,
        bold(conv_amt), bold(conv)
    ))

