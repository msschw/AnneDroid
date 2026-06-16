import sys
import os
import re
import random
import urllib.parse
import asyncio
from datetime import timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "AnneDroid"))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "AnneDroid", ".env"))


# ---------------------------------------------------------------------------
# !timer – time-string parsing (pure logic, no network)
# ---------------------------------------------------------------------------
def parse_timer(time_str):
    regex = re.compile(
        r"((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?"
    )
    parts = regex.match(time_str)
    if not parts:
        return None
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params) if time_params else None


class TestTimerParsing:
    def test_parse_hours_minutes_seconds(self):
        assert parse_timer("1h30m15s") == timedelta(hours=1, minutes=30, seconds=15)

    def test_parse_minutes_only(self):
        assert parse_timer("45m") == timedelta(minutes=45)

    def test_parse_hours_only(self):
        assert parse_timer("2h") == timedelta(hours=2)

    def test_parse_seconds_only(self):
        assert parse_timer("10s") == timedelta(seconds=10)

    def test_parse_invalid_string(self):
        assert parse_timer("abc") is None

    def test_parse_complex(self):
        assert parse_timer("99h99m99s") == timedelta(hours=99, minutes=99, seconds=99)


# ---------------------------------------------------------------------------
# !timer – integration (real asyncio.sleep)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_timer_duration_is_computed_correctly():
    time_str = "0h0m1s"
    regex = re.compile(r"((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?")
    parts = regex.match(time_str).groupdict()
    time_params = {k: int(v) for k, v in parts.items() if v}
    duration = timedelta(**time_params)
    assert duration == timedelta(seconds=1)


@pytest.mark.asyncio
async def test_timer_invalid_format_produces_zero_duration():
    time_str = "not_a_valid_time"
    regex = re.compile(r"((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?")
    parts = regex.match(time_str).groupdict()
    time_params = {k: int(v) for k, v in parts.items() if v}
    duration = timedelta(**time_params)
    assert duration == timedelta(0)


# ---------------------------------------------------------------------------
# !google – DuckDuckGo search (real endpoint)
# ---------------------------------------------------------------------------
import ddgs


class TestGoogleCommand:
    def test_google_returns_result_for_known_query(self):
        query = "python programming language"
        with ddgs.DDGS() as ddg:
            results = ddg.text(query, max_results=1)
        assert len(results) > 0
        assert "title" in results[0]
        assert "href" in results[0]

    def test_google_returns_empty_for_bogus_query(self):
        query = "asdfghjkl12345qwertz"
        with ddgs.DDGS() as ddg:
            results = ddg.text(query, max_results=1)
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# !wiki – Wikipedia search (real endpoint)
# ---------------------------------------------------------------------------
import wikipedia


# Patch wikipedia's request function to handle 429 gracefully
import wikipedia.wikipedia as _wiki_mod

_original_request = _wiki_mod._wiki_request


def _patched_wiki_request(params):
    import requests as _req
    params["format"] = "json"
    params.setdefault("action", "query")
    url = _wiki_mod.API_URL.replace("http://", "https://")
    headers = {
        "User-Agent": "AnneDroidTest/1.0 (annedroid-test@example.com)"
    }
    resp = _req.get(url, params=params, headers=headers, timeout=10)
    if resp.status_code != 200:
        pytest.skip(f"Wikipedia API returned {resp.status_code}")
    return resp.json()


_wiki_mod._wiki_request = _patched_wiki_request


class TestWikiCommand:
    def test_wiki_returns_result_for_known_query(self):
        results = wikipedia.search("Python (programming language)")
        assert len(results) > 0
        page = wikipedia.page(results[0])
        assert page.title
        assert page.url.startswith("https://en.wikipedia.org/")

    def test_wiki_handles_disambiguation_gracefully(self):
        """page() should either return a result or raise DisambiguationError."""
        try:
            page = wikipedia.page("Python")
            assert page.title
            assert page.url
        except wikipedia.exceptions.DisambiguationError:
            pass

    def test_wiki_disambiguation_returns_best_match(self):
        results = wikipedia.search("Money")
        assert len(results) > 0
        try:
            page = wikipedia.page(results[0])
        except wikipedia.exceptions.DisambiguationError as de:
            assert len(de.options) > 0
            for option in de.options:
                try:
                    page = wikipedia.page(option)
                    assert page.title
                    assert page.url
                    url = (
                        "https://en.wikipedia.org/wiki/"
                        + urllib.parse.quote(option.replace(" ", "_"))
                    )
                    assert url.startswith("https://en.wikipedia.org/wiki/")
                    break
                except (wikipedia.exceptions.DisambiguationError,
                        wikipedia.exceptions.PageError):
                    continue
            else:
                assert False, "no non-disambiguation option found"

    def test_wiki_returns_empty_for_bogus_query(self):
        results = wikipedia.search("xyznonexistentpage123456")
        assert len(results) == 0


