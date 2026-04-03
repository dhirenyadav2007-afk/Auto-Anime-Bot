"""
up_posts.py — Scheduled anime schedule poster + stats/ping/shell/ongoing commands.
"""
import time
import subprocess
import logging
from datetime import datetime
from json import loads as jloads

from aiohttp import ClientSession
from motor.motor_asyncio import AsyncIOMotorClient

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.filters import command, private, user
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from config import Var
from bot.core.bot_instance import bot, bot_loop, ani_cache, ffQueue
from bot.core.text_utils import TextEditor
from bot.core.reporter import rep
from bot.core.func_utils import decode, editMessage, sendMessage, new_task, convertTime, getfeed

LOGGER = logging.getLogger(__name__)

# MongoDB ping helper (for /ping command)
DB_URI = Var.DB_URI
_mongo_client = AsyncIOMotorClient(DB_URI)
_db = _mongo_client["AutoAniOngoing"]


def get_readable_time(seconds: int) -> str:
    count, up_time = 0, ""
    time_list = []
    suffix = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = (
            divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        )
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for i in range(len(time_list)):
        time_list[i] = str(time_list[i]) + suffix[i]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time


async def _db_ping() -> float:
    start = time.time()
    await _db.command("ping")
    return round((time.time() - start) * 1000, 2)


async def _tg_ping() -> float:
    start = time.time()
    await bot.get_me()
    return round((time.time() - start) * 1000, 2)


# ── /ping ────────────────────────────────────────────────────────────────────
@bot.on_message(filters.command("ping") & filters.user(Var.ADMINS))
@new_task
async def ping_cmd(client: Client, message: Message):
    try:
        now = datetime.now()
        if hasattr(bot, "uptime"):
            uptime = get_readable_time((now - bot.uptime).seconds)
        else:
            uptime = "N/A"
        tg_ping = await _tg_ping()
        db_ping = await _db_ping()
        await message.reply_text(
            f"<b>🏓 Pong!</b>\n"
            f"<b>Bot Uptime:</b> <code>{uptime}</code>\n"
            f"<b>TG Ping:</b> <code>{tg_ping} ms</code>\n"
            f"<b>DB Ping:</b> <code>{db_ping} ms</code>"
        )
    except Exception as e:
        await message.reply_text(f"Error: {e}")


# ── /shell ────────────────────────────────────────────────────────────────────
@bot.on_message(filters.command("shell") & filters.private & filters.user(Var.ADMINS))
@new_task
async def shell_cmd(client: Client, message: Message):
    parts = message.text.split(" ", 1)
    if len(parts) == 1:
        return await message.reply_text("No command given.")
    cmd = parts[1]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = proc.communicate()
    reply = ""
    if stdout:
        reply += f"<b>stdout:</b>\n<code>{stdout.decode()}</code>\n"
    if stderr:
        reply += f"<b>stderr:</b>\n<code>{stderr.decode()}</code>\n"
    if not reply:
        reply = "No output."
    if len(reply) > 4000:
        with open("shell_output.txt", "w") as fh:
            fh.write(reply)
        with open("shell_output.txt", "rb") as doc:
            await client.send_document(message.chat.id, doc, reply_to_message_id=message.id)
    else:
        await message.reply_text(reply)


# ── /ongoing ─────────────────────────────────────────────────────────────────
@bot.on_message(filters.command("ongoing"))
@new_task
async def ongoing_animes(client: Client, message: Message):
    if not Var.SEND_SCHEDULE:
        return await message.reply_text("Schedule posting is disabled.")
    try:
        async with ClientSession() as ses:
            res = await ses.get(
                "https://subsplease.org/api/?f=schedule&h=true&tz=Asia/Kolkata"
            )
            data = jloads(await res.text())["schedule"]
        text = "<b><blockquote>📆 Today's Anime Schedule [IST]</blockquote></b>\n\n"
        for item in data:
            aname = TextEditor(item["title"])
            await aname.load_anilist()
            eng = aname.adata.get("title", {}).get("english") or item["title"]
            text += (
                f'<b><blockquote>'
                f'<a href="https://subsplease.org/shows/{item["page"]}">{eng}</a>\n'
                f'    • <b>Time:</b> {item["time"]} IST\n'
                f'</blockquote></b>\n'
            )
        await message.reply_text(text)
    except Exception as err:
        await message.reply_text(f"Error: {err}")


# ── Scheduled daily post (called by scheduler at 00:30 IST) ──────────────────
TD_SCHR = None


async def upcoming_animes():
    """Post today's anime schedule to MAIN_CHANNEL. Called by APScheduler."""
    global TD_SCHR
    if not Var.SEND_SCHEDULE:
        return
    try:
        async with ClientSession() as ses:
            res = await ses.get(
                "https://subsplease.org/api/?f=schedule&h=true&tz=Asia/Kolkata"
            )
            data = jloads(await res.text())["schedule"]
        text = "<b><blockquote>📆 Today's Anime Schedule [IST]</blockquote></b>\n\n"
        for item in data:
            aname = TextEditor(item["title"])
            await aname.load_anilist()
            eng = aname.adata.get("title", {}).get("english") or item["title"]
            text += (
                f'<b><blockquote>'
                f'<a href="https://subsplease.org/shows/{item["page"]}">{eng}</a>\n'
                f'    • <b>Time:</b> {item["time"]} IST\n'
                f'</blockquote></b>\n'
            )
        TD_SCHR = await bot.send_message(Var.MAIN_CHANNEL, text)
        await (await TD_SCHR.pin()).delete()
        await rep.report("Daily schedule posted successfully.", "info", log=True)
    except Exception as err:
        await rep.report(f"upcoming_animes error: {err}", "error", log=True)
