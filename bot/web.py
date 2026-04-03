"""
Web server for health checks and status dashboard.
Render / Railway / Koyeb keep the service alive by hitting GET /
"""

import time
from datetime import datetime, timedelta
from aiohttp import web

routes = web.RouteTableDef()

# ── shared state populated by bot/__main__.py ─────────────────────────────
_bot_state: dict = {
    "status": "starting",      # starting | online | error
    "start_time": time.time(),
    "bot_username": None,
    "processed_total": 0,
    "last_anime": None,
    "last_anime_time": None,
}


def get_state() -> dict:
    return _bot_state


def set_state(**kwargs):
    _bot_state.update(kwargs)


def _uptime_str() -> str:
    delta = timedelta(seconds=int(time.time() - _bot_state["start_time"]))
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


# ── HTML dashboard ────────────────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="30">
<title>Auto Anime Bot — Status</title>
<style>
  :root {{
    --bg:#0d1117;--card:#161b22;--border:#30363d;
    --green:#3fb950;--yellow:#d29922;--red:#f85149;
    --blue:#58a6ff;--text:#c9d1d9;--muted:#8b949e;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:2rem}}
  h1{{font-size:1.6rem;color:var(--blue);margin-bottom:.3rem}}
  .subtitle{{color:var(--muted);margin-bottom:2rem;font-size:.9rem}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:2rem}}
  .card{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:1.2rem}}
  .card-label{{font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:.5rem}}
  .card-value{{font-size:1.5rem;font-weight:700}}
  .badge{{display:inline-flex;align-items:center;gap:.4rem;padding:.25rem .7rem;border-radius:20px;font-size:.8rem;font-weight:600}}
  .badge-green{{background:rgba(63,185,80,.15);color:var(--green)}}
  .badge-yellow{{background:rgba(210,153,34,.15);color:var(--yellow)}}
  .badge-red{{background:rgba(248,81,73,.15);color:var(--red)}}
  .dot{{width:8px;height:8px;border-radius:50%;background:currentColor}}
  .section-title{{font-size:1rem;font-weight:600;margin-bottom:.8rem}}
  .info-row{{display:flex;justify-content:space-between;padding:.5rem 0;border-bottom:1px solid var(--border);font-size:.875rem}}
  .info-row:last-child{{border-bottom:none}}
  .info-key{{color:var(--muted)}}
  .info-val{{font-weight:500}}
  footer{{margin-top:2rem;color:var(--muted);font-size:.75rem;text-align:center}}
  a{{color:var(--blue);text-decoration:none}}
</style>
</head>
<body>
<h1>🎌 Auto Anime Bot</h1>
<p class="subtitle">Live status dashboard — auto-refreshes every 30 s &nbsp;|&nbsp; <a href="/health">JSON health API</a></p>

<div class="grid">
  <div class="card">
    <div class="card-label">Status</div>
    <div class="card-value">{status_badge}</div>
  </div>
  <div class="card">
    <div class="card-label">Uptime</div>
    <div class="card-value" style="font-size:1.1rem;color:var(--blue)">{uptime}</div>
  </div>
  <div class="card">
    <div class="card-label">Encode Queue</div>
    <div class="card-value" style="color:{queue_color}">{queue_size}</div>
  </div>
  <div class="card">
    <div class="card-label">Animes Processed</div>
    <div class="card-value" style="color:var(--green)">{processed}</div>
  </div>
</div>

<div class="card" style="margin-bottom:1rem">
  <div class="section-title">📡 Bot Details</div>
  <div class="info-row"><span class="info-key">Username</span><span class="info-val">{username}</span></div>
  <div class="info-row"><span class="info-key">Fetch Enabled</span><span class="info-val">{fetch_status}</span></div>
  <div class="info-row"><span class="info-key">Ongoing IDs</span><span class="info-val">{ongoing}</span></div>
  <div class="info-row"><span class="info-key">Completed IDs</span><span class="info-val">{completed}</span></div>
  <div class="info-row"><span class="info-key">Custom RSS Feeds</span><span class="info-val">{rss_count}</span></div>
  <div class="info-row"><span class="info-key">Last Anime</span><span class="info-val">{last_anime}</span></div>
  <div class="info-row"><span class="info-key">Last Activity</span><span class="info-val">{last_time}</span></div>
  <div class="info-row"><span class="info-key">Encode Lock</span><span class="info-val">{ff_lock}</span></div>
  <div class="info-row"><span class="info-key">Server Time (IST)</span><span class="info-val">{server_time}</span></div>