# ---------------------------------------------------------------------------
# !yt – YouTube search (real endpoint)
# ---------------------------------------------------------------------------
import youtube_search


class TestYtCommand:
    def test_yt_returns_result_for_known_query(self):
        results = youtube_search.YoutubeSearch(
            search_terms="never gonna give you up", max_results=1
        )
        assert len(results.videos) > 0
        video = results.videos[0]
        assert "title" in video
        assert "url_suffix" in video
        assert video["url_suffix"].startswith("/watch?v=")

    def test_yt_returns_empty_for_bogus_query(self):
        results = youtube_search.YoutubeSearch(
            search_terms="xyznonexistentvideo123456", max_results=1
        )
        assert isinstance(results.videos, list)


# ---------------------------------------------------------------------------
# !imdb – IMDb search (real endpoint, if module is importable)
# ---------------------------------------------------------------------------
try:
    import imdb as imdblib

    HAS_IMDB = True
except ImportError:
    HAS_IMDB = False


@pytest.mark.skipif(not HAS_IMDB, reason="imdb module not available on this Python version")
class TestImdbCommand:
    def test_imdb_returns_result_for_known_query(self):
        imdb = imdblib.IMDb()
        matches = imdb.search_movie("The Matrix")
        assert len(matches) > 0
        assert matches[0]["title"]
        url = imdb.get_imdbURL(matches[0])
        assert url.startswith("https://www.imdb.com/")

    def test_imdb_returns_empty_for_bogus_query(self):
        imdb = imdblib.IMDb()
        matches = imdb.search_movie("xyznonexistentmovie123456")
        assert len(matches) == 0


# ---------------------------------------------------------------------------
# !gem – Gemini (real endpoint, requires GEMINI_API_KEY)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

try:
    import google.genai as genai

    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


@pytest.mark.skipif(
    not HAS_GENAI or not GEMINI_API_KEY,
    reason="requires GEMINI_API_KEY and google-genai",
)
def _gemini_request(contents):
    """Call Gemini, skipping on transient or rate-limit errors."""
    import google.genai.errors as _ge
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        return client.models.generate_content(
            model="gemini-2.0-flash", contents=contents
        )
    except (_ge.ServerError, _ge.ClientError) as e:
        pytest.skip(f"Gemini API transient error: {e}")


class TestGemCommand:
    @pytest.mark.asyncio
    async def test_gem_returns_response(self):
        response = _gemini_request("Say hello in one word")
        assert response.text
        assert len(response.text) > 0

    @pytest.mark.asyncio
    async def test_gem_chunks_long_responses(self):
        response = _gemini_request("Write a paragraph about Python programming")
        text = response.text
        chunks = [text[i : i + 2000] for i in range(0, len(text), 2000)]
        assert len(chunks) >= 1
        assert all(len(c) <= 2000 for c in chunks)
        assert "".join(chunks) == text


# ---------------------------------------------------------------------------
# !groq – Groq (real endpoint, requires GROQ_API_KEY)
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

try:
    from groq import AsyncGroq

    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


@pytest.mark.skipif(
    not HAS_GROQ or not GROQ_API_KEY,
    reason="requires GROQ_API_KEY and groq",
)
class TestGroqCommand:
    @pytest.mark.asyncio
    async def test_groq_returns_response(self):
        client = AsyncGroq(api_key=GROQ_API_KEY)
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say hello in one word"}],
        )
        text = response.choices[0].message.content
        assert text
        assert len(text) > 0

    @pytest.mark.asyncio
    async def test_groq_chunks_long_responses(self):
        client = AsyncGroq(api_key=GROQ_API_KEY)
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": "Write a paragraph about Python programming"}
            ],
        )
        text = response.choices[0].message.content
        chunks = [text[i : i + 2000] for i in range(0, len(text), 2000)]
        assert len(chunks) >= 1
        assert all(len(c) <= 2000 for c in chunks)
        assert "".join(chunks) == text


# ---------------------------------------------------------------------------
# !gpt – text.pollinations.ai (free, no auth)
# ---------------------------------------------------------------------------
class TestGptCommand:
    @pytest.mark.asyncio
    async def test_gpt_returns_response(self):
        import aiohttp
        prompt = "Say hello in one word"
        url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                assert resp.status == 200
                text = await resp.text()
        assert text
        assert len(text) > 0

    @pytest.mark.asyncio
    async def test_gpt_chunks_long_responses(self):
        import aiohttp
        prompt = "Write a paragraph about Python programming"
        url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                assert resp.status == 200
                text = await resp.text()
        chunks = [text[i : i + 2000] for i in range(0, len(text), 2000)]
        assert len(chunks) >= 1
        assert all(len(c) <= 2000 for c in chunks)
        assert "".join(chunks) == text


