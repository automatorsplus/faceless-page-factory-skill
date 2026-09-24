#!/usr/bin/env python3
"""One clip through the Higgsfield API: Seedance 2.5 text-to-video, 9:16, then loudness to -13.8 LUFS, a poster
frame, meta.json, and a row in queue.json. Billed to HF_KEY per successful clip; failed and NSFW requests are not
charged (their FAQ). Quote the price before you run it: the console shows it per model.

    python3 clip.py --page ./octofacts --prompt "..." --slug octopus-hearts
    python3 clip.py --page ./octofacts --prompt "..." --duration 30            4 to 30 seconds in one call
    python3 clip.py --page ./octofacts --prompts-file shots.txt --slug x       one clip per line, stitched with ffmpeg
    python3 clip.py ... --dry-run                                               print the request, call nothing
"""
from __future__ import annotations
import argparse, datetime, json, os, pathlib, subprocess, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import find_page, load_env, load_queue, need, now_stamp, save_queue, slugify
import loudness

MODEL = "bytedance/seedance-2.5/text-to-video"


def generate(prompt: str, duration: int, resolution: str, aspect: str, audio: bool, out: pathlib.Path) -> dict:
    import higgsfield_client as hf
    args = {"prompt": prompt, "duration": duration, "resolution": resolution, "aspect_ratio": aspect,
            "output_format": "mp4", "generate_audio": audio}
    state = {"rid": None}
    t0 = time.time()
    print(f"  generating {duration}s {aspect}...")
    try:
        res = hf.subscribe(MODEL, arguments=args, on_enqueue=lambda rid: state.__setitem__("rid", rid))
    except hf.CredentialsMissedError as e:
        sys.exit(f"credentials: {e}")
    except hf.InsufficientCreditsError as e:
        sys.exit(f"the API account has no credits: {e}")
    except hf.HiggsfieldClientError as e:
        sys.exit(f"API error, no clip, nothing charged: {e}")
    url = (res.get("video") or {}).get("url") if isinstance(res, dict) else None
    if not url:
        sys.exit(f"completed without a video url: {json.dumps(res)[:300]}")
    urllib.request.urlretrieve(url, out)
    return {"request_id": state["rid"] or res.get("request_id"), "args": args, "url": url,
            "elapsed_s": round(time.time() - t0, 1), "bytes": out.stat().st_size}


def has_audio(path: pathlib.Path) -> bool:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                          "stream=index", "-of", "csv=p=0", str(path)], text=True, capture_output=True).stdout
    return bool(out.strip())


def add_silence(inp: pathlib.Path, out: pathlib.Path) -> None:
    """A clip with no audio track cannot be measured and both platforms prefer one, so give it silence
    rather than losing a generation that has already been paid for."""
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(inp),
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", str(out)], check=True)


def stitch(parts: list[pathlib.Path], out: pathlib.Path) -> None:
    lst = out.parent / "concat.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-r", "30", str(out)], check=True)
    lst.unlink()


