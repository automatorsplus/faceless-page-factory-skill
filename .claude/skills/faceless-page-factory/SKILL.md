---
name: faceless-page-factory
description: A faceless page in a box. Research what is going viral in a niche, create the page (name, bio, logo, banner), generate 9:16 clips through the Higgsfield API, schedule them to TikTok and YouTube through Blotato. Trigger on "/factory", "faceless page", "start a faceless channel", "schedule these clips", "research a niche for shorts".
---

# Faceless Page Factory

By Marcus Mewett, for the Automators community. Four things packaged as one: research the niche, create the page,
generate the clips, schedule the week. Every step is one command. Claude does the writing in chat where you can
see it (ideas, names, bios, captions); the scripts do the calls.

```
bash scripts/setup.sh                       first run, interview style, proves each key with a free call
/factory research "<niche>"                 top twenty by views, under 3 min, then five clip ideas in chat
/factory page                               three names and bios to pick from, handle check, logo, banner, page.md
/factory clip "<prompt>"                    one Seedance 2.5 clip, 9:16, loudness fixed, poster, queued
/factory batch shots.txt                    one clip per line, a month in one command
/factory schedule                           rendered clips into the next slots on both platforms, dates shown first
```

## First time: run the setup, one thing at a time

`bash scripts/setup.sh`. It checks ffmpeg, ffprobe, python3, yt-dlp and the `higgsfield-client` package, finds
`.env` by walking up from the folder you are in (or creates one from `.env.template`), then proves each key:

- `HF_KEY` (Higgsfield API, `id:secret`, from console.higgsfield.ai) with a free styles call.
- `BLOTATO_API_KEY` by listing your connected accounts, which is also where you copy the ids from.
- `APIFY_TOKEN` is optional; it adds TikTok to research. Without it research is YouTube only, which is fine.

Ask the member for each key in turn and have them paste it into `.env` themselves, or run
`bash scripts/setup.sh --set HF_KEY=...` for them. Never read a key back into chat. PASS means go.

## Research

```
python3 scripts/research.py "satisfying physics" --also "oddly satisfying" [--page <folder>]
```
YouTube results sorted by views, deduped, **anything under 3 minutes** (`--any-length` keeps the rest), top
twenty with links into `research.md`. **A thin week widens to the month on its own and says so**, and the file
records which window it used. The top ten print with their URLs so the member can open a few and hear them
before choosing.

🔴 **Every row you put in chat carries its link.** The member picks a row to replicate, so they have to be able
to watch it first, not take your word for what is in it. A table of views and titles with no links is the one
thing that makes this step useless.

Then write five clip ideas in chat, each naming the row it is modelled on and carrying that row's link, and
paste them into the file's last section.
This is the step most people skip. Do it before the page exists so the niche is chosen on numbers.

## Page

Propose three names and bios in chat. For the pick:
```
python3 scripts/page.py --name "..." --handle name --niche "..." --bio "..." \
  --tiktok-id <id> --youtube-id <id> --times-tiktok "Mon 18:00, Wed 18:00, Fri 18:00, Sat 12:00" \
  --times-youtube "Mon 17:00, Wed 17:00, Fri 17:00, Sat 11:00" --logo "<one line>" --banner "<one line>"
```
Checks both handles, writes `<handle>/page.md` with the setup checklist, makes the logo (1:1) and banner (16:9)
through the Higgsfield API (SOUL text to image, billed), and an empty `queue.json`. `--skip-art` to do the
art later, `--check-only` to test a handle.

## Clip

```
python3 scripts/clip.py --page <folder> --prompt "..." --slug <name> [--duration 10] [--price-usd 0.00]
```
Seedance 2.5 text to video through the API, 4 to 30 seconds in one call, 9:16, 720p, audio on. Then two-pass
loudness to -13.8 LUFS, a poster frame, `meta.json`, a row in `queue.json`. A clip still off spec after the fix is
kept and queued as `needs-audio`, never dropped, because the generation is already paid for. Listen to it; sparse
ASMR is the usual cause.
**A file of prompts does one of two things, and the flag decides which:**

```
python3 scripts/clip.py --page <folder> --prompts-file shots.txt --slug slide --batch
```
`--batch` makes **one separate clip per line**, slugged `slide-01`, `slide-02` and so on, each with its own
loudness pass, poster and queue row. This is how you make a week or a month in one command. It runs them one
after another in the foreground and prints the total cost before it starts.

Without `--batch` the same file is **stitched into one longer clip**, which is how you get past the 30 second
per generation ceiling. `--dry-run` prints the request and sends nothing.

**Quote before you spend.** The console shows the price per model; pass it as `--price-usd` and the script prints
the total before the call, for a batch as well as a single clip. Failed and NSFW requests are not charged
(Higgsfield FAQ). Generations always run one at a time in the foreground, never in parallel.

Then write `clips/<slug>/caption.txt`: line one is the TikTok caption with three to five tags, line two the
YouTube title (under 100 characters). No double quotes, no em dashes.

## Schedule

```
python3 scripts/schedule.py --page <folder>          the plan
python3 scripts/schedule.py --page <folder> --yes    book it
```
Every rendered clip goes into the next free slot per platform from `page.md`, local time converted on write. The
plan prints first; nothing is uploaded or booked without `--yes`. Upload is Blotato's presigned upload, the post is
`POST /v2/posts`, one per platform, `isAiGenerated` and `containsSyntheticMedia` set true because the clips are.
A clip already scheduled is refused. A `needs-audio` clip is only booked when it is named with `--clip <slug>`.

```
python3 scripts/schedule.py --page <folder> --clip <slug> --privacy unlisted --in 10 --yes
```
`--privacy public | unlisted | private` (default public). TikTok has no unlisted, so anything but public goes to
TikTok as SELF_ONLY and a test stays quiet on both platforms. `--in <minutes>` posts that far from now instead of
into the next slots, which is how you do a first test post.

## Page folder

```
<handle>/
  page.md          name, handle, bio, niche, timezone, the two Blotato account ids, posting times, checklist
  research.md      the last research pull, dated
  assets/          logo.png, banner.png
  clips/<slug>/    clip.mp4, poster.jpg, caption.txt, meta.json (raw.mp4 and shots kept)
  queue.json       every clip: state (rendered | needs-audio | scheduled), Blotato ids and times
```

## Platform rules

- -13.8 LUFS, -1.0 dBTP on every clip, and watch it before it is scheduled. `python3 scripts/loudness.py <file>`.
- A clip is scheduled once. Reposting the same clip is how a page gets buried.
- Everything through Blotato, so the numbers come back to one place.
- YouTube Shorts under 60 seconds. TikTok Creator Rewards needs clips over 60 seconds, 10,000 followers and
  100,000 views in 30 days. `--duration 30` plus a two-shot file gets you there.

## Not in it

Voice, captions burnt in, music beds, dashboards, metrics. This gets a page live and a week booked.

## References

`references/higgsfield-api.md` (endpoints, schemas, the free call), `references/blotato-api.md` (upload, post
bodies, the cursor rule, the 422 lesson), `references/platform-rules.md`.
