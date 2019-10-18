from sopel import module

from pyfiglet import Figlet


def configure(config):
    pass


def setup(bot):
    pass


@module.commands('figlet', 'f', 'fig')
@module.example('.figlet BIG TEXT')
@module.rate(user=30, channel=10)
def figlet(bot, trigger):
    """Sends BIG TEXT"""
    fig = Figlet(font='standard')
    for let in fig.renderText(trigger.group(2) or "").rsplit("\n"):
        bot.say(let)