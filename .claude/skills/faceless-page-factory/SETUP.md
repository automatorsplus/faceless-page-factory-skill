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
