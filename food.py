import requests
import pendulum
from bs4 import BeautifulSoup

from io import StringIO
from html.parser import HTMLParser
from random import choice

from sopel_sopel_plugin_argparser import parseargs

from sopel import module
from sopel.formatting import *
from sopel.tools import get_logger
from sopel.config.types import StaticSection, ValidatedAttribute


LOGGER = get_logger(__name__)
API_KEY = "&apiKey={config_spoon_api_key}"
API_URL = "https://api.spoonacular.com/"
SMMRY_API_KEY = "{config_smmry_api_key}"

DIET_MAP = {
    "keto": "Ketogenic",
    "vegetarian": "Vegetarian",
    "vegan": "Vegan",
    "pescetarian": "Pescetarian",
    "paleo": "Paleo",
    "primal": "Primal",
    "gf": "Gluten%20Free"
}


class APISection(StaticSection):
    spoonacular_api_key = ValidatedAttribute('spoonacular_api_key', str)
    smmry_api_key = ValidatedAttribute('smmry_api_key', str)

def configure(config):
    config.define_section('spoonacular', APISection)
    config.food.configure_setting('spoonacular_api_key', 'spoonacular api key')
    config.food.configure_setting('smmry_api_key', 'SMMRY api key')

def setup(bot):
    global API_KEY, SMMRY_API_KEY
    bot.config.define_section('spoonacular', APISection)
    API_KEY = API_KEY.format(config_spoon_api_key=bot.config.spoonacular.spoonacular_api_key)
    SMMRY_API_KEY = SMMRY_API_KEY.format(config_smmry_api_key=bot.config.spoonacular.smmry_api_key)


@module.commands('food', 'whatshouldieat')
@module.example('.food')
def get_random_meal(bot, trigger):
    """Fetch a random meal to enjoy"""

    user_input = None
    if trigger.group(2):
        user_input = trigger.group(2).strip().lower()
        args = parseargs(user_input)
        if args.get('--ingredients') or args.get('--have'):
            ingredients = args.get('--ingredients') or args.get('--have')
            diet = None
            if args.get('--diet'):
                diet = args['--diet']
            response = get_random_recipe("ingredients", type_of_diet=diet, ingredients=ingredients)
        else:
            response = get_random_recipe("meal", type_of_diet=user_input)
    else:
        response = get_random_recipe("meal", type_of_diet=user_input)

    bot.reply(response[0])
    if len(response) > 1:
        for line in response[1:]:
            bot.say(line, max_messages=2)


@module.commands('drink', 'whatshouldidrink')
@module.example('.drink')
def get_random_drink(bot, trigger):
    """Fetch a random beverage to enjoy"""

    user_input = None
    if trigger.group(2):
        user_input = trigger.group(2).strip().lower()

    response = get_random_recipe("drink", user_input)

    bot.reply(response[0])
    if len(response) > 1:
        for line in response[1:]:
            bot.say(line, max_messages=2)


def get_random_recipe(type_of_recipe, type_of_diet=None, ingredients=None):
    """Gets a random recipe"""
    # print(trigger.group(1))
    if API_KEY[-4:] == "None":
        return ["You need to configure me with a spoonacular API key"]

    if type_of_recipe == "drink":
        url = API_URL + "/recipes/random?number=1" + API_KEY
        url += "&tags=beverage,drink"
    elif type_of_recipe == "meal":
        url = API_URL + "/recipes/random?number=1" + API_KEY
        url += "&tags=main%20course"
    elif type_of_recipe == "ingredients":
        url = (API_URL + 
               "recipes/findByIngredients?ingredients={ingredients}".format(
                   ingredients=ingredients
               ) +
               API_KEY)
        url += "&tags=main%20course"
    else:
        url += "&tags=main%20course"

    if type_of_diet:
        if type_of_diet not in DIET_MAP:
            return ["I'm not familiar with that diet. Valid options: {}".format(
                ", ".join(DIET_MAP.keys())
            )]
        diet = DIET_MAP[type_of_diet].lower()
        url += "," + diet

    try:
        response = requests.get(url)
        LOGGER.info(response.url)
        temp_data = response.json()
    except:
        return ["Something went wrong fetching from the API."]

    missing_ingredients = {}
    if len(temp_data) == 10:
        recipe = choice(temp_data)
        missing_ingredients['count'] = recipe['missedIngredientCount']
        missing_ingredients['list'] = []
        for ing in recipe['missedIngredients']:
            missing_ingredients['list'].append(ing['name'])
        url = API_URL + "recipes/{}/information?includeNutrition=false".format(recipe['id']) + API_KEY
        recipe = requests.get(url).json()
    else:
        if not temp_data.get('recipes'):
            return ["I couldn't find a random recipe."]
        recipe = temp_data['recipes'][0]

    # print(recipe)

    replies = []
    replies.append("I found {} for you to try. See more here: {}".format(
        bold(recipe['title']),
        recipe['sourceUrl']
    ))

    if missing_ingredients:
        replies.append("You're missing {} ingredients! ({})".format(
            missing_ingredients['count'],
            ",".join(missing_ingredients['list'])))

    try:
        summary = summry(strip_tags(recipe['summary']))
        summary = summary["sm_api_content"]
        replies.append("\x02Summary:\x02 {}".format(summary))
    except:
        replies.append("\x02Summary:\x02 {}".format(strip_tags(recipe['summary'])))

    return replies


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def summry(text):
    api_key = SMMRY_API_KEY
    if not api_key:
        return text
    api_endpoint = "https://api.smmry.com"

    data = {
        "sm_api_input": text
    }
    params = {
        "SM_API_KEY": api_key,
        "SM_LENGTH": 3,
        "SM_IGNORE_LENGTH": True,
    }
    header_params = {"Expect":"100-continue"}

    r = requests.post(url=api_endpoint, params=params, data=data, headers=header_params)

    return r.json()