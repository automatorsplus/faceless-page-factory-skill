#!/usr/bin/env python3
"""Book rendered clips into the page's posting times on TikTok and YouTube through Blotato. Prints every date
first and does nothing until --yes. Upload goes through Blotato's presigned upload, the post through
POST /v2/posts, the bodies the same shape a live faceless page has been booked with for a month.

    python3 schedule.py --page ./octofacts                 plan: which clip lands in which slot
    python3 schedule.py --page ./octofacts --yes           book them
    python3 schedule.py --page ./octofacts --clip a --clip b --yes
    python3 schedule.py --page ./octofacts --from 2026-09-25      first slot on or after this date
    python3 schedule.py --page ./octofacts --clip a --privacy unlisted --in 10 --yes    a test post, ten minutes out

--privacy public (default), unlisted or private. TikTok has no unlisted, so anything but public goes to TikTok as
SELF_ONLY: a quiet test stays quiet on both platforms. A clip queued as needs-audio (loudness off spec) is only
booked when it is named with --clip.
"""
from __future__ import annotations
import argparse, datetime, json, os, pathlib, sys, urllib.error, urllib.request, zoneinfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import find_page, load_env, load_queue, need, parse_page, save_queue, times_for

API = "https://backend.blotato.com"
MCP = "https://mcp.blotato.com/mcp"
TT_TARGET = {"targetType": "tiktok", "privacyLevel": "PUBLIC_TO_EVERYONE", "disabledComments": False,
             "disabledDuet": False, "disabledStitch": False, "isBrandedContent": False, "isYourBrand": False,
             "isAiGenerated": True}      # Seedance clips are AI generated; say so to the platform


def bl(method: str, path: str, body: dict | None = None) -> dict:
    key = need("BLOTATO_API_KEY")
    req = urllib.request.Request(API + path, method=method, headers={"blotato-api-key": key})
    data = None
    if body is not None:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, data, timeout=60) as f:
            t = f.read().decode()
            return json.loads(t) if t.strip() else {}
    except urllib.error.HTTPError as e:
        # Blotato puts the reason in the body. A bare status number is useless, so read it.
        detail = ""
        try:
            detail = e.read().decode()[:600]
        except Exception:
            pass
        sys.exit(f"Blotato {method} {path} -> HTTP {e.code}\n  {detail}")


def upload(path: pathlib.Path, name: str) -> str:
    key = need("BLOTATO_API_KEY")
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "blotato_create_presigned_upload_url", "arguments": {"filename": name}}}
    req = urllib.request.Request(MCP, method="POST", data=json.dumps(body).encode(),
                                 headers={"blotato-api-key": key, "Content-Type": "application/json",
                                          "Accept": "application/json, text/event-stream"})
    with urllib.request.urlopen(req, timeout=120) as f:
        up = json.loads(json.loads(f.read())["result"]["content"][0]["text"])
    with open(path, "rb") as fh:
        urllib.request.urlopen(urllib.request.Request(up["presignedUrl"], method="PUT", data=fh.read(),
                                                      headers={"Content-Type": "video/mp4"}), timeout=1800).read()
    return up["publicUrl"]


