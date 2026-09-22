# Setup, first time

Ten minutes, three accounts, two keys. Run `bash scripts/setup.sh` after each step; it tells you what is next.

1. **Tools.** `brew install ffmpeg yt-dlp` and `pip3 install higgsfield-client`. Python 3.9 or newer.
2. **Higgsfield API.** Sign up at higgsfield.ai, then make a key at console.higgsfield.ai, it comes as `id:secret`. Pay as you go, separate
   from a Higgsfield subscription. Put it in `.env` as `HF_KEY=id:secret`. The setup proves it with a call that
   costs nothing.
3. **Blotato.** Sign up at blotato.com/?ref=marcus, connect the page's TikTok and YouTube accounts, then Settings, API (my.blotato.com/settings/api), copy the key into
   `.env` as `BLOTATO_API_KEY=`. The setup lists your accounts with their ids; those go into `/factory page`.
4. **Apify, optional.** Adds TikTok to research. Token from console.apify.com/account/integrations, into `.env` as `APIFY_TOKEN=`. Skip it to start.

`.env` lives in your project root. The scripts find it by walking up from wherever you run them. Never commit it.

---

## What it looks like

Run it from your project root:

```bash
bash .claude/skills/faceless-page-factory/scripts/setup.sh
```

**First run, before you have any keys.** It writes the `.env` for you:

```
faceless-page-factory setup

1. Tools
  PASS  all five installed

2. Keys file
  FIX   no .env found. Made one for you at ./.env, put your keys in it and run this again.

3. Higgsfield key        sign up: higgsfield.ai   key: console.higgsfield.ai
  FIX   not set. Make one, then run: setup.sh --set HF_KEY=<id:secret>

4. Blotato key           sign up: blotato.com/?ref=marcus   key: my.blotato.com/settings/api
  FIX   not set. Copy it, then run: setup.sh --set BLOTATO_API_KEY=<key>

5. Apify token           optional: console.apify.com/account/integrations
  SKIP  not set. Research runs on YouTube only, which is fine.

Not ready yet. Fix the FIX lines above and run the setup again.
```

**A key pasted in wrong.** It tells you what the platform actually said, so you are not guessing:

```
3. Higgsfield key        sign up: higgsfield.ai   key: console.higgsfield.ai
  FIX   rejected (HTTP 401). Check the id:secret pair in the console.

4. Blotato key           sign up: blotato.com/?ref=marcus   key: my.blotato.com/settings/api
  FIX   rejected. Blotato says: Invalid API key or auth session. Get your key at
        https://my.blotato.com/settings/api, or refresh your auth session.
```

**Both keys good.** Your connected accounts print with their ids, and those ids are what
`/factory page` wants, so keep this output on screen:

```
1. Tools
  PASS  all five installed

2. Keys file
  PASS  .env found

3. Higgsfield key        sign up: higgsfield.ai   key: console.higgsfield.ai
  PASS  accepted, nothing billed

4. Blotato key           sign up: blotato.com/?ref=marcus   key: my.blotato.com/settings/api
  PASS  accepted. Your connected accounts:
        youtube    Your Page Name               id 40000
        tiktok     yourpagehandle               id 50000

5. Apify token           optional: console.apify.com/account/integrations
  SKIP  not set. Research runs on YouTube only, which is fine.

PASS. Next: /factory research "<your niche>", then /factory page.
```

The accounts above are an example. Yours will be whatever you connected in Blotato.

Nothing here bills you. The Higgsfield check is a free styles call and the Blotato check just lists
accounts. The first thing that costs money is a clip, and the price prints before it runs.
