import aiohttp
import asyncio
import datetime
import ddgs
import imdb as imdblib
import io
import os
import random
import urllib.parse
import wikipedia
import wolframalpha
import youtube_search
from bs4 import BeautifulSoup

import discord
from discord.ext import commands
from dotenv import load_dotenv
from google import genai
from groq import AsyncGroq

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
        if len(searchresult) == 0:
            await context.author.send("Query '" + query + "' provided no results.")
            return

        for title in searchresult:
            try:
                wikipage = wikipedia.page(title)
                url = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
                await context.send(wikipage.title + ": " + url)
                return
            except wikipedia.exceptions.DisambiguationError as de:
                for option in de.options:
                    try:
                        wikipage = wikipedia.page(option)
                        url = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(option.replace(" ", "_"))
                        await context.send(
                            "(Amb.) " + wikipage.title + ": " + url
                        )
                        return
                    except wikipedia.exceptions.DisambiguationError:
                        continue
                    except wikipedia.exceptions.PageError:
                        continue
                await context.send(
                    title + " (disambiguation): "
                    + ", ".join(de.options[:15])
                )
                return
            except wikipedia.exceptions.PageError:
                continue

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

    @bot.command(name="metacritic", help="look up a game's Metacritic score")
    async def metacritic(context, *query):
        try:
            game = " ".join(query)
            slug = urllib.parse.quote(game.lower().replace(" ", "-"))
            async with aiohttp.ClientSession(
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/133.0.0.0 Safari/537.36"
                    )
                }
            ) as session:
                async with session.get(
                    f"https://www.metacritic.com/search/game/{slug}/results"
                ) as resp:
                    if resp.status != 200:
                        await context.send(
                            "Could not reach Metacritic."
                        )
                        return
                    html = await resp.text()

                soup = BeautifulSoup(html, "html.parser")
                items = soup.select(".search-item")

                if len(items) == 0:
                    await context.send(
                        "No games found on Metacritic for that query."
                    )
                    return

                for item in items:
                    name_el = item.select_one(".c-search-item__title")
                    score_el = item.select_one(".c-siteReviewScore span")
                    if not name_el or not score_el:
                        continue
                    name = name_el.get_text(strip=True)
                    score = score_el.get_text(strip=True)
                    if score.isdigit():
                        await context.send(f"{name}: **{score}**")
                        return

                await context.send(
                    "No Metacritic rating available for any result."
                )
        except Exception as e:
            await context.author.send(
                "Could not query Metacritic: " + repr(e)
            )

    @bot.command(name="gem", help="query gemini 2.0 flash (free tier)")
    async def gemini(context, *query):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            await context.author.send("GEMINI_API_KEY not set.")
            return
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.0-flash', contents=" ".join(query)
            )
            chunks = [response.text[i:i + 2000] for i in range(0, len(response.text), 2000)]
            for chunk in chunks:
                await context.send(chunk)
        except Exception as e:
            await context.author.send("Could not query Gemini: " + repr(e))

    @bot.command(name="gpt", help="query GPT-4 via text.pollinations.ai (free)")
    async def gpt(context, *query):
        try:
            prompt = " ".join(query)
            url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        await context.send(f"Could not query GPT: {text[:200]}")
                        return
                    text = await resp.text()
            chunks = [text[i:i + 2000] for i in range(0, len(text), 2000)]
            for chunk in chunks:
                await context.send(chunk)
        except Exception as e:
            await context.author.send("Could not query GPT: " + repr(e))

    @bot.command(name="groq", help="query llama 3.3 via groq")
    async def groq(context, *query):
        api_key = os.getenv("GROQ_API_KEY")
        try:
            client = AsyncGroq(api_key=api_key)
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": " ".join(query)}],
            )
            text = response.choices[0].message.content
            chunks = [text[i:i + 2000] for i in range(0, len(text), 2000)]
            for chunk in chunks:
                await context.send(chunk)
        except Exception as e:
            await context.author.send("Could not query Groq: " + repr(e))

    @bot.command(name="hug", help="generate an image from a text prompt via Pollinations.ai")
    async def hug(context, *query):
        try:
            prompt = " ".join(query)
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?model=flux&nologo=true"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        await context.send(f"Could not generate image: {text[:200]}")
                        return
                    data = await resp.read()
            await context.send(file=discord.File(fp=io.BytesIO(data), filename="hug.png"))
        except Exception as e:
            await context.author.send("Could not generate image: " + repr(e))

    @bot.command(name="song", help="generate music from a text description via AI Music API")
    async def song(context, *query):
        api_key = os.getenv("AIMUSIC_API_KEY")
        if not api_key:
            await context.author.send("AIMUSIC_API_KEY not set.")
            return
        try:
            prompt = " ".join(query)
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept-Encoding": "identity",
            }
            body = {
                "custom_mode": False,
                "mv": "sonic-v4-5",
                "title": prompt[:50],
                "tags": "ai generated",
                "gpt_description_prompt": prompt,
            }
            async with context.typing():
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.post(
                        "https://api.aimusicapi.ai/api/v1/sonic/create",
                        json=body,
                    ) as resp:
                        if resp.status != 200:
                            text = await resp.text()
                            await context.send(f"Could not create music: {text[:200]}")
                            return
                        result = await resp.json()

                    task_id = result.get("task_id")
                    if not task_id:
                        await context.send("No task ID returned.")
                        return

                    for _ in range(60):
                        await asyncio.sleep(5)
                        async with session.get(
                            f"https://api.aimusicapi.ai/api/v1/sonic/task/{task_id}"
                        ) as poll_resp:
                            if poll_resp.status != 200:
                                continue
                            poll = await poll_resp.json()
                            if poll.get("type") == "not_ready":
                                continue
                            clips = poll.get("data", [])
                            if not isinstance(clips, list):
                                continue
                            for clip in clips:
                                if clip.get("state") == "succeeded":
                                    audio_url = clip.get("audio_url", "")
                                    if audio_url:
                                        async with session.get(audio_url) as audio_resp:
                                            audio_data = await audio_resp.read()
                                        await context.send(
                                            file=discord.File(fp=io.BytesIO(audio_data), filename="song.mp3")
                                        )
                                        return
                            if any(c.get("state") == "failed" for c in clips):
                                await context.send("Music generation failed.")
                                return

                    await context.send("Music generation timed out.")
        except Exception as e:
            await context.author.send("Could not generate music: " + repr(e))

    async def set_idle_state(message=None):
        name = message if message else "with herself"
        await bot.change_presence(
            activity=discord.Game(name=name), status=discord.Status.online
        )

    async def set_dnd_state(message=None):
        name = message if message else "with herself"
        await bot.change_presence(
            activity=discord.Activity(name=name), status=discord.Status.dnd
        )

    @bot.before_invoke
    async def before_any_command(context):
        await set_dnd_state(f"!{context.command.name}")

    @bot.after_invoke
    async def after_any_command(context):
        await set_idle_state()

    @bot.event
    async def on_ready():
        await set_idle_state()

    bot.run(token)


if __name__ == "__main__":
    main()
