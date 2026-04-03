from dotenv import load_dotenv
load_dotenv()          # must be first

__version__ = "2.0.0"

import pyrogram.utils
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647
