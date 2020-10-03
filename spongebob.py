from __future__ import unicode_literals, absolute_import, print_function, division

from sopel.module import commands, rule, priority, thread, example, rate
from sopel.formatting import *
from sopel.config.types import StaticSection, ValidatedAttribute
from sopel.tools import Identifier
from sopel.tools.time import get_timezone, format_time

import re
import time
import base64
import requests
import random

import pendulum
from PIL import Image, ImageDraw, ImageFont

class APIKey(StaticSection):
    linx_pass = ValidatedAttribute('linx_pass', str)
    linx_url = ValidatedAttribute('linx_url', str)
    img_path = ValidatedAttribute('img_path', str)
    font_path = ValidatedAttribute('font_path', str)
    base_image_url = ValidatedAttribute('base_image_url', str)

def configure(config):
    config.define_section('spongebob', APIKey, validate=False)
    config.spongebob.configure_setting('linx_pass', '')
    config.spongebob.configure_setting('linx_url', '')
    config.spongebob.configure_setting('img_path', '')
    config.spongebob.configure_setting('base_image_url', '')
    config.spongebob.configure_setting('font_path', '')

def setup(bot):
    bot.config.define_section('spongebob', APIKey)
    if "spongebob_urls" not in bot.memory:
        bot.memory["spongebob_urls"] = {}

def shutdown(bot):
    for key in ['spongebob_urls']:
        try:
            del bot.memory[key]
        except KeyError:
            pass

# https://i.imgur.com/DvukwQl.png
@rate(user=5)
@commands('katzman', 'katz', 'tk', 'km')
@example('.katzman <nick>')
@example('.katzman haha this is funny')
def katz(bot, trigger):
    """Makes a sPoNgEbOb-sTyLe TeXt (or the last message from a provided nick) meme"""
    # verify input and config options
    img_path = "/home/cottongin/katz.png"
    font_path = bot.config.spongebob.font_path
    base_image_url = "https://i.imgur.com/DvukwQl.png"
    linx_url = bot.config.spongebob.linx_url
    linx_pass = bot.config.spongebob.linx_pass
    if not img_path or not base_image_url:
        return bot.say("You need to set the path and/or URL to the base image in this module's config options.")
    if not linx_url:
        return bot.say("You need to set the linx upload URL in this module's config options.")
    if not linx_pass:
        return bot.say("You need to provide the linx upload password in this module's config options.")
    if not font_path:
        return bot.say("You need to proved the path to the font in this module's config options.")
    if not trigger.group(2):
        return bot.say(base_image_url)
    nick_or_msg = trigger.group(2).strip()
    if nick_or_msg == bot.nick:
        return
    
    if len(nick_or_msg.split()) == 1:
        # we have a single, presumably nick
        # fetch latest message
        nick = nick_or_msg
        timestamp = bot.db.get_nick_value(nick, 'seen_timestamp')
        if timestamp:
            # get the relevant information
            channel = bot.db.get_nick_value(nick, 'seen_channel')
            message = bot.db.get_nick_value(nick, 'seen_message')
            action  = bot.db.get_nick_value(nick, 'seen_action')

            if Identifier(channel) == trigger.sender:
                # match to channel
                if action:
                    msg = nick + " " + message
                else:
                    msg = "<{}> {}".format(nick, message)
            else:
                # TBD
                msg = ""
            # do image stuff
            msg = _crazyCase(msg)
            _do_image_and_url(bot, msg, img_path, font_path, linx_url, linx_pass)
        else:
            bot.say("Sorry, I haven't seen {} around.".format(nick))
    else:
        nick_or_msg = _crazyCase(nick_or_msg)
        _do_image_and_url(bot, nick_or_msg, img_path, font_path, linx_url, linx_pass)