</div>

<footer>Auto Anime Bot &copy; {year} &nbsp;|&nbsp; Powered by SubsPlease + AniList</footer>
</body>
</html>"""


@routes.get("/", allow_head=True)
async def dashboard(request: web.Request) -> web.Response:
    try:
        from bot.core.bot_instance import ani_cache, ffQueue, ffLock
        queue_size = ffQueue.qsize()
        ongoing    = len(ani_cache.get("ongoing", set()))
        completed  = len(ani_cache.get("completed", set()))
        rss_count  = len(ani_cache.get("custom_rss", set()))
        fetch_on   = ani_cache.get("fetch_animes", False)
        ff_locked  = ffLock.locked()
    except Exception:
        queue_size = ongoing = completed = rss_count = 0
        fetch_on   = False
        ff_locked  = False

    status = _bot_state["status"]
    if status == "online":
        badge = '<span class="badge badge-green"><span class="dot"></span>Online</span>'
    elif status == "starting":
        badge = '<span class="badge badge-yellow"><span class="dot"></span>Starting…</span>'
    else:
        badge = '<span class="badge badge-red"><span class="dot"></span>Error</span>'

    try:
        import pytz
        ist = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        ist = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    last_anime   = _bot_state.get("last_anime") or "—"
    last_time_ts = _bot_state.get("last_anime_time")
    last_time    = datetime.fromtimestamp(last_time_ts).strftime("%H:%M:%S") if last_time_ts else "—"

    html = HTML_TEMPLATE.format(
        status_badge=badge,
        uptime=_uptime_str(),
        queue_size=queue_size,
        queue_color="var(--yellow)" if queue_size > 0 else "var(--green)",
        processed=_bot_state.get("processed_total", 0),
        username=f"@{_bot_state['bot_username']}" if _bot_state.get("bot_username") else "—",
        fetch_status="✅ Enabled" if fetch_on else "⏸ Paused",
        ongoing=ongoing,
        completed=completed,
        rss_count=rss_count,
        last_anime=last_anime,
        last_time=last_time,
        ff_lock="🔒 Locked" if ff_locked else "🔓 Free",
        server_time=ist,
        year=datetime.now().year,
    )
    return web.Response(text=html, content_type="text/html")


@routes.get("/health")
async def health_json(request: web.Request) -> web.Response:
    try:
        from bot.core.bot_instance import ani_cache, ffQueue, ffLock
        queue_size = ffQueue.qsize()
        ongoing    = len(ani_cache.get("ongoing", set()))
        completed  = len(ani_cache.get("completed", set()))
        ff_locked  = ffLock.locked()
    except Exception:
        queue_size = ongoing = completed = 0
        ff_locked  = False

    payload = {
        "status":          _bot_state["status"],
        "uptime":          _uptime_str(),
        "uptime_seconds":  int(time.time() - _bot_state["start_time"]),
        "bot_username":    _bot_state.get("bot_username"),
        "queue_size":      queue_size,
        "ongoing":         ongoing,
        "completed":       completed,
        "encode_locked":   ff_locked,
        "processed_total": _bot_state.get("processed_total", 0),
        "last_anime":      _bot_state.get("last_anime"),
        "timestamp":       int(time.time()),
    }
    http_status = 200 if _bot_state["status"] == "online" else 503
    return web.json_response(payload, status=http_status)


async def web_server() -> web.Application:
    app = web.Application(client_max_size=30_000_000)
    app.add_routes(routes)
    return app
