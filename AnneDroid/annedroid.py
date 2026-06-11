import aiohttp
import asyncio
import datetime
import ddgs
import imdb as imdblib
import os
import random
import wikipedia
import wolframalpha
import youtube_search

import discord
from discord.ext import commands
from dotenv import load_dotenv
from google import genai

import message_storage as ms
import statistics as stat

# Fix wikipedia library: use HTTPS and a proper User-Agent
import wikipedia.wikipedia as _wiki_mod

_wiki_mod.API_URL = "https://en.wikipedia.org/w/api.php"
_wiki_mod.USER_AGENT = "AnneDroidBot/1.0 (annedroid-bot@example.com)"


def main():
    load_dotenv()
    token = os.getenv("ANNEDROID_TOKEN")

    message_database = "messages.db"

    mdb = ms.MessageStorage(message_database)
    statistics = stat.Statistics(mdb)

    help_command = commands.DefaultHelpCommand(no_category="Available Commands")
    intents = discord.Intents.default()
    intents.messages = True
    intents.guild_messages = True
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", help_command=help_command, intents=intents)

    def message_db_channelname(message):
        return message.guild.name + ":" + message.channel.name

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return

        # message storage
        if message.guild is not None:
            mdb.insert_message(
                ms.Message(
                    message.author.name,
                    message.content,
                    message_db_channelname(message),
                    datetime.datetime.now().strftime(ms.Message.FORMAT),
                )
            )

        # process commands
        await bot.process_commands(message)

    @bot.command(name="stats", help="show channel stats")
    @commands.guild_only()
    async def stats(context):
        await context.send(
            statistics.message_length_stats(message_db_channelname(context))
        )

    @bot.command(name="quote", help="show random quote from current channel")
    @commands.guild_only()
    async def quote(context):
        await context.send(statistics.random_quote(message_db_channelname(context)))

    @bot.command(name="gquote", help="show random quote from current channel and provide an analysis")
    @commands.guild_only()
    async def comment_quote(context):
        quote = statistics.random_quote(message_db_channelname(context))
        api_key = os.getenv("GEMINI_API_KEY")
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-1.5-flash-002', contents="Provide a very sarcastic response to the following quote in maximum three sentences: " + " ".join(quote)
            )
            await context.send(f"{quote}\n{response.text}")
        except Exception as e:
            await context.author.send("Sorry, i failed")

    @bot.command(name="google", help="perform DDG search")
    async def google(context, *query):
        try:
            with ddgs.DDGS() as ddg:
                searchresult = ddg.text(
                    " ".join(query), max_results=1
                )
                if len(searchresult) > 0:
                    await context.send(f'{searchresult[0]["title"]}: {searchresult[0]["href"]}')
                else:
                    await context.send("No results")
        except Exception as e:
            await context.author.send(f"Query {query} provided no results: {e}")

    @bot.command(name="wiki", help="perform wikipedia search")
    async def wiki(context, *query):
        searchresult = wikipedia.search(query=" ".join(query))
        # just lookup the first one
        if len(searchresult) > 0:
            try:
                wikipage = wikipedia.page(searchresult[0])
                await context.send(wikipage.title + ": " + wikipage.url)
            except wikipedia.exceptions.DisambiguationError as de:
                wikipage = wikipedia.page(random.choice(de.options))
                await context.send("(Amb.) " + wikipage.title + ": " + wikipage.url)
        else:
            await context.author.send("Query '" + query + "' provided no results.")

    @bot.command(name="yt", help="perform YouTube search")
    async def youtube(context, *query):
        searchresult = youtube_search.YoutubeSearch(
            search_terms=" ".join(query), max_results=1
        )
        # just lookup the first one
        if len(searchresult.videos) > 0:
            await context.send(
                searchresult.videos[0]["title"]
                + ": "
                + "https://youtube.com"
                + searchresult.videos[0]["url_suffix"]
            )
        else:
            await context.author.send("Query '" + query + "' provided no results.")

    @bot.command(name="imdb", help="perform iMDB search")
    async def imdb(context, *query):
        imdb = imdblib.IMDb()
        matches = imdb.search_movie(" ".join(query))
        if len(matches) > 0:
            await context.send(
                matches[0]["title"] + ": " + imdb.get_imdbURL(matches[0])
            )
        else:
            await context.author.send("Query '" + query + "' provided no results.")

    @bot.command(
        name="timer", help="set a timer specifying duration(XXhYYmZZs) and a message"
    )
    async def timer(context, time_str, *message):
        import asyncio
        from datetime import timedelta
        import re

        regex = re.compile(
            r"((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?"
        )
        parts = regex.match(time_str)
        if not parts:
            await context.author.send(
                "Please check queried time '" + time_str + "'to match format: XXhYYmZZs"
            )
        parts = parts.groupdict()
        time_params = {}
        for name, param in parts.items():
            if param:
                time_params[name] = int(param)
        duration = timedelta(**time_params)

        try:
            seconds = float(duration.seconds)
            await asyncio.sleep(seconds)
            await context.send(context.message.author.mention + " " + " ".join(message))
        except Exception as e:
            await context.author.send("Could not set timer: " + repr(e))

    @bot.command(name="wa", help="query WolframAlpha")
    async def wa(context, *query):
        try:
            client = wolframalpha.Client(os.getenv("WOLFRAMALPHA_API_KEY"))
            result = await asyncio.to_thread(client.query, " ".join(query))
            await context.send(next(result.results).text)
        except Exception as e:
            await context.author.send("Could not query WolframAlpha: " + repr(e))

    @bot.command(name="protondb", help="look up a game's ProtonDB rating")
    async def protondb(context, *query):
        try:
            game = " ".join(query)
            async with aiohttp.ClientSession() as session:
                params = {"term": game, "cc": "us", "l": "en"}
                async with session.get(
                    "https://store.steampowered.com/api/storesearch",
                    params=params,
                ) as resp:
                    data = await resp.json()

                items = data.get("items", [])
                if len(items) == 0:
                    await context.send("No Steam games found for that query.")
                    return

                game = items[0]
                game_id = game["id"]
                game_name = game["name"]

                async with session.get(
                    f"https://www.protondb.com/api/v1/reports/summaries/{game_id}.json"
                ) as resp:
                    if resp.status != 200:
                        await context.send(f"{game_name}: **No Rating**")
                        return
                    rating_data = await resp.json(content_type=None)

                tier = rating_data.get("tier", "unknown")
                confidence = rating_data.get("confidence", "unknown")
                total = rating_data.get("total", 0)

                await context.send(
                    f"{game_name}: **{tier.capitalize()}** "
                    f"(confidence: {confidence}, {total} reports)"
                )
        except Exception as e:
            await context.author.send("Could not query ProtonDB: " + repr(e))

    @bot.command(name="gem", help="query gemini 1.5 flash")
    async def gemini(context, *query):
        api_key = os.getenv("GEMINI_API_KEY")
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash', contents=" ".join(query)
            )
            chunks = [response.text[i:i + 2000] for i in range(0, len(response.text), 2000)]
            for chunk in chunks:
                await context.send(chunk)
        except Exception as e:
            await context.author.send("Could not query Gemini: " + repr(e))

    async def set_idle_state():
        await bot.change_presence(
            activity=discord.Game(name="with herself"), status=discord.Status.online
        )

    async def set_dnd_state(message):
        await bot.change_presence(
            activity=discord.Activity(name=message), status=discord.Status.dnd
        )

    @bot.event
    async def on_ready():
        await set_idle_state()

    bot.run(token)


if __name__ == "__main__":
    main()
