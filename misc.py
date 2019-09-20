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
    parts = s.decode().split(",")
    output = []
    output.append("🕒 {}, {}".format(parts[0].strip(), parts[1].strip()))
    output.append("👥 {}".format(parts[2].strip()))
    output.append("📈{}".format(",".join(parts[3:])))
    # output.append("🕒 {}".format(parts[0]))
    # output.append("🕒 {}".format(parts[0]))
    out_str = " :: ".join(output)

    return bot.say(out_str)