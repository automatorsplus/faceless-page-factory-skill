# Higgsfield API, what this skill uses

Read from docs.higgsfield.ai on 2026-09-22. Model pages on the console are the authority; the OpenAPI file is
supplementary and does not list every model.

- **Auth:** header `Authorization: Key <id>:<secret>`. The Python SDK (`higgsfield-client`) reads `HF_KEY`.
- **Free call to prove a key:** `GET https://api.higgsfield.ai/v1/text2image/soul-styles`. 200 with a valid key.
- **Clips:** `bytedance/seedance-2.5/text-to-video`. `prompt`, `duration` 4 to 30, `resolution` 480p or 720p,
  `aspect_ratio` (9:16 for shorts), `generate_audio` (default true), `output_format` mp4. Response `video.url`.
- **Images:** `higgsfield-ai/soul/standard`. `prompt`, `aspect_ratio` (1:1, 16:9, 9:16 and more), `resolution`
  720p or 1080p, `enhance_prompt`, `batch_size` 1 or 4. Response `images[0].url`.
- **SDK:** `higgsfield_client.subscribe(model, arguments=..., on_enqueue=...)` polls and returns the completed
  payload. Errors: `CredentialsMissedError`, `InsufficientCreditsError`, `HiggsfieldClientError`.
- **Billing:** successful requests only. Failed and NSFW are not charged and reserved credits are refunded.
  Price per model is on the console; pass it to `clip.py --price-usd` so it prints before the call.
