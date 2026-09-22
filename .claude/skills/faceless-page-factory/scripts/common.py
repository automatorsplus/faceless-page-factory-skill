#!/usr/bin/env python3
"""Shared helpers for the faceless-page-factory scripts: the .env lookup that walks up from the working
directory, the page folder, page.md parsing, queue.json, small shell helpers. No key is ever printed."""
from __future__ import annotations
import datetime, json, os, pathlib, re, subprocess, sys

KEYS = ("HF_KEY", "BLOTATO_API_KEY", "APIFY_TOKEN", "FAL_KEY")
PLACEHOLDERS = {"", "your_key_here", "YOUR_KEY", "xxx"}


def find_env(start: str | None = None) -> pathlib.Path | None:
    """.env in the working directory or any parent, then the same walk from the script's own folder."""
    for s in (pathlib.Path(start or os.getcwd()).resolve(), pathlib.Path(__file__).resolve().parent):
        p = s
        for _ in range(10):
            f = p / ".env"
            if f.is_file():
                return f
            if p.parent == p:
                break
            p = p.parent
    return None


def load_env() -> pathlib.Path | None:
    f = find_env()
    if f:
        for line in f.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k in KEYS and not os.environ.get(k) and v not in PLACEHOLDERS:
                os.environ[k] = v
    return f


def need(key: str) -> str:
    v = os.environ.get(key)
    if not v or v in PLACEHOLDERS:
        sys.exit(f"{key} is missing. Put it in .env (walk-up from this folder) and run setup.sh. See SETUP.md.")
    return v


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:48] or "clip"


def now_stamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")


def sh(cmd: list[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, text=True, capture_output=capture)


# ---- page folder -------------------------------------------------------------------------------

def find_page(explicit: str | None = None) -> pathlib.Path:
    if explicit:
        p = pathlib.Path(explicit).expanduser().resolve()
        if (p / "page.md").is_file():
            return p
        sys.exit(f"no page.md in {p}")
    cwd = pathlib.Path(os.getcwd()).resolve()
    if (cwd / "page.md").is_file():
        return cwd
    found = [d for d in cwd.iterdir() if d.is_dir() and (d / "page.md").is_file()]
    if len(found) == 1:
        return found[0]
    if not found:
        sys.exit("no page here. Run /factory page first, or pass --page <folder>.")
    sys.exit("several pages here, pass --page: " + ", ".join(d.name for d in found))


def parse_page(path: pathlib.Path) -> dict:
    """page.md is plain `key: value` lines; a key with no value opens a block of indented `sub: value` lines.
    Comma-separated values become lists when the key is a times or tags key."""
    data: dict = {}
    block: str | None = None
    for raw in (path / "page.md").read_text().splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indented = raw.startswith((" ", "\t"))
        line = raw.strip()
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if indented and block:
            data.setdefault(block, {})[k] = v
        elif v == "":
            block = k
            data.setdefault(k, {})
        else:
            block = None
            data[k] = v
    return data


def times_for(page: dict, platform: str) -> list[tuple[int, int, int]]:
    """'Mon 18:00, Wed 18:00' -> [(weekday, hour, minute)], Monday = 0."""
    days = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    out = []
    for item in (page.get("times") or {}).get(platform, "").split(","):
        item = item.strip()
        if not item:
            continue
        d, hm = item.split()
        h, m = hm.split(":")
        out.append((days[d[:3].lower()], int(h), int(m)))
    return sorted(out)


def load_queue(page: pathlib.Path) -> list[dict]:
    f = page / "queue.json"
    return json.loads(f.read_text()) if f.is_file() else []


def save_queue(page: pathlib.Path, q: list[dict]) -> None:
    (page / "queue.json").write_text(json.dumps(q, indent=2))
