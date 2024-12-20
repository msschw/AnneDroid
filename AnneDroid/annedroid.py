import datetime
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

import message_storage as ms
import statistics as stat


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

    @bot.command(name="google", help="perform Google search")
    async def google(context, *query):
        from googlesearch import search

        try:
            searchresult = search(query=" ".join(query), start=0, stop=1, safe="on")
            await context.send(next(searchresult))
        except:
            await context.author.send("Query '" + query + "' provided no results.")

    @bot.command(name="googlensfw", help="perform NSFW Google search")
    async def google(context, *query):
        from googlesearch import search

        try:
            searchresult = search(query=" ".join(query), start=0, stop=1, safe="off")
            await context.send(next(searchresult))
        except:
            await context.author.send("Query '" + query + "' provided no results.")

    @bot.command(name="wiki", help="perform wikipedia search")
    async def wikipedia(context, *query):
        from wikipedia import search, page, exceptions

        searchresult = search(query=" ".join(query))
        # just lookup the first one
        if len(searchresult) > 0:
            try:
                wikipage = page(searchresult[0])
                await context.send(wikipage.title + ": " + wikipage.url)
            except exceptions.DisambiguationError as de:
                wikipage = page(random.choice(de.options))
                await context.send("(Amb.) " + wikipage.title + ": " + wikipage.url)
        else:
            await context.author.send("Query '" + query + "' provided no results.")

    @bot.command(name="yt", help="perform YouTube search")
    async def youtube(context, *query):
        from youtube_search import YoutubeSearch

        searchresult = YoutubeSearch(search_terms=" ".join(query), max_results=1)
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
        from imdb import IMDb

        imdb = IMDb()
        matches = imdb.search_movie(" ".join(query))
        if len(matches) > 0:
            await context.send(
                matches[0]["title"] + ": " + imdb.get_imdbURL(matches[0])
            )
        else:
            await context.author.send("Query '" + query + "' provided no results.")

    @bot.command(name="metacritic", help="perform Metacritic search")
    async def metacritic(context, *query):
        from metacritic_webdriver import MetacriticWebDriver

        metacritic = MetacriticWebDriver()
        result = metacritic.search(query)
        if result is not None:
            await context.send(result)
        else:
            await context.author.send("Query '" + query + "' provided no results.")

    @bot.command(name="protondb", help="perform ProtonDB search")
    async def protondb(context, *query):
        from protondb_webdriver import ProtonDBWebDriver

        protonDB = ProtonDBWebDriver()
        result = protonDB.search(query)
        if result is not None:
            await context.send(result)
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

    @bot.command(name="rki", help="Generate diagram from RKI CoViD19 nowcasting")
    async def rki(context, selector, days: int = 0):
        from rki_nowcasting import RKINowCasting

        rki = RKINowCasting()

        filename = "figure.png"

        if selector.lower().startswith("r"):
            rki.PlotR(filename, daysBack=days)

        if selector.lower().startswith("c"):
            rki.PlotCases(filename, days_back=days)

        if os.path.isfile(filename):
            with open(filename, "rb") as f:
                picture = discord.File(f)
                await context.send(file=picture)
            os.remove(filename)

    @bot.command(name="wa", help="query WolframAlpha")
    async def wolframalpha(context, *query):
        try:
            import wolframalpha

            client = wolframalpha.Client(os.getenv("WOLFRAMALPHA_API_KEY"))
            result = client.query(" ".join(query))
            await context.send(next(result.results).text)
        except Exception as e:
            await context.author.send("Could not query WolframAlpha: " + repr(e))

    @bot.command(name="gpt", help="query ddg-ai-chat")
    async def gpt(context, *query):
        try:
            from duck_chat import DuckChat
            async with DuckChat() as chat:
                await context.send(await chat.ask_question(" ".join(query)))
        except Exception as e:
            await context.author.send("Could not query AI chat: " + repr(e))

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
