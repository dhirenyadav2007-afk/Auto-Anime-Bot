import logging
from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message
from bot.Script import botmaker
from bot.core.bot_instance import bot
from helper_func import admin, get_readable_time
from bot.core.database import db
from config import Var

logger = logging.getLogger(__name__)

WAIT_MSG = "<b>Working....</b>"


@bot.on_message(filters.command("stats") & filters.private & admin)
async def bot_stats(client, message: Message):
    now = datetime.now()
    if hasattr(bot, "uptime"):
        delta = now - bot.uptime
        uptime_str = get_readable_time(delta.seconds)
    else:
        uptime_str = "N/A (uptime not tracked yet)"
    await message.reply(botmaker.BOT_STATS_TEXT.format(uptime=uptime_str))


@bot.on_message(filters.command("users") & filters.private & admin)
async def get_users(client, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await db.full_userbase()
    await msg.edit(f"<b>{len(users)} users</b> are using this bot")


@bot.on_message(filters.private & filters.command("dlt_time") & admin)
async def set_delete_time(client, message: Message):
    try:
        duration = int(message.command[1])
        await db.set_del_timer(duration)
        await message.reply(
            f"<b>Delete Timer set to <blockquote>{duration} seconds.</blockquote></b>"
        )
    except (IndexError, ValueError):
        await message.reply(
            "<b>Usage:</b> <code>/dlt_time {seconds}</code>"
        )


@bot.on_message(filters.private & filters.command("check_dlt_time") & admin)
async def check_delete_time(client, message: Message):
    duration = await db.get_del_timer()
    await message.reply(
        f"<b><blockquote>Current delete timer: {duration} seconds.</blockquote></b>"
    )


@bot.on_message(filters.private & filters.command("log") & filters.user(Var.ADMINS))
async def send_log(client, message: Message):
    try:
        with open("log.txt", "rb") as f:
            await client.send_document(
                message.chat.id, f, caption="<b>📄 Bot Log File</b>",
                reply_to_message_id=message.id
            )
    except FileNotFoundError:
        await message.reply("<b>No log file found.</b>")
    except Exception as e:
        await message.reply(f"<b>Error:</b> <code>{e}</code>")