@rate(user=5)
@commands('mb', 'mbl')
@example('.mb <nick>')
@example('.mb haha this is funny')
def mb(bot, trigger):
    """Makes a sPoNgEbOb-sTyLe TeXt (or the last message from a provided nick) meme"""
    # verify input and config options
    img_path = "/home/cottongin/mb.png"
    font_path = bot.config.spongebob.font_path
    base_image_url = "https://img.cottongin.xyz/i/ekh3amcc.png"
    linx_url = bot.config.spongebob.linx_url
    linx_pass = bot.config.spongebob.linx_pass
    if not img_path or not base_image_url:
        return bot.say("You need to set the path and/or URL to the base image in this module's config options.")
    if not linx_url:
        return bot.say("You need to set the linx upload URL in this module's config options.")
    if not linx_pass:
        return bot.say("You need to provide the linx upload password in this module's config options.")
    if not font_path:
        return bot.say("You need to proved the path to the font in this module's config options.")
    if not trigger.group(2):
        return bot.say(base_image_url)
    nick_or_msg = trigger.group(2).strip()
    if nick_or_msg == bot.nick:
        return
    
    if len(nick_or_msg.split()) == 1:
        # we have a single, presumably nick
        # fetch latest message
        nick = nick_or_msg
        timestamp = bot.db.get_nick_value(nick, 'seen_timestamp')
        if timestamp:
            # get the relevant information
            channel = bot.db.get_nick_value(nick, 'seen_channel')
            message = bot.db.get_nick_value(nick, 'seen_message')
            action  = bot.db.get_nick_value(nick, 'seen_action')

            if Identifier(channel) == trigger.sender:
                # match to channel
                if action:
                    msg = nick + " " + message
                else:
                    msg = "<{}> {}".format(nick, message)
            else:
                # TBD
                msg = ""
            # do image stuff
            msg = _crazyCase(msg)
            _do_image_and_url(bot, msg, img_path, font_path, linx_url, linx_pass)
        else:
            bot.say("Sorry, I haven't seen {} around.".format(nick))
    else:
        nick_or_msg = _crazyCase(nick_or_msg)
        _do_image_and_url(bot, nick_or_msg, img_path, font_path, linx_url, linx_pass)


@rate(user=5)
@commands('spongebob', 'sb', 'sbl')
@example('.spongebob <nick>')
@example('.spongebob haha this is funny')
def spongebob(bot, trigger):
    """Makes a sPoNgEbOb TeXt (or the last message from a provided nick) meme"""
    # verify input and config options
    img_path = bot.config.spongebob.img_path
    font_path = bot.config.spongebob.font_path
    base_image_url = bot.config.spongebob.base_image_url
    linx_url = bot.config.spongebob.linx_url
    linx_pass = bot.config.spongebob.linx_pass
    if not img_path or not base_image_url:
        return bot.say("You need to set the path and/or URL to the base image in this module's config options.")
    if not linx_url:
        return bot.say("You need to set the linx upload URL in this module's config options.")
    if not linx_pass:
        return bot.say("You need to provide the linx upload password in this module's config options.")
    if not font_path:
        return bot.say("You need to proved the path to the font in this module's config options.")
    nick_or_msg = trigger.group(2).strip()
    if not nick_or_msg:
        return bot.say(base_image_url)
    if nick_or_msg == bot.nick:
        return
    
    if len(nick_or_msg.split()) == 1:
        # we have a single, presumably nick
        # fetch latest message
        nick = nick_or_msg
        timestamp = bot.db.get_nick_value(nick, 'seen_timestamp')
        if timestamp:
            # get the relevant information
            channel = bot.db.get_nick_value(nick, 'seen_channel')
            message = bot.db.get_nick_value(nick, 'seen_message')
            action  = bot.db.get_nick_value(nick, 'seen_action')

            if Identifier(channel) == trigger.sender:
                # match to channel
                if action:
                    msg = nick + " " + message
                else:
                    msg = "<{}> {}".format(nick, message)
            else:
                # TBD
                msg = ""
            # do image stuff
            msg = _crazyCase(msg)
            _do_image_and_url(bot, msg, img_path, font_path, linx_url, linx_pass)
        else:
            bot.say("Sorry, I haven't seen {} around.".format(nick))
    else:
        nick_or_msg = _crazyCase(nick_or_msg)
        _do_image_and_url(bot, nick_or_msg, img_path, font_path, linx_url, linx_pass)


# this captures messages
@thread(False)
@rule('(.*)')
@priority('low')
def note(bot, trigger):
    if not trigger.is_privmsg:
        bot.db.set_nick_value(trigger.nick, 'seen_timestamp', time.time())
        bot.db.set_nick_value(trigger.nick, 'seen_channel', trigger.sender)
        bot.db.set_nick_value(trigger.nick, 'seen_message', trigger)
        bot.db.set_nick_value(trigger.nick, 'seen_action', 'intent' in trigger.tags)


