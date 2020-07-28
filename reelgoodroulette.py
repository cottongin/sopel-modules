import requests
import pendulum
from bs4 import BeautifulSoup

from io import StringIO
from html.parser import HTMLParser

from sopel_sopel_plugin_argparser import parseargs

from sopel import module
from sopel.formatting import *
from sopel.tools import get_logger
from sopel.config.types import StaticSection, ValidatedAttribute


LOGGER = get_logger(__name__)
ROULETTE_API_URL = ("https://api.reelgood.com/v3.0/content/roulette?"
                    "content_kind={kind}&free=true&nocache=true&region={region}"
                    "&sources=netflix,hulu_plus,amazon_prime,disney_plus,"
                    "hbo_max,hbo,peacock,apple_tv_plus,fubo_tv,showtime,starz,"
                    "cbs_all_access,epix,crunchyroll_premium,funimation,"
                    "amc_premiere,kanopy,hoopla,criterion_channel,britbox,"
                    "dc_universe,mubi,cinemax,fandor,acorntv,hallmark_movies_now,"
                    "bet_plus,shudder,youtube_premium,indieflix,abc_tveverywhere,"
                    "ae_tveverywhere,amc,fx_tveverywhere,fox_tveverywhere,"
                    "nbc_tveverywhere,usa_tveverywhere,comedycentral_tveverywhere,"
                    "watch_food_network,cartoon_network,watchdisney_tveverywhere,"
                    "bet_tveverywhere,adult_swim_tveverywhere,e_tveverywhere,"
                    "hallmark_everywhere,history_tveverywhere,lifetime_tveverywhere,"
                    "natgeo_tveverywhere,tvland_tveverywhere,bravo_tveverywhere,"
                    "watch_hgtv,sundance_tveverywhere,syfy_tveverywhere,tbs,tnt,"
                    "mtv_tveverywhere,vh1_tveverywhere,watch_travel_channel,ifc,"
                    "watch_diy_network,nick_tveverywhere,bbc_america_tve,"
                    "fyi_tveverywhere,watch_tcm,viceland_tve,trutv_tveverywhere,"
                    "cnbc_tveverywhere,science_go,tlc_go")
INFO_API_URL = "https://api.reelgood.com/v3.0/content/{mode}/{guid}"

SOURCE_MAP = {

}

MODE_MAP = {
    "m": "movie",
    "s": "show",
}

class RGRSection(StaticSection):
    smmry_api_key = ValidatedAttribute('smmry_api_key', str)

def configure(config):
    config.define_section('smmry_api_key', RGRSection)
    config.reelgoodroulette.configure_setting('smmry_api_key', 'SMMRY api key')

def setup(bot):
    bot.config.define_section('reelgoodroulette', RGRSection)
    try:
        html_data = requests.get("https://reelgood.com/services")
        soup = BeautifulSoup(html_data.content, "html.parser")
        uls = soup.find_all("ul")
        for ul in uls:
            imgs = ul.find_all("img")
            for img in imgs:
                name = img.get("src")
                name = name.split("/")[-1]
                name = name.replace(".svg", "")
                full = img.get("alt")
                SOURCE_MAP[name] = full
        SOURCE_MAP["hulu_plus"] = "Hulu+"
    except:
        LOGGER.error("couldn't parse sources")
        pass

@module.commands('watch', 'whatshouldiwatch')
@module.example('.watch')
def get_random_show_or_movie(bot, trigger):
    """Fetch a random TV Show or Movie to enjoy"""

    try:
        api_key = bot.config.reelgoodroulette.smmry_api_key
    except:
        api_key = None

    user_input = None
    if trigger.group(2):
        user_input = parseargs(trigger.group(2).strip().lower())

    response = reelgood_random(user_input, api_key)

    bot.reply(response[0])
    if len(response) > 1:
        for line in response[1:]:
            bot.say(line, max_messages=2)


def reelgood_random(user_input=None, api_key=None):
    """Gets a random TV Show or Movie from reelgood.com roulette API"""

    if user_input:
        pass
    url = ROULETTE_API_URL.format(kind="both", region="us")

    try:
        response = requests.get(url)
        LOGGER.info(response.url)
        data = response.json()
    except:
        return ["Something went wrong fetching from the API."]

    if data.get('errors'):
        LOGGER.error(data['errors'])
        return ["Something went wrong parsing the response from the API"]

    guid = data['id']
    mode = MODE_MAP[data['content_type']]
    url = INFO_API_URL.format(mode=mode, guid=guid)
    try:
        response = requests.get(url)
        LOGGER.info(response.url)
        info_data = response.json()
    except:
        return ["Something went wrong fetching from the API."]

    replies = []
    base_url = "https://reelgood.com/{mode}/{slug}"
    sources = []
    for src in info_data['sources']:
        try:
            sources.append(SOURCE_MAP[src])
        except:
            sources.append(src)
    replies.append("I found a {} called {} for you to watch on {}. See more here: {}".format(
        mode,
        bold(data['title']),
        ", ".join(sources),
        base_url.format(mode=mode, slug=data['slug'])
    ))

    try:
        text = info_data['overview'] if info_data['overview'] else info_data['reelgood_synopsis']
        summary = summry(strip_tags(text), api_key)
        summary = summary["sm_api_content"]
        replies.append("\x02Summary:\x02 {}".format(summary))
    except:
        text = info_data['overview'] if info_data['overview'] else info_data['reelgood_synopsis']
        replies.append("\x02Summary:\x02 {}".format(strip_tags(text)))

    scores = "\x02Rating(s):\x02 "
    scores_t = []
    if info_data.get('imdb_rating'):
        scores_t.append("IMDB: {}".format(info_data['imdb_rating']))
    if info_data.get('rt_audience_rating'):
        scores_t.append("RT Audience: {}".format(info_data['rt_audience_rating']))
    if info_data.get('rt_critics_rating'):
        scores_t.append("RT Critics: {}".format(info_data['rt_critics_rating']))
    if info_data.get('reelgood_scores'):
        if info_data['reelgood_scores'].get('reelgood_popularity'):
            scores_t.append("Reelgood Popularity: {}".format(info_data['reelgood_scores']['reelgood_popularity']))
    if scores_t:
        replies.append(scores + " | ".join(scores_t))

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

def summry(text, api_key=None):
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