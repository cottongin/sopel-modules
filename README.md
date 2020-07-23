# sopel-modules

A collection of misc sopel modules

## Requirements
- Python 3.6+
- Sopel (v7+)
- tweepy (for the twitter module)
- pendulum (for the odds, space, and twitter modules)

(these modules are **all** written for Python 3.6+, your mileage may vary if running on earlier versions of Python, and tested/run on Sopel 7)

## Modules

### Quick Start

| Module          | Commands                     | Description                                                                |
|-----------------|------------------------------|----------------------------------------------------------------------------|
| exchange        | `.exchange` (`.x`, `.xe`)    | converts currencies                                                        |
| figlet          | `.figlet` (`.fig`, `.f`)     | converts input to BIG TEXT                                                 |
| gas             | `.gas` (`.gasbuddy`)         | fetches gas prices                                                         |
| misc            | `.pick`                      | picks a random choice from input                                           |
|                 | `.source`                    | outputs a link to this repository                                          |
|                 | `.uptime`                    | outputs bot uptime information                                             |
| nhl             | `.nhlplayer`                 | fetches bio information for provided player lookup (\<team\> \<roster #\>) |
| odds            | `.odds`                      | fetches sports odds                                                        |
| podcasts*       |                              | module with various commands for looking up podcast information            |
| soma            |                              | module with various commands for fetching information from somafm          |
| space           | `.launch` (`.space`)         | fetches information on next rocket launch                                  |
|                 | `.spacex`                    | fetches information on next SpaceX launch                                  |
| spongebob       | `.spongebob` (`.sb`, `.sbl`) | generates a sPoNgEbOb meme image                                           |
| twitch*         |                              | module that fetches more detailed information from twitch links            |
| twitter*        | `.twitter` (`.t`)            | fetches most recent tweet                                                  |
|                 | `.tsearch` (`.ts`)           | fetches at most 3 tweets via search                                        |
| urbandictionary | `.urbandictionary` (`.ud`)   | fetches definition from Urban Dictionary                                   |
| wolfram*        | `.wolfram` (`.wa`)           | queries Wolfram Alpha                                                      |
| steam           | `.steam`                     | queries the Steam Store and returns basic info                             |

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

### urbandictionary

This module fetches definitions from Urban Dictionary.  Use `--worst` to fetch the worst-rated definition.  If no input/word is provided, will fetch a random word.

### wolfram

**API Key required**

This module queries the Wolfram Alpha API with user provided input (e.g. `.wolfram tallest building in the world`)

![wolfram demo](https://i.imgur.com/jEgJpzU.png)

Once you have acquired your Wolfram Alpha API key you can set it in a PM with the bot via `.set wolfram.api_key <your api key>`

### spongebob

**Requires lots of configuration and a [linx.li](https://linx.li) server**

This module generates a sPoNgEbOb meme image based on user input, it requires a lot of configuration and your own [linx.li](https://linx.li) server so I am not going into detail here on how to get it working.

The source code is there if you'd like to give it a shot yourself

### steam

**Requires my custom argparser which I haven't published yet, Coming Some Day™**, but should be able to made to function without it with minimal effort

This module queries the [Steam Store](https://store.steampowered.com) for a user provided game and returns basic information.

```
<cottongin> ?steam half-life
<sopel> [Steam] Half-Life: Alyx | $59.99 | OS: Windows | Genres: Action, Adventure | Developer/Publisher: Valve | Released: Mar 23, 2020 | https://store.steampowered.com/app/546560/HalfLife_Alyx
```

It uses the Steam Store's search autosuggestion (first result only, for now) and isn't very configurable.