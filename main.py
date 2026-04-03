from bot.__main__ import main, bot_loop
import pyrogram.utils

pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

if __name__ == "__main__":
    bot_loop.run_until_complete(main())