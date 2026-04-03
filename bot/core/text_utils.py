from calendar import month_name
from datetime import datetime
from random import choice
from asyncio import sleep as asleep
from aiohttp import ClientSession
import xml.etree.ElementTree as ET
from anitopy import parse
from bot.core.bot_instance import bot, ani_cache
from config import Var, LOGS
from .ffencoder import ffargs
from .func_utils import handle_logs
from .reporter import rep

_DIV    = "──────────────────────"
_FOOTER = "● ᴜsᴇ <a href='https://play.google.com/store/apps/details?id=org.videolan.vlc'>ᴠʟᴄ</a> ᴏʀ ᴀɴʏ ᴏᴛʜᴇʀ <a href='https://play.google.com/store/apps/details?id=com.mxtech.videoplayer.ad'>ɢᴏᴏᴅ ᴠɪᴅᴇᴏ</a> ᴘʟᴀʏᴇʀ ᴀᴘᴘ ᴛᴏ ᴡᴀᴛᴄʜ ᴛʜᴇ ᴇᴘɪsᴏᴅᴇs ᴡɪᴛʜ ɢᴏᴏᴅ ᴇxᴘᴇʀɪᴇɴᴄᴇ!"

# ── Caption format ─────────────────────────────────────────────────────────────
#
#  PETALS OF REINCARNATION
#  ──────────────────────
#  ➥ Season:  01
#  ➤ Episode: 01
#  ➤ Audio:   Japanese [ESub]
#  ➥ Quality: Multi Quality
#  ──────────────────────
#  ● ᴜsᴇ VLC or any other GOOD VIDEO player …
#
CAPTION_FORMAT = (
    "<b>{english_title}</b>\n"
    f"<b>{_DIV}</b>\n"
    "<b>\u27a5 Season:</b> <code>{anime_season}</code>\n"
    "<b>\u27a4 Episode:</b> <code>{ep_no}</code>\n"
    "<b>\u27a4 Audio:</b> <code>{audio_lang}</code>\n"
    "<b>\u27a5 Quality:</b> <code>{quality_line}</code>\n"
    f"<b>{_DIV}</b>\n"
    + _FOOTER
)

# ── Genre emoji mapping ────────────────────────────────────────────────────────
GENRES_EMOJI = {
    "Action": "👊", "Adventure": choice(["🪂", "🧗\u200d♀️", "🗺️"]), "Comedy": "🤣",
    "Drama": "🎭", "Ecchi": choice(["💋", "🥵"]), "Fantasy": choice(["🧞", "🧙\u200d♂️", "🐉", "🌗"]),
    "Hentai": "🔞", "Horror": "☠️", "Mahou Shoujo": "☯️", "Mecha": "🤖", "Mystery": "🔮",
    "Psychological": "♟️", "Romance": "💞", "Sci-Fi": "🛸", "Slice of Life": choice(["☘️", "🍁"]),
    "Sports": "⚽️", "Supernatural": "🫧", "Thriller": choice(["🥶", "🔪", "🤯"]),
    "Isekai": choice(["🌌", "🌀", "🧙"]), "Historical": "🏯", "Music": "🎶", "Martial Arts": "🥋",
    "School": "🏫", "Military": "🎖️", "Demons": "😈", "Vampire": "🧛\u200d♂️", "Space": "🚀",
    "Game": "🎮", "Crime": "🚓", "Parody": "😂", "Detective": "🕵️\u200d♂️", "Tragedy": "💔",
    "Yaoi": "👨\u200d❤️\u200d👨", "Yuri": "👩\u200d❤️\u200d👩", "Kids": "🧒", "Harem": "👸",
    "Music & Idol": "🎤", "Post-Apocalyptic": "☢️", "Cyberpunk": "💽", "Samurai": "🗡️",
    "Time Travel": "⏳",
}

GENRE_NORMALIZATION = {
    "Action & Adventure": "Action",
    "Romantic Comedy": "Comedy",
    "Shounen": "Action",
    "Shoujo": "Romance",
    "Seinen": "Drama",
    "Josei": "Drama",
    "Slice-of-Life": "Slice of Life",
    "Magical Girl": "Mahou Shoujo",
    "Science Fiction": "Sci-Fi",
    "Psychological Thriller": "Psychological",
    "Suspense": "Thriller",
    "Martial-Arts": "Martial Arts",
    "Fantasy Adventure": "Fantasy",
    "Post Apocalypse": "Post-Apocalyptic",
    "Cyber Punk": "Cyberpunk",
    "Historical Drama": "Historical",
    "Romance Comedy": "Romance",
    "Action Comedy": "Action",
    "Super Power": "Supernatural",
    "Game Based": "Game",
    "Music Idol": "Music & Idol",
    "Sports Drama": "Sports",
    "Military Sci-Fi": "Military",
    "Time-Travel": "Time Travel",
    "Detective Mystery": "Detective",
}

