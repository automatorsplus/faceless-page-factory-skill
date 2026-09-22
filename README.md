# Faceless Page Factory Skill for Claude Code

> Part of the **Automators+** skills library -- Claude Code skills shared exclusively with the Automators+ community.

A faceless page in a box. Research what is getting views in a niche, create the page, generate
9:16 clips through the Higgsfield API, and schedule a week of posts to TikTok and YouTube through Blotato.
Four steps, one command each. Claude does the writing where you can see it; the scripts do the calls.

## What You Get

- **Research before you pick a niche** -- the top twenty clips by views, under three minutes, with links, then five clip ideas modelled on what is already working. A thin week widens to the month on its own. The step everyone skips
- **The page, made** -- three names and bios to pick from, both handles checked, a logo and a banner generated, a page file with the setup checklist
- **Clips from a prompt** -- Seedance 2.5 through the Higgsfield API, 4 to 30 seconds in one call, 9:16, sound on. Longer clips are stitched from a list of shots
- **Every clip at broadcast loudness** -- normalised to -13.8 LUFS before it can be scheduled, so it never plays quiet next to everyone else's
- **A week booked in one go** -- rendered clips drop into your posting times on both platforms through Blotato, the dates printed before anything is sent
- **Cost quoted first** -- the price prints before every paid call, and a clip that fails is not charged
- **A setup that proves each key** -- one command checks the tools and tests each key with a call that costs nothing

## Prerequisites

### 1. A Higgsfield API key

Create one at [console.higgsfield.ai](https://console.higgsfield.ai). It comes as `id:secret`. Pay as you go,
separate from a Higgsfield subscription.

### 2. A Blotato account with the page's TikTok and YouTube connected

Connect the accounts in Blotato, then Settings, API, copy the key. Sign up at [blotato.com](https://blotato.com/?ref=marcus).


### 3. Put both keys in `.env`

Copy `.claude/skills/faceless-page-factory/.env.template` to `.env` at your project root and paste the keys in.
The skill finds it there. Never paste a key into the chat.

```
HF_KEY=id:secret
BLOTATO_API_KEY=your_key_here
APIFY_TOKEN=            optional, adds TikTok to research
```

### Where to get each one

| | Sign up | The key itself |
| --- | --- | --- |
| Higgsfield | [higgsfield.ai](https://higgsfield.ai) | [console.higgsfield.ai](https://console.higgsfield.ai) |
| Blotato | [blotato.com](https://blotato.com/?ref=marcus) | Settings, API, or [my.blotato.com/settings/api](https://my.blotato.com/settings/api) |
| Apify (optional) | [apify.com](https://apify.com) | [console.apify.com/account/integrations](https://console.apify.com/account/integrations) |

The setup prints these links too, so you do not need to come back here.

### 4. Tools

```bash
brew install ffmpeg yt-dlp
pip3 install higgsfield-client
```

### 5. Run the setup

```bash
bash .claude/skills/faceless-page-factory/scripts/setup.sh
```

Interview style: it checks the tools, finds the keys, proves each with a free call and lists your Blotato
accounts with their ids. When it prints PASS you are ready. Claude runs this for you the first time.

## Install the Skill

### Option 1: into a project you already have

```bash
git clone https://github.com/automatorsplus/faceless-page-factory-skill
cp -r faceless-page-factory-skill/.claude/skills/faceless-page-factory /path/to/your-project/.claude/skills/
```

Restart Claude Code in that project and the skill is live.

### Option 2: use the clone as the project

```bash
git clone https://github.com/automatorsplus/faceless-page-factory-skill
cd faceless-page-factory-skill
```

Open that folder in Claude Code. Everything, including the pages you make, lives here.

## Try It

Say one of these in Claude Code:

- Research what is going viral in oddly satisfying right now and give me five clip ideas.
- Start a faceless page for AI food slides. Three names, check the handles, make the logo and banner.
- Make a 10 second clip: a glossy jelly cube sliding down a marble ramp, macro, soft studio light.
- Schedule everything I've rendered into this week's slots on TikTok and YouTube.

Claude shows you the research table, the names, every clip and the booking dates before anything paid or
posted happens.

## How It Works

The skill definition is in [`.claude/skills/faceless-page-factory/SKILL.md`](.claude/skills/faceless-page-factory/SKILL.md).
`scripts/research.py` pulls the top clips, `page.py` checks handles and makes the art, `clip.py`
generates through the API and normalises loudness, `schedule.py` uploads and books through Blotato. The API
shapes are in `references/`.

## License

MIT

---

*Shared with the Automators+ community*
