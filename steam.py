import requests
import pendulum
from bs4 import BeautifulSoup

from io import StringIO
from html.parser import HTMLParser
import random
import re
from pprint import pprint

from sopel_sopel_plugin_argparser import parseargs

from sopel import module
from sopel.formatting import *
from sopel.tools import get_logger


LOGGER = get_logger(__name__)

API_URL = "https://store.steampowered.com/api/appdetails?appids={app_id}"
PKG_URL = "https://store.steampowered.com/api/packagedetails?packageids={pkg_id}"
SEARCH_URL = ("https://store.steampowered.com/search/suggest?term={query}"
              "&f=games&cc={region}&realm=1&l=english"
              "&ignore_preferences=1")
REVIEWS_URL = "https://store.steampowered.com/appreviewhistogram/{app_id}"
STEAM_URL_REGEX = re.compile(r"store\.steampowered\.com\/app\/(.+\d)\/")


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

    details = _fetch_game_details(game_data['id'], game_data.get('pkg'))

    if not details[game_data['id']]['success']:
        LOGGER.error("error fetching details")
    if game_data.get('pkg'):
        # TODO: implement
        game_details = details[game_data['id']]['data']
    else:
        game_details = details[game_data['id']]['data']

    reviews = _fetch_game_reviews(game_data['id'], game_data.get('pkg'))

    reply = _parse_game(game_data, game_details, reviews)

    bot.say(reply, max_messages=2)


@module.url(STEAM_URL_REGEX)
def get_info(bot, trigger, match=None):
    """
    Get information about the latest steam URL uploaded by the channel provided.
    """
    if trigger.sender == "#chat":
        return
    match = match or trigger
    _say_result(bot, trigger, match.group(1), include_link=False)


def _say_result(bot, trigger, match, include_link):
    details = _fetch_game_details(match)
    for k,v in details.items():
        if not v['success']:
            LOGGER.error("error fetching details")
            game_details = None
        else:
            game_details = v['data']

    reviews = _fetch_game_reviews(match)

    reply = _parse_game(None, game_details, reviews, include_link)

    bot.say(reply, max_messages=2)


def _fetch_search_page(query, region="US"):
    try:
        html = requests.get(SEARCH_URL.format(query=query, region=region))
        LOGGER.info(html.url)
        soup = BeautifulSoup(html.content)
        return soup
    except:
        return None


def _fetch_game_details(game_id, pkg_id=None):
    try:
        response = requests.get(API_URL.format(app_id=game_id))
        LOGGER.info(response.url)
        response = response.json()
        if pkg_id:
            pkg_response = requests.get(PKG_URL.format(pkg_id=pkg_id))
            pkg_response = pkg_response.json()
            for k,v in pkg_response.items():
                response[k] = v
        return response
    except:
        return None


def _fetch_game_reviews(game_id, pkg_id=None):
    try:
        response = requests.get(REVIEWS_URL.format(app_id=game_id))
        LOGGER.info(response.url)
        response = response.json()
        if pkg_id:
            pkg_response = requests.get(PKG_URL.format(pkg_id=pkg_id))
            pkg_response = pkg_response.json()
            for k,v in pkg_response.items():
                response[k] = v
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
        out['pkg'] = first_result.get('data-ds-packageid')
        out['id'] = out['id'].split(',')[0]
    out['url'] = first_result.get('href').split('/?')[0]
    out['name'] = html.find('div', class_='match_name').text
    if fetch_price:
        out['price'] = html.find('div', class_='match_price').text
    return out


def _parse_game(game_data, game_details, reviews, include_link=True):

    # pprint(game_details)
    def scores(score):
        display_score = "{:.0%}".format(score)
        if score >= 0.95:
            return color(f"Overwhelmingly Positive ({display_score})", "cyan")
        elif 0.80 <= score < 0.95:
            return color(f"Very Positive ({display_score})", "light_green")
        elif 0.70 <= score < 0.79:
            return color(f"Mostly Positive ({display_score})", "green")
        elif 0.40 <= score < 0.69:
            return color(f"Mixed ({display_score})", "yellow")
        elif 0.20 <= score < 0.39:
            return color(f"Mostly Negative ({display_score})", "orange")
        elif 0 <= score < 0.19:
            return color(f"Overwhelmingly Negative ({display_score})", "red")
        else:
            return display_score

    out = "[Steam] "
    out += bold(game_details['name']) if game_details else bold(game_data['name'])

    if int(game_details['required_age']) >= 18:
        out += bold(color(" [18+]", "red"))

    try:
        price = game_data.get('price')
    except:
        price = None
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

    # out += " | {}".format(game_details['short_description'].replace("&quot;", '"'))
    if reviews:
        if reviews.get('results'):
            results = reviews['results']
            if results.get('recent'):
                recent_pos = 0
                recent_neg = 0
                overall_pos = 0
                overall_neg = 0
                for rev in results['recent']:
                    recent_pos += rev['recommendations_up']
                    recent_neg += rev['recommendations_down']
                for rev in results['rollups']:
                    overall_pos += rev['recommendations_up']
                    overall_neg += rev['recommendations_down']
                total_recent = recent_neg + recent_pos
                total_overall = overall_neg + overall_pos
                out += " | {} recent, {} overall".format(
                    scores(recent_pos / total_recent),
                    scores(overall_pos / total_overall)
                )
    if game_details.get('metacritic'):
        out += " | {} on metacritic".format(game_details['metacritic']['score'])

    # last: link
    if include_link:
        out += " | {}".format(game_data['url'])

    return out