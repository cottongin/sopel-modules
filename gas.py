import sopel.module
from sopel.formatting import *

import requests
import urllib.parse

HEADERS = {
    'Host': 'www.gasbuddy.com',
    'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 11316.35.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.30 Safari/537.36',
    'DNT': '1',
    'Accept': '*/*',
    'Cache-Control': 'no-cache',
}
        
SEARCH_ENDPOINT = 'https://www.gasbuddy.com/assets-v2/api/stations?search={query}&fuel=1'
STATIONS_ENDPOINT = 'https://www.gasbuddy.com/assets-v2/api/fuels?{stations}'

@sopel.module.commands('gas', 'gasbuddy')
@sopel.module.example('.gas 75069')
def gas(bot, trigger):
    """Fetches gas prices for provided query/location."""

    query = trigger.group(2)
    if not query:
        return bot.reply("You need to give me a location!")

    quoted_query = urllib.parse.quote_plus(query)

    try:
        url = SEARCH_ENDPOINT.format(query=quoted_query)
        search_results = requests.get(url, headers=HEADERS).json()
    except:
        return bot.reply('ERROR: Something went wrong searching for your query: {}'.format(query))
    
    try:
        region_trends = search_results['trends'][0]
    except:
        return bot.reply('ERROR: Something went wrong parsing search results (try again?)')
    
    stationIds = ''
    for station in search_results['stations']:
        stationIds += '&stationIds={}'.format(station['id'])
        
    try:
        url = STATIONS_ENDPOINT.format(stations=stationIds)
        # bot.say(url)
        prices = requests.get(url, headers=HEADERS).json()
    except:
        return bot.reply('ERROR: Something went wrong fetching fuel prices.')
    
    prices = prices['fuels']
    
    region = "\x02%s, %s\x02" % (region_trends['AreaName'], region_trends['State'])
    low = "\x02{}\x02".format(color('$' + "{:.2f}".format(region_trends['TodayLow']), 'green'))
    high = "\x02{}\x02".format(color('$' + "{:.2f}".format(region_trends['TodayHigh']), 'red'))
    avg = "\x02{}\x02".format('$' + "{:.2f}".format(region_trends['Today']))
    reply_string = "GasBuddy.com Fuel Info :: {} :: Today's Low: {} | Today's High: {} | Average Price: {}"
    reply_string = reply_string.format(
        region,
        low,
        high,
        avg
    )
    bot.say(reply_string)
    return