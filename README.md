# Amanda DeepSeek API

An Agent Skill for calling DeepSeek's official APIs from Codex or Claude Code. It ships with a dependency-free Python 3.9+ CLI for web search, webpage extraction and Q&A, document Q&A, OCR, speech synthesis and transcription.

## Install from ZIP

Extract `amanda-deepseek-api` into your project's `.agents/skills/` for Codex or `.claude/skills/` for Claude Code. Keep the directory structure intact.

After the GitHub repository is published, install with:

```sh
npx skills add amandamode/amanda-deepseek-api --skill amanda-deepseek-api
```

## Use

Set `DEEPSEEK_API_KEY` in the environment that launches the agent or CLI. Use your own [DeepSeek API key](https://platform.deepseek.com/api_keys). Configure it locally through your shell or secret manager.

In Codex, try “Use $amanda-deepseek-api to search DeepSeek's release notes and show me the original links.” You can also run the CLI from the extracted folder:

```sh
python3 scripts/deepseek_tools.py search "DeepSeek 应用 API"
python3 scripts/deepseek_tools.py web "DeepSeek 最近开放了哪些 API 能力？" --thinking
python3 scripts/deepseek_tools.py document report.pdf "Extract the dates and amounts."
python3 scripts/deepseek_tools.py tts "你好，这是 Amanda 的语音示例。" --output speech.wav
python3 scripts/deepseek_tools.py asr speech.wav
```

Use `--help` for all commands. The CLI prints JSON to stdout and writes diagnostics to stderr. See [API behavior and checks](references/api.md) for formats, billing and expected responses.

Built by Amanda Mode. This is an independent integration using DeepSeek's public API.