def next_slots(times: list[tuple[int, int, int]], after: datetime.datetime, n: int, tz: zoneinfo.ZoneInfo) -> list[datetime.datetime]:
    """The next n local datetimes matching the page's (weekday, hour, minute) rhythm, strictly after `after`."""
    out, day = [], after.date()
    for _ in range(120):
        for wd, h, m in times:
            if day.weekday() == wd:
                t = datetime.datetime(day.year, day.month, day.day, h, m, tzinfo=tz)
                if t > after:
                    out.append(t)
        if len(out) >= n:
            return out[:n]
        day += datetime.timedelta(days=1)
    sys.exit("could not find enough slots; check the times in page.md")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default=None)
    ap.add_argument("--clip", action="append", default=[], help="slug, repeatable; default every rendered clip")
    ap.add_argument("--from", dest="from_date", default=None, help="YYYY-MM-DD, first slot on or after")
    ap.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"],
                    help="YouTube privacy. Anything but public posts to TikTok as SELF_ONLY")
    ap.add_argument("--in", dest="in_minutes", type=int, default=None,
                    help="post N minutes from now instead of the next slots; several clips go a minute apart")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    if a.in_minutes is not None and a.in_minutes < 2:
        sys.exit("--in needs at least 2 minutes, so Blotato has time to take the upload")
    load_env()
    page = find_page(a.page)
    pg = parse_page(page)
    tz = zoneinfo.ZoneInfo(pg.get("timezone", "Europe/London"))
    acc = pg.get("accounts") or {}
    q = load_queue(page)
    # rendered clips go by default; a needs-audio clip only when it is named, which is the choice to post it anyway
    todo = [r for r in q if (r["state"] == "rendered" and (not a.clip or r["slug"] in a.clip))
            or (r["state"] == "needs-audio" and r["slug"] in a.clip)]
    if not todo:
        held = [r["slug"] for r in q if r["state"] == "needs-audio"]
        hint = f" Waiting as needs-audio (name one with --clip to post it): {', '.join(held)}." if held else ""
        sys.exit("nothing rendered to schedule. Run /factory clip first, or the slugs given are already scheduled." + hint)
    for r in todo:
        if r["state"] == "needs-audio":
            print(f"  {r['slug']}: loudness is off spec, booking it because it was named")
    tt_target = dict(TT_TARGET, privacyLevel="PUBLIC_TO_EVERYONE" if a.privacy == "public" else "SELF_ONLY")
    plan = []
    for platform in ("tiktok", "youtube"):
        if not acc.get(platform):
            print(f"  {platform}: no account id in page.md, skipped")
            continue
        if a.in_minutes is not None:
            start = datetime.datetime.now(tz).replace(second=0, microsecond=0) + datetime.timedelta(minutes=a.in_minutes)
            for i, r in enumerate(todo):
                plan.append((platform, r, start + datetime.timedelta(minutes=i)))
            continue
        times = times_for(pg, platform)
        if not times:
            print(f"  {platform}: no times in page.md, skipped")
            continue
        last = max([datetime.datetime.fromisoformat(r["blotato"][platform]["at"]) for r in q
                    if r.get("blotato", {}).get(platform)] + [datetime.datetime.now(tz) + datetime.timedelta(hours=1)])
        if a.from_date:
            y, mo, d = map(int, a.from_date.split("-"))
            last = max(last, datetime.datetime(y, mo, d, 0, 0, tzinfo=tz) - datetime.timedelta(minutes=1))
        for r, t in zip(todo, next_slots(times, last, len(todo), tz)):
            plan.append((platform, r, t))
    print(f"Plan for {pg.get('name', page.name)}, {a.privacy}:")
    for platform, r, t in plan:
        print(f"  {t.strftime('%a %d %b %H:%M')}  {platform:<8} {r['slug']}")
    if not a.yes:
        print("\n  dry run. Add --yes to book.")
        return 0
    urls: dict[str, str] = {}
    for platform, r, t in plan:
        d = page / "clips" / r["slug"]
        cap_lines = (d / "caption.txt").read_text().splitlines() if (d / "caption.txt").is_file() else []
        cap = cap_lines[0].strip() if cap_lines else r["slug"].replace("-", " ")
        title = cap_lines[1].strip() if len(cap_lines) > 1 else cap[:100]
        if r["slug"] not in urls:
            print(f"  uploading {r['slug']}...")
            urls[r["slug"]] = upload(d / "clip.mp4", f"{r['slug']}-{t.strftime('%Y%m%d%H%M')}.mp4")
        iso = t.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z")
        if platform == "tiktok":
            body = {"post": {"accountId": acc["tiktok"], "target": tt_target,
                             "content": {"text": cap, "mediaUrls": [urls[r["slug"]]], "platform": "tiktok"}}, "scheduledTime": iso}
        else:
            body = {"post": {"accountId": acc["youtube"],
                             "target": {"targetType": "youtube", "title": title[:100], "privacyStatus": a.privacy,
                                        "isMadeForKids": False, "containsSyntheticMedia": True, "shouldNotifySubscribers": False},
                             "content": {"text": "", "mediaUrls": [urls[r["slug"]]], "platform": "youtube"}}, "scheduledTime": iso}
        res = bl("POST", "/v2/posts", body)
        pid = str(res.get("postSubmissionId") or res.get("id") or "")
        r.setdefault("blotato", {})[platform] = {"id": pid, "at": t.isoformat(), "url": urls[r["slug"]]}
        print(f"  booked  {t.strftime('%a %d %b %H:%M')}  {platform:<8} {r['slug']}")
    for r in todo:
        if r.get("blotato"):
            r["state"] = "scheduled"
    save_queue(page, q)
    print(f"\n  {len(plan)} posts booked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
