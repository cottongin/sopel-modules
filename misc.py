from sopel import module

from sopel.formatting import bold, color

import subprocess
import random

from pyfiglet import Figlet


def configure(config):
    pass


def setup(bot):
    pass


@module.commands('source', 'github', 'gh')
@module.example('.source')
def source(bot, trigger):
    """Simply replies with a link to my modules' source"""

    url = "https://github.com/cottongin/sopel-modules"

    return bot.say(f"You can find the source to my custom modules here: {url}")


@module.commands('pick', 'choose', 'p', 'ch')
@module.example('.pick eat, don\'t eat')
def pick(bot, trigger):
    """Returns a random choice from user-provided comma separated list"""
    choices = trigger.group(2)
    if not choices:
        return bot.reply("You gotta give me something to choose from!")
    if "," not in choices:
        if " or " in choices.lower():
            choices = choices.split(" or ")
        else:
            choices = choices.split()
    else:
        choices = choices.split(",")
    if len(choices) == 1:
        return bot.reply("What do you expect from me?")
    elif len(choices) >= 50:
        return bot.reply("Way too many things to choose from, try thinking for yourself!")
    choice = random.choice(choices)
    return bot.reply("{}".format(bold(choice.strip())))


@module.commands('uptime', 'stats')
@module.example('.uptime')
def stats(bot, trigger):
    """Responds with my shell's uptime"""
    s = subprocess.check_output(["uptime"])
    parts = s.decode().split(",")
    output = []
    output.append("🕒 {}, {}".format(parts[0].strip(), parts[1].strip()))
    output.append("👥 {}".format(parts[2].strip()))
    output.append("📈{}".format(",".join(parts[3:])))
    # output.append("🕒 {}".format(parts[0]))
    # output.append("🕒 {}".format(parts[0]))
    out_str = " :: ".join(output)

    return bot.say(out_str)