from sopel import module

from sopel.formatting import *

import subprocess


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

@module.commands('uptime', 'stats')
@module.example('.uptime')
def stats(bot, trigger):
    """Responds with my shell's uptime"""
    s = subprocess.check_output(["uptime"])
    return bot.say("🕒 " + str(s.strip().decode()))