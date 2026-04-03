import os

class botmaker(object):
    START_MSG = """<b>Bᴀᴋᴀᴀᴀ!!!....{first}\n\n<blockquote>ɪ ᴀᴍ ғɪʟᴇ sᴛᴏʀᴇ + Aᴜᴛᴏ Aɴɪᴍᴇ ʙᴏᴛ, ɪ ᴄᴀɴ sᴛᴏʀᴇ ᴘʀɪᴠᴀᴛᴇ ғɪʟᴇs ɪɴ sᴘᴇᴄɪғɪᴇᴅ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴏᴛʜᴇʀ ᴜsᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss ɪᴛ ғʀᴏᴍ sᴘᴇᴄɪᴀʟ ʟɪɴᴋ.</blockquote></b>"""

    FORCE_MSG = """ʜᴇʟʟᴏ {first}\n\n<b>ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʀᴇʟᴏᴀᴅ button ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛᴇᴅ ꜰɪʟᴇ.</b>"""

    HELP_TXT = """<b><blockquote>ᴛʜɪs ɪs ᴀɴ ғɪʟᴇ ᴛᴏ ʟɪɴᴋ ʙᴏᴛ ᴡᴏʀᴋɪɴɢ ғᴏʀ @Cantarellabots

❏ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs
├ /start : sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ
├ /about : ᴏᴜʀ Iɴғᴏʀᴍᴀᴛɪᴏɴ
└ /help : ʜᴇʟᴘ ʀᴇʟᴀᴛᴇᴅ ʙᴏᴛ

sɪᴍᴘʟʏ ᴄʟɪᴄᴋ ᴏɴ ʟɪɴᴋ ᴀɴᴅ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ, ᴊᴏɪɴ ʙᴏᴛʜ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ — ᴛʜᴀᴛ'ꜱ ɪᴛ.....!</blockquote></b>"""

    ABOUT_TXT = """<b><blockquote>
◈ ᴄʀᴇᴀᴛᴏʀ: <a href="https://t.me/ITSANIMEN">彡 ΔNI_OTΔKU 彡</a>
◈ ᴀɴɪᴍᴇ ᴄʜᴀɴɴᴇʟ: <a href="https://t.me/Anime_z_Flex">ᴀɴɪᴍᴇ_ғʟɪx</a>
◈ Oɴɢᴏɪɴɢ Eɴɢ sᴜʙ/ᴅᴜʙ: <a href="https://t.me/otakuflix_ongoings">Oᴛᴀᴋᴜ-Fʟɪx ᴏɴɢᴏɪɴɢ</a>
</blockquote></b>"""

    CMD_TXT = """‹‹ /stats — Bot uptime
‹‹ /ping — TG + DB latency
‹‹ /users — Total users
‹‹ /log — Download log file

<b>─── Anime Engine ───</b>
‹‹ /pause — Stop RSS fetching
‹‹ /resume — Resume RSS fetching
‹‹ /ongoing — Today's SubsPlease schedule
‹‹ /addlink — Add RSS feed URL
‹‹ /addtask — Trigger anime task manually
‹‹ /add_rss — Add custom RSS link
‹‹ /list_rss — List custom RSS links
‹‹ /remove_rss — Remove custom RSS link
‹‹ /post [query] — Search Nyaa & upload
‹‹ /setchannel — Map anime to channel
‹‹ /listchannels — View anime->channel map
‹‹ /setsticker — Set post-upload sticker

<b>─── File & Links ───</b>
‹‹ /genlink — Generate share link
‹‹ /batch — Batch link (first to last)
‹‹ /custom_batch — Custom batch link
‹‹ /search [name] — Search episodes in DB

<b>─── Broadcast ───</b>
‹‹ /broadcast — Send to all users
‹‹ /pbroadcast — Send + pin message
‹‹ /dbroadcast [secs] — Broadcast + auto-delete

<b>─── Users & Admins ───</b>
‹‹ /ban — Ban user(s)
‹‹ /unban — Unban user(s)
‹‹ /banlist — List banned users
‹‹ /add_admin — Add admin
‹‹ /deladmin — Remove admin
‹‹ /admins — List admins

<b>─── Force Sub ───</b>
‹‹ /addchnl — Add force-sub channel
‹‹ /delchnl — Remove force-sub channel
‹‹ /listchnl — List force-sub channels
‹‹ /fsub_mode — Toggle request mode

<b>─── Settings ───</b>
‹‹ /dlt_time [secs] — Set file auto-delete timer
‹‹ /check_dlt_time — Check current timer
‹‹ /shell [cmd] — Run shell command
‹‹ /restart — Restart bot
"""

    BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"

    # ✅ Custom Caption from environment
    CUSTOM_CAPTION = os.getenv("CUSTOM_CAPTION", None)