def build(page: pathlib.Path, slug: str, prompts: list, a) -> None:
    """One finished clip: generate (one call, or several stitched), loudness, poster, meta, queue row."""
    d = page / "clips" / slug
    d.mkdir(parents=True, exist_ok=True)
    parts, records = [], []
    for i, p in enumerate(prompts, 1):
        out = d / (f"shot-{i:02d}.mp4" if len(prompts) > 1 else "raw.mp4")
        records.append(generate(p, a.duration, a.resolution, a.aspect, not a.no_audio, out))
        parts.append(out)
        print(f"  done in {records[-1]['elapsed_s']}s")
    raw = d / "raw.mp4"
    if len(parts) > 1:
        stitch(parts, raw)
    silent = False
    if not has_audio(raw):
        silent = True
        print("  no audio track came back. Adding silence so the clip still ships.")
        mute = d / "raw-silent.mp4"
        add_silence(raw, mute)
        raw = mute
    mm = loudness.fix(str(raw), str(d / "clip.mp4"))
    print("  loudness:", loudness.report(mm))
    # The generation is already paid for, so an off-spec clip is still written and queued, never dropped.
    # It waits as needs-audio and schedule.py books it only when it is named with --clip.
    off_spec = not loudness.in_spec(mm) and not silent
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", "1", "-i", str(d / "clip.mp4"),
                    "-frames:v", "1", "-q:v", "2", str(d / "poster.jpg")], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(d / "clip.mp4")], text=True, capture_output=True).stdout.strip() or 0)
    meta = {"slug": slug, "model": MODEL, "prompts": prompts, "duration_s": round(dur, 2), "aspect": a.aspect,
            "resolution": a.resolution, "generations": records, "price_usd_each": a.price_usd,
            "loudness": mm, "silent": silent, "made": datetime.datetime.now().isoformat(timespec="seconds")}
    meta["loudness_ok"] = not off_spec
    (d / "meta.json").write_text(json.dumps(meta, indent=2))
    if not (d / "caption.txt").is_file():
        (d / "caption.txt").write_text("")
    q = load_queue(page)
    state = "needs-audio" if off_spec else "rendered"
    q.append({"slug": slug, "state": state, "duration_s": round(dur, 2), "made": meta["made"], "blotato": {}})
    save_queue(page, q)
    if off_spec:
        print(f"  clips/{slug}/clip.mp4  ({dur:.1f}s)  queued as needs-audio: loudness is off spec.\n"
              f"  Listen to it. To post it anyway, name it: schedule.py --clip {slug}")
    else:
        print(f"  clips/{slug}/clip.mp4  ({dur:.1f}s)  queued")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default=None)
    ap.add_argument("--prompt", default=None)
    ap.add_argument("--prompts-file", default=None, help="one prompt per line")
    ap.add_argument("--batch", action="store_true",
                    help="with --prompts-file: one SEPARATE clip per line. Without it the lines are stitched into one clip")
    ap.add_argument("--slug", default=None)
    ap.add_argument("--duration", type=int, default=10, help="4 to 30 seconds per clip")
    ap.add_argument("--resolution", default="720p", choices=["480p", "720p"])
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--price-usd", type=float, default=None, help="what the console says one clip costs, printed first")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    load_env()
    page = find_page(a.page)
    prompts = [l.strip() for l in open(a.prompts_file).read().splitlines() if l.strip()] if a.prompts_file else [a.prompt or ""]
    if not prompts or not prompts[0]:
        sys.exit("give --prompt or --prompts-file")
    if not 4 <= a.duration <= 30:
        sys.exit("duration is 4 to 30 seconds per clip on Seedance 2.5")
    if a.batch and not a.prompts_file:
        sys.exit("--batch needs --prompts-file, one prompt per line")

    if a.batch:
        base = slugify(a.slug) if a.slug else None
        jobs = [((f"{base}-{i:02d}" if base else slugify(p)), [p]) for i, p in enumerate(prompts, 1)]
    else:
        jobs = [(slugify(a.slug or prompts[0]), prompts)]

    for slug, _ in jobs:
        if (page / "clips" / slug / "clip.mp4").is_file():
            sys.exit(f"{page / 'clips' / slug} already has a clip. Pick another --slug.")

    gens = sum(len(pr) for _, pr in jobs)
    cost = f"about ${a.price_usd * gens:.2f}" if a.price_usd else f"the console price for Seedance 2.5, times {gens}"
    if a.batch:
        print(f"Batch: {len(jobs)} clips x {a.duration}s, {a.aspect}. Cost: {cost}.")
    else:
        print(f"Clip {jobs[0][0]}: {a.duration}s, {a.aspect}. Cost: {cost}.")
    for slug, pr in jobs:
        print(f"  [{slug}] {pr[0][:88]}")
    if a.dry_run:
        print("  dry run, nothing sent")
        return 0

    need("HF_KEY")
    for n, (slug, pr) in enumerate(jobs, 1):
        if len(jobs) > 1:
            print(f"\n({n}/{len(jobs)}) {slug}")
        build(page, slug, pr, a)

    if len(jobs) == 1:
        print("\n  Next: the caption, then /factory schedule.")
        subprocess.run(["open", str(page / "clips" / jobs[0][0] / "clip.mp4")], check=False)
    else:
        print(f"\n  {len(jobs)} clips queued. Next: captions, then /factory schedule.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
