import shlex

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
    valid_args = ["--font"]
    text = trigger.group(2)
    if not text:
        return bot.reply("I need something to figlet")
    
    args = {}
    tmp = shlex.split(text)
    for index,word in enumerate(tmp):
        if word in valid_args:
            args[word.replace("--", "")] = tmp[index + 1]
            tmp.pop(index)
            tmp.pop(index)
    text = " ".join(tmp)

    if not args:
        font = 'standard'
    else:
        font = args['font']
    
    try:
        fig = Figlet(font=font)
    except:
        fig = Figlet(font='standard')

    for let in fig.renderText(text.strip() or "").rsplit("\n"):
        if let.strip():
            bot.say(let)