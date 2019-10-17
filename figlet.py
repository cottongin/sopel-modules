from sopel import module

from sopel.formatting import *

import subprocess
import random

from pyfiglet import Figlet


def configure(config):
    pass


def setup(bot):
    pass


@module.commands('figlet', 'f')
@module.example('.figlet BIG TEXT')
def figlet(bot, trigger):
    """Sends BIG TEXT"""
    f = Figlet(font='standard')
    for l in f.renderText(trigger.group(2) or "").rsplit("\n"):
        bot.say(l)