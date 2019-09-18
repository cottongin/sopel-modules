# sopel-modules

A collection of misc sopel modules

## Requirements
- Sopel
- tweepy (for the twitter module)
- pendulum (for the odds, space, and twitter modules)

(these modules are **all** written for Python 3.6+, your mileage may vary if running on earlier versions of Python)

## Modules

### Quick Start

Module | Commands | Description
------ | -------- | -----------
exchange | `.exchange` (`.x`, `.xe`) | converts currencies
gas | `.gas` (`.gasbuddy`) | fetches gas prices
odds | `.odds` | fetches sports odds
space | `.launch` (`.space`) | fetches information on next rocket launch
space | `.spacex` | fetches information on next SpaceX launch
twitter* | `.twitter` (`.t`) | fetches most recent tweet
twitter* | `.tsearch` (`.ts`) | fetches at most 3 tweets via search
wolfram* | `.wolfram` (`.wa`) | queries Wolfram Alpha

_*API key(s) required_

### exchange

This module converts a provided amount in one currency to another (e.g. `.exchange 10 usd to cad`)

![exchange demo](https://i.imgur.com/l5ocM1H.png)

### gas

This module fetches gas prices for a region/location provided by the caller (e.g. `.gas New York`)

![gas demo](https://i.imgur.com/l0E7pZh.png)

### odds

This module fetches sports odds for a provided league (nfl, cfb, mlb, nhl, nba currently supported) and can optionally be filtered by team(s) (e.g. `.odds nfl` / `.odds cfb bama` / `.odds mlb bos nyy`)

![odds demo](https://i.imgur.com/HOLKq9D.png)

### space

This module fetches information about upcoming rocket launches

- `.launch` (or `.space`)
  - ![space demo 1](https://i.imgur.com/duQqs4F.png)
- `.spacex`
  - ![space demo 2](https://i.imgur.com/FsnJsO4.png)

### twitter

**API Keys required**

This module interacts with the Twitter API

- .twitter (or .t) _Twitter handle_ (e.g. `.twitter Twitter`)
  - ![twitter demo](https://i.imgur.com/kW28Xjy.png)
- .tsearch (or .ts) _search query_ (e.g. `.tsearch sopel is awesome`)
  - ![tsearch demo](https://i.imgur.com/pTovk2p.png)

Once you have acquired Twitter API keys you can set them in a PM with the bot via `.set twitter.consumer_key <your key>` and `.set twitter.consumer_secret <your secret>`

### wolfram

**API Key required**

This module queries the Wolfram Alpha API with user provided input (e.g. `.wolfram tallest building in the world`)

![wolfram demo](https://i.imgur.com/jEgJpzU.png)

Once you have acquired your Wolfram Alpha API key you can set it in a PM with the bot via `.set wolfram.api_key <your api key>`