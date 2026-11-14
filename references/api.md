# DeepSeek endpoints and interpretation

- `search` and `fetch` use the standalone [Search and Fetch API](https://api-docs.deepseek.com/zh-cn/guides/search/). Search can return an empty result array. Fetch returns Markdown that can omit details such as link destinations on some pages.
- `web` and `read` use the [server-side web tools](https://api-docs.deepseek.com/zh-cn/guides/web_tools/) via the Anthropic-compatible Messages endpoint with `deepseek-flash`. Inspect `server_tool_use`, tool result blocks, and text citations in the JSON. The model chooses whether to call a declared tool.
- `document` uses [Files API document parsing](https://api-docs.deepseek.com/zh-cn/guides/document_parsing/). Use the default text mode for text extraction. Add `--layout` if document Q&A depends on figures or diagrams. The response includes the model result and cleanup status. A request that times out during upload may still create a file. The upload requests a one-hour expiry.
- `ocr` uses the [standalone OCR API](https://api-docs.deepseek.com/zh-cn/guides/ocr/). Check `pages[].text` and `finish_reason`. `length` means a page result is incomplete. The service may send an error object inside an HTTP 200 response.
- `tts` uses [full-text TTS](https://api-docs.deepseek.com/zh-cn/guides/tts/) with `stella` or `tide`. The CLI saves WAV and fills unknown streaming RIFF/data sizes; success returns the output filename and duration.
- `asr` uses [whole-file ASR](https://api-docs.deepseek.com/zh-cn/guides/asr/). Use 16-bit PCM WAV or Ogg Opus, up to 8 MiB and 120 seconds. Stereo recognition uses the left channel.
- `chat --safety-high` requests [high safety review](https://api-docs.deepseek.com/zh-cn/guides/safety/). Check the stop reason for refusal. A normal response to benign input does not test moderation coverage.

Costs vary by requests, pages, audio duration, and model tokens. See [official prices](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/). Check key and provider on `401`, the account balance on `402`, and the reported limits on `429`. After an ambiguous transport failure, check whether the operation completed before retrying a paid call.
