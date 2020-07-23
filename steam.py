import requests
import pendulum
from bs4 import BeautifulSoup

from io import StringIO
from html.parser import HTMLParser
import random

from sopel_sopel_plugin_argparser import parseargs

from sopel import module
from sopel.formatting import *
from sopel.tools import get_logger


LOGGER = get_logger(__name__)

API_URL = "https://store.steampowered.com/api/appdetails?appids={app_id}"
SEARCH_URL = ("https://store.steampowered.com/search/suggest?term={query}"
              "&f=games&cc={region}&realm=1&l=english"
              "&excluded_content_descriptors%5B%5D=3"
              "&excluded_content_descriptors%5B%5D=4&v=9008005")

@module.commands('steam')
@module.example('.steam Half-Life 3')
def get_steam_info(bot, trigger):
    """Fetches information about a given game from store.steampowered.com"""

    if not trigger.group(2):
        return bot.reply("I need a game to look up!")

    user_input = parseargs(trigger.group(2).lower())

    query = user_input.get("--query") or user_input["extra_text"]
    region = user_input.get("--region") or "US"

    search_html = _fetch_search_page(query=query, region=region)
    if not search_html:
        return bot.reply("Something went wrong finding that game!")

    fetch_price = False if region == "US" else True
    game_data = _parse_html(search_html, fetch_price)
    if not game_data:
        return bot.reply("I couldn't find that game.")

    details = _fetch_game_details(game_data['id'])
    for k,v in details.items():
        if not v['success']:
            LOGGER.error("error fetching details")
            game_details = None
        else:
            game_details = v['data']

    reply = _parse_game(game_data, game_details)

    bot.say(reply, max_messages=2)


def _fetch_search_page(query, region="US"):
    try:
        html = requests.get(SEARCH_URL.format(query=query, region=region))
        LOGGER.info(html.url)
        soup = BeautifulSoup(html.content)
        return soup
    except:
        return None

def _fetch_game_details(game_id):
    try:
        response = requests.get(API_URL.format(app_id=game_id))
        LOGGER.info(response.url)
        response = response.json()
        return response
    except:
        return None

def _parse_html(html, fetch_price=False):
    first_result = html.find('a')
    if not first_result:
        return None
    out = {}
    out['id'] = first_result.get('data-ds-appid') or first_result.get('data-ds-packageid')
    if "," in out['id']:
        out['id'] = first_result.get('data-ds-packageid')
    out['url'] = first_result.get('href').split('/?')[0]
    out['name'] = html.find('div', class_='match_name').text
    if fetch_price:
        out['price'] = html.find('div', class_='match_price').text
    return out

def _parse_game(game_data, game_details):
    out = "[Steam] "
    out += bold(game_details['name']) if game_details else bold(game_data['name'])

    price = game_data.get('price')
    if not price:
        if game_details.get('price_overview'):
            price = game_details['price_overview']['final_formatted']
            if game_details['price_overview'].get('discount_percent'):
                discount = color(" ({}% off)".format(game_details['price_overview']['discount_percent']), "green")
            else:
                discount = ""
        else:
            price = "Free"
            discount = ""
        
    out += " | {price}{discount}".format(price=price, discount=discount)
    out += " | {}: {}".format(
        bold("OS"),
        ", ".join(k.title() for k,v in game_details['platforms'].items() if v)
    )

    out += " | {}: {}".format(
        bold("Genre{}".format("s" if len(game_details['genres']) > 1 else "")),
        ", ".join([genre['description'] for genre in game_details['genres']])
    )

    # out += " | {} achievements".format(
    #     game_details['achievements']['total'] if game_details.get('achievements') else "0"
    # )

    if len(game_details['developers']) == 1 and len(game_details['publishers']) == 1 \
        and game_details['developers'][0] == game_details['publishers'][0]:
        out += " | {}: {}".format(
            bold("Developer/Publisher"),
            game_details['developers'][0]
        )
    else:
        out += " | {}: {}".format(
            bold("Developer{}".format("s" if len(game_details['developers']) > 1 else "")),
            ", ".join(game_details['developers'])
        )
        out += " | {}: {}".format(
            bold("Publisher{}".format("s" if len(game_details['publishers']) > 1 else "")),
            ", ".join(game_details['publishers'])
        )

    out += " | {}: {}".format(
        bold("Release{}".format("s" if game_details['release_date']['coming_soon'] else "d")),
        game_details['release_date']['date']
    )

    # out += " | {}".format(game_details['short_description'])

    # last: link
    out += " | {}".format(game_data['url'])

    return out