from asyncio import (
    create_task, create_subprocess_exec, create_subprocess_shell,
    run as asyrun, all_tasks, gather, sleep as asleep
)
from aiofiles import open as aiopen
from aiohttp import web
from pyrogram import idle
from pyrogram.filters import command, user
from os import path as ospath, execl, kill, environ
from sys import executable
from signal import SIGKILL
import logging
import static_ffmpeg
static_ffmpeg.add_paths()

from bot.core.bot_instance import bot, bot_loop, sch, ffQueue, ffLock, ffpids_cache, ff_queued
from bot.core.reporter import rep
from config import Var, LOGS
from bot.core.auto_animes import fetch_animes
from bot.core.func_utils import clean_up, new_task, editMessage
from bot.plugins.up_posts import upcoming_animes
from bot.web import web_server, set_state

# Attach reporter to bot
bot.rep = rep


@bot.on_message(command('restart') & user(Var.ADMINS))
@new_task
async def restart(client, message):
    rmessage = await message.reply('<i>Restarting...</i>')
    if sch.running:
        sch.shutdown(wait=False)
    await clean_up()
    for pid in list(ffpids_cache):
        try:
            kill(pid, SIGKILL)
        except (OSError, ProcessLookupError):
            pass
    await (await create_subprocess_exec('python3', 'update.py')).wait()
    async with aiopen(".restartmsg", "w") as f:
        await f.write(f"{rmessage.chat.id}\n{rmessage.id}\n")
    set_state(status="starting")
    execl(executable, executable, "-m", "bot")


async def restart_bot():
    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            lines = f.readlines()
            chat_id, msg_id = map(int, lines)
        try:
            await bot.edit_message_text(
                chat_id=chat_id, message_id=msg_id, text="<i>Restarted!</i>"
            )
        except Exception as e:
            LOGS.error(e)


async def queue_loop():
    LOGS.info("Queue Loop Started!!")
    while True:
        if not ffQueue.empty():
            post_id = await ffQueue.get()
            await asleep(1.5)
            ff_queued[post_id].set()
            await asleep(1.5)
            ffQueue.task_done()
        await asleep(10)


async def main():
    # ── Start web server first so Render health-checks pass immediately ──
    PORT = int(environ.get("PORT", 8080))
    runner = web.AppRunner(await web_server())
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    LOGS.info(f"Web server listening on port {PORT}")

    # Schedule daily anime post
    sch.add_job(upcoming_animes, "cron", hour=0, minute=30)

    await bot.start()

    # Record uptime start
    from datetime import datetime
    bot.uptime = datetime.now()

    # Set bot username
    try:
        me = await bot.get_me()
        bot.username = me.username
        set_state(bot_username=me.username, status="online")
        LOGS.info(f"Bot username set to @{bot.username}")
    except Exception as e:
        LOGS.error(f"Failed to set bot username: {e}")
        set_state(status="error")
        await bot.stop()
        return

    await restart_bot()
    LOGS.info("Auto Anime Bot Started!")

    # Verify DB channel
    try:
        db_channel = await bot.get_chat(Var.CHANNEL_ID)
        test_msg = await bot.send_message(chat_id=db_channel.id, text="✅ Startup Test")
        await test_msg.delete()
        bot.db_channel = db_channel
    except Exception as e:
        await bot.rep.report(f"❌ MAIN_CHANNEL error: {e}", "critical")
        set_state(status="error")
        await bot.stop()
        return

    try:
        await bot.send_message(Var.ADMINS, "<b><blockquote>✅ Bᴏᴛ Rᴇsᴛᴀʀᴛᴇᴅ</blockquote></b>")
    except Exception:
        pass

    sch.start()
    bot_loop.create_task(queue_loop())

    await fetch_animes()
    await idle()

    LOGS.info("Auto Anime Bot Stopped!")
    set_state(status="error")
    await bot.stop()
    for task in all_tasks():
        task.cancel()
    await clean_up()
    await runner.cleanup()
    LOGS.info("Finished AutoCleanUp!!")


if __name__ == '__main__':
    bot_loop.run_until_complete(main())
