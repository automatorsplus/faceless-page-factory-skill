#!/usr/bin/env bash
# First-run setup for faceless-page-factory. Interview style: one thing at a time, each proved before the next.
# Checks the tools, finds (or creates) .env walking up from this folder, proves each key with a call that costs
# nothing, lists your Blotato accounts so you can copy the ids into /factory page. Prints PASS or what to fix.
# Never prints a key. Safe to run as many times as you like.
#
#   bash scripts/setup.sh                      run the interview
#   bash scripts/setup.sh --set HF_KEY=...     write one key into .env without typing it in chat, then re-check
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ok(){ printf '  PASS  %s\n' "$1"; }
fix(){ printf '  FIX   %s\n' "$1"; FAILED=1; }
FAILED=0

# ---------- 0. --set KEY=VALUE writes into .env (created next to the working directory if none) ----------
find_env(){ local d="$PWD"; for _ in 1 2 3 4 5 6 7 8; do [ -f "$d/.env" ] && { echo "$d/.env"; return; }; [ "$d" = "/" ] && break; d="$(dirname "$d")"; done
            d="$HERE"; for _ in 1 2 3 4 5 6 7 8; do [ -f "$d/.env" ] && { echo "$d/.env"; return; }; [ "$d" = "/" ] && break; d="$(dirname "$d")"; done; echo ""; }
if [ "${1:-}" = "--set" ]; then
  KV="${2:-}"; KEY="${KV%%=*}"; VAL="${KV#*=}"
  [ -z "$KEY" ] || [ -z "$VAL" ] && { echo "usage: setup.sh --set KEY=VALUE"; exit 2; }
  ENVFILE="$(find_env)"; [ -z "$ENVFILE" ] && { ENVFILE="$PWD/.env"; touch "$ENVFILE"; }
  grep -q "^$KEY=" "$ENVFILE" && sed -i '' "/^$KEY=/d" "$ENVFILE"
  printf '%s=%s\n' "$KEY" "$VAL" >> "$ENVFILE"; echo "  wrote $KEY into $ENVFILE"; shift 2
fi

echo "faceless-page-factory setup"
echo
echo "1. Tools"
TOOLS_OK=1
for t in ffmpeg ffprobe python3; do command -v "$t" >/dev/null 2>&1 || { TOOLS_OK=0; fix "$t missing (brew install ffmpeg)"; }; done
command -v yt-dlp >/dev/null 2>&1 || { TOOLS_OK=0; fix "yt-dlp missing (brew install yt-dlp)"; }
python3 -c "import higgsfield_client" 2>/dev/null || { TOOLS_OK=0; fix "higgsfield-client missing (pip3 install higgsfield-client)"; }
[ "$TOOLS_OK" = "1" ] && ok "all five installed"
echo
echo "2. Keys file"
ENVFILE="$(find_env)"
if [ -z "$ENVFILE" ]; then
  ENVFILE="$PWD/.env"; cp "$HERE/../.env.template" "$ENVFILE" 2>/dev/null || printf 'HF_KEY=your_key_here\nBLOTATO_API_KEY=your_key_here\nAPIFY_TOKEN=\n' > "$ENVFILE"
  fix "no .env found. Made one for you at ./.env, put your keys in it and run this again."
else
  ok ".env found"
fi
getkey(){ grep "^$1=" "$ENVFILE" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"' \r'; }

echo
echo "3. Higgsfield key        sign up: higgsfield.ai   key: console.higgsfield.ai"
HF="$(getkey HF_KEY)"
if [ -z "$HF" ] || [ "$HF" = "your_key_here" ]; then
  fix "not set. Make one, then run: setup.sh --set HF_KEY=<id:secret>"
else
  CODE=$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Key $HF" https://api.higgsfield.ai/v1/text2image/soul-styles)
  [ "$CODE" = "200" ] && ok "accepted, nothing billed" || fix "rejected (HTTP $CODE). Check the id:secret pair in the console."
fi

echo
echo "4. Blotato key           sign up: blotato.com/?ref=marcus   key: my.blotato.com/settings/api"
BK="$(getkey BLOTATO_API_KEY)"
if [ -z "$BK" ] || [ "$BK" = "your_key_here" ]; then
  fix "not set. Copy it, then run: setup.sh --set BLOTATO_API_KEY=<key>"
else
  RESP=$(curl -s -X POST https://mcp.blotato.com/mcp -H "blotato-api-key: $BK" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"blotato_list_accounts","arguments":{}}}')
  # An invalid key still comes back HTTP 200 with result.isError set, so grepping for
  # "result" reported PASS on a bad key and then printed a raw JSON blob. Decide in python.
  ACCOUNTS=$(echo "$RESP" | python3 -c '
import sys, json
raw = sys.stdin.read()
try:
    d = json.loads(raw)
except Exception:
    print("Blotato sent something that is not JSON: " + raw[:160]); sys.exit(1)
res = d.get("result") or {}
if res.get("isError") or d.get("error"):
    try:
        msg = res["content"][0]["text"]
    except Exception:
        msg = json.dumps(d.get("error") or res)[:200]
    print(msg[:200]); sys.exit(1)
try:
    acc = json.loads(res["content"][0]["text"])
except Exception as e:
    print("could not read the accounts list: " + str(e)[:120]); sys.exit(1)
items = acc if isinstance(acc, list) else acc.get("items") or acc.get("accounts") or acc.get("data") or []
if not items:
    print("        (no accounts connected yet: connect TikTok and YouTube in Blotato first)"); sys.exit(0)
for a in items:
    print("        %-10s %-28s id %s" % (str(a.get("platform","?")), str(a.get("fullname") or a.get("username") or a.get("name") or "")[:28], a.get("id")))
')
  if [ $? -eq 0 ]; then
    ok "accepted. Your connected accounts:"
    echo "$ACCOUNTS"
  else
    fix "rejected. Blotato says: $ACCOUNTS"
  fi
fi

echo
echo "5. Apify token           optional: console.apify.com/account/integrations"
AP="$(getkey APIFY_TOKEN)"
if [ -z "$AP" ]; then
  echo "  SKIP  not set. Research runs on YouTube only, which is fine."
else
  CODE=$(curl -s -o /dev/null -w '%{http_code}' "https://api.apify.com/v2/users/me?token=$AP")
  [ "$CODE" = "200" ] && ok "accepted" || fix "rejected (HTTP $CODE)"
fi

echo
if [ "$FAILED" = "0" ]; then
  echo "PASS. Next: /factory research \"<your niche>\", then /factory page."
  exit 0
else
  echo "Not ready yet. Fix the FIX lines above and run: bash scripts/setup.sh"
  exit 1
fi