ANIME_GRAPHQL_QUERY = """
query ($id: Int, $search: String, $seasonYear: Int) {
  Media(id: $id, type: ANIME, format_not_in: [MOVIE, MUSIC, MANGA, NOVEL, ONE_SHOT], search: $search, seasonYear: $seasonYear) {
    id
    idMal
    title {
      romaji
      english
      native
    }
    type
    format
    status(version: 2)
    description(asHtml: false)
    startDate {
      year
      month
      day
    }
    endDate {
      year
      month
      day
    }
    season
    seasonYear
    episodes
    duration
    chapters
    volumes
    countryOfOrigin
    source
    hashtag
    trailer {
      id
      site
      thumbnail
    }
    updatedAt
    coverImage {
      large
    }
    bannerImage
    genres
    synonyms
    averageScore
    meanScore
    popularity
    trending
    favourites
    studios {
      nodes {
        name
        siteUrl
      }
    }
    isAdult
    nextAiringEpisode {
      airingAt
      timeUntilAiring
      episode
    }
    airingSchedule {
      edges {
        node {
          airingAt
          timeUntilAiring
          episode
        }
      }
    }
    externalLinks {
      url
      site
    }
    siteUrl
  }
}
"""


def normalize_genres(genres: list) -> list:
    normalized = []
    for genre in genres or []:
        genre_key = GENRE_NORMALIZATION.get(genre, genre)
        if genre_key in GENRES_EMOJI:
            normalized.append(genre_key)
    return normalized


class AniLister:
    def __init__(self, anime_name: str, year: int) -> None:
        self.__api = "https://graphql.anilist.co"
        self.__ani_name = anime_name
        self.__ani_year = year
        self.__vars = {"search": self.__ani_name, "seasonYear": self.__ani_year}

    def __update_vars(self, year: bool = True) -> None:
        if year:
            self.__ani_year -= 1
            self.__vars["seasonYear"] = self.__ani_year
        else:
            self.__vars = {"search": self.__ani_name}

    async def post_data(self):
        async with ClientSession() as sess:
            async with sess.post(self.__api, json={"query": ANIME_GRAPHQL_QUERY, "variables": self.__vars}) as resp:
                return (resp.status, await resp.json(), resp.headers)

    async def get_anidata(self):
        cache_key = f"{self.__ani_name}:{self.__ani_year}"
        if cache_key in ani_cache:
            return ani_cache[cache_key]
        res_code, resp_json, res_heads = await self.post_data()
        while res_code == 404 and self.__ani_year > 2020:
            self.__update_vars()
            await rep.report(f"AniList Query Name: {self.__ani_name}, Retrying with {self.__ani_year}", "warning", log=False)
            res_code, resp_json, res_heads = await self.post_data()
        if res_code == 404:
            self.__update_vars(year=False)
            res_code, resp_json, res_heads = await self.post_data()
        if res_code == 200:
            data = resp_json.get("data", {}).get("Media", {}) or {}
            ani_cache[cache_key] = data
            return data
        elif res_code == 429:
            retry_after = int(res_heads.get("Retry-After", 10))
            await asleep(retry_after * 1.5)
            return await self.get_anidata()
        elif res_code in [500, 501, 502]:
            await asleep(5)
            return await self.get_anidata()
        await rep.report(f"AniList API Error: {res_code}", "error", log=False)
        return {}

    @handle_logs
    async def _parse_anilist_data(self, data):
        if not data or not data.get("data", {}).get("Media"):
            return {}
        anime = data["data"]["Media"]
        genres = normalize_genres(anime.get("genres", []))
        return {
            "id": anime.get("id"),
            "idMal": anime.get("idMal"),
            "title": anime.get("title", {}),
            "status": anime.get("status", "").replace("_", " ").title(),
            "description": anime.get("description"),
            "startDate": anime.get("startDate", {}),
            "endDate": anime.get("endDate", {}),
            "episodes": anime.get("episodes"),
            "genres": genres,
            "averageScore": anime.get("averageScore"),
            "coverImage": anime.get("coverImage", {})
        }

    @handle_logs
    async def get_anilist_id(self, mal_id: int = None, name: str = None, year: int = None):
        if mal_id:
            variables = {"idMal": mal_id}
        else:
            variables = {"search": name, "seasonYear": year} if year else {"search": name}
        res_code, resp_json, res_heads = await self.post_data()
        if res_code == 200 and resp_json.get("data", {}).get("Media"):
            return resp_json["data"]["Media"]["id"]
        elif res_code == 429:
            f_timer = int(res_heads.get("Retry-After", 10))
            await rep.report(f"AniList ID Fetch Rate Limit: Sleeping for {f_timer}s", "error")
            await asleep(f_timer)
            return await self.get_anilist_id(mal_id, name, year)
        await rep.report(f"Failed to fetch AniList ID for {name or mal_id}", "error")
        return None


