import asyncio
import threading
import os
from flask import Flask

# 🔥 Flask app for Render
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running 🚀", 200


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Flask running on port {port}")
    app.run(host="0.0.0.0", port=port)


# 🔥 Your bot import
from bot.__main__ import main as bot_main, bot_loop


def run_bot():
    bot_loop.run_until_complete(bot_main())


if __name__ == "__main__":
    # ✅ Start Flask FIRST (Render detects this)
    threading.Thread(target=run_flask, daemon=True).start()

    # ✅ Run bot
    run_bot()
