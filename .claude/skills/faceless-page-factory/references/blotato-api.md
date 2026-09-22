# Blotato, what this skill uses

Shapes taken from a booking script that has scheduled a live page daily for a month. Header on every REST call:
`blotato-api-key: <key>`. Base `https://backend.blotato.com`.

- **Accounts:** through Blotato's MCP endpoint, `POST https://mcp.blotato.com/mcp`, JSON-RPC `tools/call`,
  tool `blotato_list_accounts`. The result text is a JSON list with `id`, `platform`, `name`.
- **Upload:** same endpoint, tool `blotato_create_presigned_upload_url` with `{filename}`; PUT the mp4 to
  `presignedUrl` with `Content-Type: video/mp4`; use `publicUrl` as the media URL.
- **Post:** `POST /v2/posts`:
  - TikTok: `{"post":{"accountId":"…","target":{"targetType":"tiktok","privacyLevel":"PUBLIC_TO_EVERYONE",
    "disabledComments":false,"disabledDuet":false,"disabledStitch":false,"isBrandedContent":false,
    "isYourBrand":false,"isAiGenerated":true},"content":{"text":"caption","mediaUrls":["…"],"platform":"tiktok"}},
    "scheduledTime":"2026-09-25T17:00:00Z"}`
  - YouTube: target `{"targetType":"youtube","title":"…","privacyStatus":"public","isMadeForKids":false,
    "containsSyntheticMedia":true,"shouldNotifySubscribers":false}`, content `text` empty, `platform` youtube.
  - Response carries `postSubmissionId` (or `id`).
- **Schedules:** `GET /v2/schedules?limit=100&cursor=…`. Paginate by cursor. `?page=` is ignored and returns
  the same first hundred every time.
- **Errors:** a 422 puts the reason in the response body. Read it; a bare status tells you nothing.