class TextEditor:
    def __init__(self, name):
        self.__name = name
        self.adata = {}
        self.pdata = parse(name)
        self.anilister = AniLister(self.__name, datetime.now().year)

    async def load_anilist(self):
        cache_names = set()
        variations = [(False, False), (False, True), (True, False), (True, True), "clean"]
        for var in variations:
            if var == "clean":
                ani_name = self.pdata.get("anime_title")
            else:
                no_s, no_y = var
                ani_name = await self.parse_name(no_s, no_y)
            if not ani_name or ani_name in cache_names:
                continue
            cache_names.add(ani_name)
            self.anilister._AniLister__ani_name = ani_name
            self.anilister._AniLister__vars["search"] = ani_name
            self.adata = await self.anilister.get_anidata()
            if self.adata:
                break

    @handle_logs
    async def parse_name(self, no_s=False, no_y=False):
        anime_name = self.pdata.get("anime_title") or self.__name
        anime_season = self.pdata.get("anime_season")
        anime_year = self.pdata.get("anime_year")
        if anime_name:
            pname = anime_name
            if not no_s and self.pdata.get("episode_number") and anime_season:
                pname += f" {anime_season}"
            if not no_y and anime_year:
                pname += f" {anime_year}"
            return pname
        return anime_name

    @handle_logs
    async def get_poster(self):
        anime_id = self.adata.get("id")
        if anime_id and str(anime_id).isdigit():
            return f"https://img.anili.st/media/{anime_id}"
        return "https://envs.sh/YsH.jpg"

    @handle_logs
    async def get_upname(self, qual=""):
        anime_name = self.pdata.get("anime_title")
        codec = "HEVC" if "libx265" in ffargs[qual] else "AV1" if "libaom-av1" in ffargs[qual] else ""
        lang = "SUB" if "sub" in self.__name.lower() else "Sub"
        anime_season = str(ani_s[-1]) if (ani_s := self.pdata.get("anime_season", "01")) and isinstance(ani_s, list) else str(ani_s)
        if anime_name and self.pdata.get("episode_number"):
            titles = self.adata.get("title", {})
            return (
                f"[S{anime_season}-"
                f"{'E'+str(self.pdata.get('episode_number')) if self.pdata.get('episode_number') else ''}] "
                f"{titles.get('english') or titles.get('romaji') or titles.get('native')} "
                f"{'['+qual+'p]' if qual else ''} "
                f"{'['+codec.upper()+'] ' if codec else ''}"
                f"{'['+lang+']'} {Var.BRAND_UNAME}.mkv"
            )
        return None

    @handle_logs
    async def get_caption(self):
        titles = self.adata.get("title", {})

        # ── English title in UPPERCASE
        english_title = (
            titles.get("english") or titles.get("romaji") or titles.get("native") or "N/A"
        ).upper()

        # ── Season number (zero-padded)
        ani_s = self.pdata.get("anime_season", "01")
        anime_season = str(ani_s[-1]) if isinstance(ani_s, list) else str(ani_s)
        try:
            anime_season = str(int(anime_season)).zfill(2)
        except (ValueError, TypeError):
            anime_season = "01"

        # ── Episode number (zero-padded)
        ep_raw = self.pdata.get("episode_number") or "N/A"
        try:
            ep_no = str(int(str(ep_raw))).zfill(2)
        except (ValueError, TypeError):
            ep_no = str(ep_raw)

        # ── Audio language
        lower = self.__name.lower()
        if "dual" in lower or "multi" in lower:
            audio_lang = "Dual Audio"
        elif "dub" in lower:
            audio_lang = "English Dub"
        else:
            audio_lang = "Japanese [ESub]"

        # ── Quality line
        qual_tags = [q for q in ("1080", "720", "480", "360", "HDRip") if q in self.__name]
        if len(qual_tags) > 1 or not qual_tags:
            quality_line = "Multi Quality"
        else:
            quality_line = f"{qual_tags[0]}p"

        return CAPTION_FORMAT.format(
            english_title=english_title,
            anime_season=anime_season,
            ep_no=ep_no,
            audio_lang=audio_lang,
            quality_line=quality_line,
        )