def _do_image_and_url(bot, msg, img_path, font_path, linx_url, linx_pass):
    _hash = _stringToBase64(msg)
    if str(_hash) not in bot.memory["spongebob_urls"]:
        image = _make_image(img_path, font_path, msg)
        if not image:
            return bot.reply("Something went wrong generating the image")
        url = _post_image(linx_url, linx_pass, image)
        if url: bot.memory["spongebob_urls"][str(_hash)] = url
    else:
        url = bot.memory["spongebob_urls"][str(_hash)]
    if not url:
        return bot.reply("Something went wrong uploading the image")
    bot.say(url)


def _make_image(path, font_path, message):
    message = _normalizeWhitespace(message)
    message = _stripFormatting(message)
    try:
        # try to split multi-word string in half without cutting a word in two
        if len(message.split()) > 1:

            if len(message) - len(message.split()[0]) > 0:
                n = len(message) // 2
            else:
                n = len(message.split()[0])
            
            if n < len(message.split()[0]):
                n = len(message.split()[0]) 

            half1 = message[:n]
            half2 = message[n:]

            half1_space = [pos for pos, char in enumerate(half1) if char == ' ']
            if not half1_space:
                half1_space = [pos for pos, char in enumerate(message[:n+1]) if char == ' ']
            half2_space = half2.find(' ')

            new_half1 = message[:half1_space[-1]].strip()
            new_half2 = message[half1_space[-1]:].strip()

            top_text = new_half1
            bot_text = new_half2
        else:
            top_text = ''
            bot_text = message
            
        # defaults
        shadow = 'black'
        fill = 'white'
        img = Image.open(path)
        W, H = img.size
        draw = ImageDraw.Draw(img)
        fontsize = 1
        img_fraction = 0.9
        
        # find ideal font size based on image size 
        # and length of text
        font = ImageFont.truetype(font_path, fontsize)
        if len(top_text) > len(bot_text):
            while font.getsize(top_text)[0] < img_fraction*img.size[0]:
                # iterate until the text size is just larger than the criteria
                fontsize += 1
                font = ImageFont.truetype(font_path, fontsize)
        else:
            while font.getsize(bot_text)[0] < img_fraction*img.size[0]:
                # iterate until the text size is just larger than the criteria
                fontsize += 1
                font = ImageFont.truetype(font_path, fontsize)
        # if we've exceed some sane values, let's reset
        if fontsize > 50:
            fontsize = 50
            font = ImageFont.truetype(font_path, fontsize)
        elif fontsize < 24:
            fontsize = 24
            font = ImageFont.truetype(font_path, fontsize)
        # get sizes and positions for actually drawing
        wt, ht = draw.textsize(top_text, font)
        wb, hb = draw.textsize(bot_text, font)
        xt = (W-wt)/2
        yt = -10
        xb = (W-wb)/2
        yb = H-70

        # TOP TEXT
        # be smarter about how we draw the text
        lines,tmp,h = _IntelliDraw(draw,top_text,font,W)
        # draw the text, hack for shadow by drawing the text a few times
        # in black just outside of where the actual text will be
        j = 0
        for i in lines:
            wt, _ = draw.textsize(i, font)
            xt = (W-wt)/2
            yt = 0+j*h
            # shadow/outline
            draw.text((xt-2, yt-2), i, font=font, fill=shadow)
            draw.text((xt+2, yt-2), i, font=font, fill=shadow)
            draw.text((xt-2, yt+2), i, font=font, fill=shadow)
            draw.text((xt+2, yt+2), i, font=font, fill=shadow)
            # actual text
            draw.text( (xt,yt), i , font=font, fill=fill)
            j = j + 1
        
        # BOTTOM TEXT
        lines,tmp,h = _IntelliDraw(draw,bot_text,font,W)
        j = 0
        for i in lines:
            wb, _ = draw.textsize(i, font)
            xb = (W-wb)/2
            yb = (H-((fontsize+25)*len(lines)))+j*h
            draw.text((xb-2, yb-2), i, font=font, fill=shadow)
            draw.text((xb+2, yb-2), i, font=font, fill=shadow)
            draw.text((xb-2, yb+2), i, font=font, fill=shadow)
            draw.text((xb+2, yb+2), i, font=font, fill=shadow)
            draw.text( (xb,yb), i , font=font, fill=fill)
            j = j + 1

        # save the image, read/convert to binary for the imgur upload
        img.save('out.png')
        f = open('out.png', 'rb')
        image = f.read()
        f.close()
    except:
        image = None

    return image


