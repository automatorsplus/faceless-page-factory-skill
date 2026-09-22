#!/usr/bin/env python3
"""What is going viral in a niche this week. YouTube sorted by views, this week, no key, no cost; TikTok too when
APIFY_TOKEN is set. Writes <page or cwd>/research.md as a table and prints it. Claude then writes the clip ideas
in chat, each pointing at a row here.

    python3 research.py "satisfying physics"
    python3 research.py "satisfying physics" --also "oddly satisfying" --also "asmr simulation" --limit 20
    python3 research.py "..." --any-length          keep long videos too (default keeps 90 seconds and under)
    python3 research.py "..." --page <folder>       write research.md into that page folder
"""
from __future__ import annotations
import argparse, datetime, json, os, pathlib, shutil, subprocess, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_env

# YouTube results page, sorted by view count, uploaded this week or this month, under 4 minutes.
# The sp value is YouTube's own filter encoding: CAM = sort by views, 08 03 = this week, 08 04 = this month, 18 01 = short.
SP = {"week": "CAMSBAgDGAE%3D", "month": "CAMSBAgEGAE%3D"}
YT_URL = "https://www.youtube.com/results?search_query={q}&sp={sp}"


def youtube(query: str, window: str = "week", n: int = 30) -> list[dict]:
    if not shutil.which("yt-dlp"):
        sys.exit("yt-dlp missing: brew install yt-dlp")
    url = YT_URL.format(q=urllib.parse.quote(query), sp=SP[window])
    cmd = ["yt-dlp", url, "--flat-playlist", "--playlist-end", str(n), "--print",
           "%(view_count)s|%(duration)s|%(channel)s|%(title)s|%(id)s"]
    out = subprocess.run(cmd, text=True, capture_output=True).stdout
    rows = []
    for line in out.splitlines():
        parts = line.split("|")
        if len(parts) < 5:
            continue
        views, dur, ch, title, vid = parts[0], parts[1], parts[2], "|".join(parts[3:-1]), parts[-1]
        try:
            views_i = int(views)
        except ValueError:
            continue
        dur_i = int(float(dur)) if dur not in ("NA", "") else 0
        rows.append({"platform": "youtube", "views": views_i, "duration": dur_i, "channel": ch, "title": title,
                     "url": f"https://www.youtube.com/watch?v={vid}", "query": query, "window": window})
    return rows


def tiktok(query: str, n: int = 30) -> list[dict]:
    """Optional. Runs an Apify TikTok search actor synchronously. Verify the actor id and its input fields on the
    Apify store before relying on it; the field names below are the common ones for clockworks/tiktok-scraper."""
    tok = os.environ.get("APIFY_TOKEN")
    if not tok:
        return []
    actor = os.environ.get("APIFY_TIKTOK_ACTOR", "clockworks~tiktok-scraper")
    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?token={tok}&timeout=120"
    body = json.dumps({"searchQueries": [query], "resultsPerPage": n, "shouldDownloadVideos": False}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as f:
            items = json.loads(f.read().decode())
    except Exception as e:
        print(f"  tiktok research skipped: {str(e)[:160]}")
        return []
    rows = []
    for it in items:
        views = it.get("playCount") or it.get("stats", {}).get("playCount") or 0
        rows.append({"platform": "tiktok", "views": int(views), "duration": int(it.get("videoMeta", {}).get("duration") or 0),
                     "channel": (it.get("authorMeta") or {}).get("name") or "", "title": (it.get("text") or "")[:120],
                     "url": it.get("webVideoUrl") or "", "query": query})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("niche")
    ap.add_argument("--also", action="append", default=[], help="extra search phrase, repeatable")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--any-length", action="store_true", help="keep videos over 3 minutes too")
    ap.add_argument("--window", default="week", choices=["week", "month"], help="widens to month on its own when the week is thin")
    ap.add_argument("--page", default=None)
    a = ap.parse_args()
    load_env()
    queries = [a.niche] + a.also
    rows: list[dict] = []
    window = a.window
    for q in queries:
        rows += youtube(q, window)
        rows += youtube(q + " shorts", window)
        rows += tiktok(q)
    if window == "week" and len({r["url"] for r in rows}) < 10:
        print("  thin week, widening to the month")
        window = "month"
        for q in queries:
            rows += youtube(q, window)
            rows += youtube(q + " shorts", window)
    seen, uniq = set(), []
    for r in rows:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        if not a.any_length and r["duration"] > 180:
            continue
        uniq.append(r)
    uniq.sort(key=lambda r: -r["views"])
    top = uniq[: a.limit]
    out_dir = pathlib.Path(a.page).expanduser() if a.page else pathlib.Path(os.getcwd())
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    lines = [f"# Research: {a.niche}", "", f"Pulled {today}. YouTube this {window} sorted by views" +
             (", TikTok via Apify" if os.environ.get("APIFY_TOKEN") else "") +
             f". Queries: {', '.join(queries)} (each also with 'shorts')." +
             (" Under 3 minutes only." if not a.any_length else ""), "",
             "| # | Views | Length | Platform | Channel | Title | Link |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for i, r in enumerate(top, 1):
        lines.append(f"| {i} | {r['views']:,} | {r['duration']}s | {r['platform']} | {r['channel'][:28]} | {r['title'][:70].replace('|', '/')} | {r['url']} |")
    lines += ["", "## Five clip ideas", "", "(Claude writes these in chat, each naming the row it is modelled on, then they go here.)", ""]
    (out_dir / "research.md").write_text("\n".join(lines))
    print()
    for i, r in enumerate(top[:10], 1):
        print(f"  {i:>2}. {r['views']:>10,}  {r['duration']:>3}s  {r['channel'][:20]:<20}  {r['title'][:48]}")
        print(f"      {r['url']}")          # the link is the point: watch it before you pick it
    extra = len(top) - 10
    print(f"\n  {len(top)} rows in research.md" + (f" ({extra} more below these)" if extra > 0 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