# ---------------------------------------------------------------------------
# !wa – WolframAlpha (real endpoint, requires WOLFRAMALPHA_API_KEY)
# ---------------------------------------------------------------------------
WOLFRAMALPHA_API_KEY = os.getenv("WOLFRAMALPHA_API_KEY")

try:
    import wolframalpha

    HAS_WA = True
except ImportError:
    HAS_WA = False


@pytest.mark.skipif(
    not HAS_WA or not WOLFRAMALPHA_API_KEY,
    reason="requires WOLFRAMALPHA_API_KEY and wolframalpha",
)
class TestWaCommand:
    @pytest.mark.asyncio
    async def test_wa_api_is_reachable(self):
        import httpx
        async with httpx.AsyncClient() as http:
            resp = await http.get(
                "https://api.wolframalpha.com/v2/query",
                params={
                    "appid": WOLFRAMALPHA_API_KEY,
                    "input": "2+2",
                    "format": "plaintext",
                },
            )
            assert resp.status_code == 200
            assert "plaintext" in resp.text


# ---------------------------------------------------------------------------
# !protondb – Steam search + ProtonDB rating (real endpoints, no auth)
# ---------------------------------------------------------------------------
class TestProtondbCommand:
    @pytest.mark.asyncio
    async def test_protondb_returns_rating_for_known_game(self):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            params = {"term": "Half-Life 2", "cc": "us", "l": "en"}
            async with session.get(
                "https://store.steampowered.com/api/storesearch",
                params=params,
            ) as resp:
                data = await resp.json()

            items = data.get("items", [])
            assert len(items) > 0
            game_id = items[0]["id"]
            assert game_id == 220

            async with session.get(
                f"https://www.protondb.com/api/v1/reports/summaries/{game_id}.json"
            ) as resp:
                rating_data = await resp.json()

            assert "tier" in rating_data
            assert rating_data["tier"] in (
                "platinum", "gold", "silver", "bronze", "borked"
            )
            assert "confidence" in rating_data
            assert "total" in rating_data

    @pytest.mark.asyncio
    async def test_protondb_shows_no_rating_when_unavailable(self):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            params = {"term": "Halo", "cc": "us", "l": "en"}
            async with session.get(
                "https://store.steampowered.com/api/storesearch",
                params=params,
            ) as resp:
                data = await resp.json()

            items = data.get("items", [])
            assert len(items) >= 1

            first_id = items[0]["id"]
            async with session.get(
                f"https://www.protondb.com/api/v1/reports/summaries/{first_id}.json"
            ) as resp:
                assert resp.status != 200, (
                    "first result should lack a ProtonDB rating "
                    "for this test to be meaningful"
                )

    @pytest.mark.asyncio
    async def test_protondb_handles_bogus_query(self):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            params = {"term": "xyznonexistentgame123456", "cc": "us", "l": "en"}
            async with session.get(
                "https://store.steampowered.com/api/storesearch",
                params=params,
            ) as resp:
                data = await resp.json()

            items = data.get("items", [])
            assert len(items) == 0


# ---------------------------------------------------------------------------
# !metacritic – Metacritic score from metacritic.com (no auth, scraped)
# ---------------------------------------------------------------------------
class TestMetacriticCommand:
    @pytest.mark.asyncio
    async def test_metacritic_returns_score_for_known_game(self):
        import aiohttp, urllib.parse
        from bs4 import BeautifulSoup

        slug = urllib.parse.quote("half-life-2")
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
                assert resp.status == 200
                html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")
            items = soup.select(".search-item")
            assert len(items) > 0

            name_el = items[0].select_one(".c-search-item__title")
            score_el = items[0].select_one(".c-siteReviewScore span")
            assert name_el is not None
            assert score_el is not None
            score = score_el.get_text(strip=True)
            assert score.isdigit(), (
                f"first result should have a numeric score, got {score!r}"
            )
            assert name_el.get_text(strip=True) == "Half-Life 2"

    @pytest.mark.asyncio
    async def test_metacritic_handles_bogus_query(self):
        import aiohttp, urllib.parse
        from bs4 import BeautifulSoup

        slug = urllib.parse.quote("xyznonexistentgame123456")
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
                assert resp.status == 200
                html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")
            items = soup.select(".search-item")
            assert len(items) == 0
