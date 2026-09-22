#!/usr/bin/env python3
"""Create the page folder: page.md, a logo and a banner through the Higgsfield API (SOUL), the handle check.
Claude proposes the names and bios in chat; this script takes the picked one.

    python3 page.py --name "Octo Facts" --handle octofacts --niche "animal facts" --bio "One fact a day." \
        --tiktok-id 123 --youtube-id 456 \
        --times-tiktok "Mon 18:00, Wed 18:00, Fri 18:00, Sat 12:00" --times-youtube "Mon 17:00, Wed 17:00, Fri 17:00, Sat 11:00" \
        --logo "a minimal octopus mark, flat, one colour on black" --banner "deep sea, soft light, no text" \
        [--out ./octofacts] [--skip-art] [--check-only]
"""
from __future__ import annotations
import argparse, json, os, pathlib, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_env, need, slugify

SOUL = "higgsfield-ai/soul/standard"     # text to image on the Higgsfield API, verified in their docs 2026-09-22
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/128 Safari/537.36"}


def handle_free(url: str, taken_markers: tuple[str, ...], free_markers: tuple[str, ...] = ()) -> str:
    """YouTube answers 404 for a free handle. TikTok always answers 200 and says it in the page: a free handle
    carries statusCode 10221 and no uniqueId for that name; a taken one carries the uniqueId. Checked 2026-09-22."""
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as f:
            body = f.read().decode("utf-8", "ignore")
            if any(m in body for m in taken_markers):
                return "taken"
            if any(m in body for m in free_markers):
                return "free"
            return "unclear, open it"
    except urllib.error.HTTPError as e:
        return "free" if e.code == 404 else f"unclear (HTTP {e.code}), open it"
    except Exception as e:
        return f"unclear ({type(e).__name__}), open it"


def art(prompt: str, aspect: str, out: pathlib.Path) -> str:
    import higgsfield_client as hf
    res = hf.subscribe(SOUL, arguments={"prompt": prompt, "aspect_ratio": aspect, "resolution": "1080p",
                                        "enhance_prompt": True, "batch_size": 1})
    url = (res.get("images") or [{}])[0].get("url") if isinstance(res, dict) else None
    if not url:
        sys.exit(f"no image in the response: {json.dumps(res)[:300]}")
    urllib.request.urlretrieve(url, out)
    return url


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True); ap.add_argument("--handle", required=True)
    ap.add_argument("--niche", required=True); ap.add_argument("--bio", required=True)
    ap.add_argument("--tiktok-id", default=""); ap.add_argument("--youtube-id", default="")
    ap.add_argument("--times-tiktok", default="Mon 18:00, Wed 18:00, Fri 18:00, Sat 12:00")
    ap.add_argument("--times-youtube", default="Mon 17:00, Wed 17:00, Fri 17:00, Sat 11:00")
    ap.add_argument("--timezone", default="Europe/London")
    ap.add_argument("--length", default="short", choices=["short", "long"])
    ap.add_argument("--logo", default=""); ap.add_argument("--banner", default="")
    ap.add_argument("--out", default=None); ap.add_argument("--skip-art", action="store_true")
    ap.add_argument("--check-only", action="store_true", help="only check the handles")
    a = ap.parse_args()
    load_env()
    h = a.handle.lstrip("@")
    print("Handle check")
    yt = handle_free(f"https://www.youtube.com/@{h}", ("subscriber", "channelMetadataRenderer"))
    tt = handle_free(f"https://www.tiktok.com/@{h}", ('"uniqueId":"' + h + '"',), ('"statusCode":10221',))
    print(f"  youtube.com/@{h}: {yt}\n  tiktok.com/@{h}:  {tt}")
    if a.check_only:
        return 0
    out = pathlib.Path(a.out or slugify(h)).resolve()
    (out / "assets").mkdir(parents=True, exist_ok=True)
    (out / "clips").mkdir(exist_ok=True)
    page_md = f"""# {a.name}

name: {a.name}
handle: {h}
niche: {a.niche}
bio: {a.bio}
length: {a.length}
timezone: {a.timezone}
accounts:
  tiktok: {a.tiktok_id}
  youtube: {a.youtube_id}
times:
  tiktok: {a.times_tiktok}
  youtube: {a.times_youtube}

## Setup checklist
- [ ] one fresh email for the page
- [ ] TikTok account @{h}, bio pasted, logo uploaded
- [ ] YouTube channel @{h}, bio pasted, logo and banner uploaded
- [ ] both connected in Blotato, ids above filled in (bash scripts/setup.sh lists them)
"""
    (out / "page.md").write_text(page_md)
    if not (out / "queue.json").is_file():
        (out / "queue.json").write_text("[]")
    print(f"  wrote {out.name}/page.md")
    if a.skip_art:
        print("  art skipped")
        return 0
    need("HF_KEY")
    if a.logo:
        print("  logo (billed)...")
        art(a.logo + ". Square logo mark, centred, plain background, no text.", "1:1", out / "assets" / "logo.png")
        print("  assets/logo.png")
    if a.banner:
        print("  banner (billed)...")
        art(a.banner + ". Wide channel banner, no text, room in the centre for a name.", "16:9", out / "assets" / "banner.png")
        print("  assets/banner.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