def _post_image(linx_url, linx_pass, image):
    # upload 
    headers = {
        'linx-api-key': linx_pass,
        'Linx-Expiry': '2592000',
        "Accept": "application/json",
    }
    try:
        r = requests.put(linx_url, headers=headers, data=image).json()
        link = r["direct_url"]
        return link
    except:
        return None


# helper functions

def _crazyCase(text):
    # this is dumb
    weight_upper = [False, False, True]
    weight_lower = [True, True, False]
    temp = ''
    text = text.lower()
    for idx, char in enumerate(text):
        # pick first character's case random 50/50
        if idx == 0:
            pick = random.choice([True, False])
        else:
            # pick the next character weighted, based on the previous's case
            # and also check for too many repeats
            if temp[-3:].isupper():
                pick = True
            elif temp[-3:].islower():
                pick = False
            else:
                if temp[-1].isupper():
                    pick = random.choice(weight_lower)
                else:
                    pick = random.choice(weight_upper)
        # now apply our selected case
        if pick:
            temp += char.lower()
        else:
            temp += char.upper()   
    return temp


def _IntelliDraw(drawer,text,font,containerWidth):
    words = text.split()  
    lines = [] # prepare a return argument
    lines.append(words) 
    finished = False
    line = 0
    while not finished:
        thistext = lines[line]
        newline = []
        innerFinished = False
        while not innerFinished:
            if drawer.textsize(' '.join(thistext),font)[0] > containerWidth:
                # this is the heart of the algorithm: we pop words off the current
                # sentence until the width is ok, then in the next outer loop
                # we move on to the next sentence. 
                newline.insert(0,thistext.pop(-1))
            else:
                innerFinished = True
        if len(newline) > 0:
            lines.append(newline)
            line = line + 1
        else:
            finished = True
    tmp = []        
    for i in lines:
        tmp.append( ' '.join(i) )
    lines = tmp
    (width,height) = drawer.textsize(lines[0],font)            
    return (lines,width,height)


def _stringToBase64(s):
    return base64.b64encode(s.encode('utf-8'))

def base64ToString(b):
    return base64.b64decode(b).decode('utf-8')


# everything below is from Supybot/Limnoria
def _normalizeWhitespace(s, removeNewline=True):
    r"""Normalizes the whitespace in a string; \s+ becomes one space."""
    if not s:
        return str(s) # not the same reference
    starts_with_space = (s[0] in ' \n\t\r')
    ends_with_space = (s[-1] in ' \n\t\r')
    if removeNewline:
        newline_re = re.compile('[\r\n]+')
        s = ' '.join(filter(bool, newline_re.split(s)))
    s = ' '.join(filter(bool, s.split('\t')))
    s = ' '.join(filter(bool, s.split(' ')))
    if starts_with_space:
        s = ' ' + s
    if ends_with_space:
        s += ' '
    return s

def _stripBold(s):
    """Returns the string s, with bold removed."""
    return s.replace('\x02', '')

def _stripItalic(s):
    """Returns the string s, with italics removed."""
    return s.replace('\x1d', '')

_stripColorRe = re.compile(r'\x03(?:\d{1,2},\d{1,2}|\d{1,2}|,\d{1,2}|)')
def _stripColor(s):
    """Returns the string s, with color removed."""
    return _stripColorRe.sub('', s)

def _stripReverse(s):
    """Returns the string s, with reverse-video removed."""
    return s.replace('\x16', '')

def _stripUnderline(s):
    """Returns the string s, with underlining removed."""
    return s.replace('\x1f', '')

def _stripFormatting(s):
    """Returns the string s, with all formatting removed."""
    # stripColor has to go first because of some strings, check the tests.
    s = _stripColor(s)
    s = _stripBold(s)
    s = _stripReverse(s)
    s = _stripUnderline(s)
    s = _stripItalic(s)
    return s.replace('\x0f', '')