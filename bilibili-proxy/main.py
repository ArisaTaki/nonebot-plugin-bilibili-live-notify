import time
import re
import json
import httpx
from fastapi import FastAPI, Query, HTTPException

app = FastAPI(
    title="Bilibili Live HTML Proxy",
    description="Parse bilibili live status / title / cover from HTML page",
    version="1.1.0",
)

# =========================
# 请求头（模拟真实浏览器）
# =========================
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://live.bilibili.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

LIVE_PAGE_URL = "https://live.bilibili.com/{room_id}"

# =========================
# 预编译正则（稳定 & 高效）
# =========================
LIVE_STATUS_RE = re.compile(r'"live_status"\s*:\s*(\d)')
TITLE_RE = re.compile(r'"title"\s*:\s*"([^"]+)"')
COVER_RE = re.compile(r'"cover"\s*:\s*"([^"]+)"')
USER_COVER_RE = re.compile(r'"user_cover"\s*:\s*"([^"]+)"')


@app.get("/bilibili/live")
async def bilibili_live(
    room_id: int = Query(..., description="Bilibili live room id")
):
    url = LIVE_PAGE_URL.format(room_id=room_id)

    # -------------------------
    # 请求直播页 HTML
    # -------------------------
    try:
        async with httpx.AsyncClient(
            headers=HEADERS,
            timeout=10,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"request failed: {e}")

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"bad status code: {resp.status_code}",
        )

    html = resp.text

    # -------------------------
    # 解析直播状态
    # -------------------------
    live_match = LIVE_STATUS_RE.search(html)
    if not live_match:
        raise HTTPException(
            status_code=502,
            detail="live_status not found in html",
        )

    live_status = int(live_match.group(1))
    is_live = live_status == 1

    # -------------------------
    # 解析标题（可选）
    # -------------------------
    title = None
    title_match = TITLE_RE.search(html)
    if title_match:
        title = title_match.group(1)

    # -------------------------
    # 解析封面（JSON 转义 → 反转义）
    # -------------------------
    cover = None
    raw_cover = None

    cover_match = COVER_RE.search(html)
    if cover_match:
        raw_cover = cover_match.group(1)
    else:
        user_cover_match = USER_COVER_RE.search(html)
        if user_cover_match:
            raw_cover = user_cover_match.group(1)

    if raw_cover:
        try:
            # 关键点：把字符串当作 JSON 再解析一次
            cover = json.loads(f'"{raw_cover}"')
        except Exception:
            cover = raw_cover

    # -------------------------
    # 返回稳定、自定义协议
    # -------------------------
    return {
        "ok": True,
        "room_id": room_id,
        "is_live": is_live,
        "live_status": live_status,
        "title": title,
        "cover": cover,
        "source": "html",
        "checked_at": int(time.time()),
    }
