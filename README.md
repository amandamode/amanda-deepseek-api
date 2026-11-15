# Amanda DeepSeek API

[![GitHub Release](https://img.shields.io/github/v/release/amandamode/amanda-deepseek-api)](https://github.com/amandamode/amanda-deepseek-api/releases/latest)
[![MIT License](https://img.shields.io/github/license/amandamode/amanda-deepseek-api)](LICENSE)
[![Stars](https://img.shields.io/github/stars/amandamode/amanda-deepseek-api)](https://github.com/amandamode/amanda-deepseek-api/stargazers)
[![Forks](https://img.shields.io/github/forks/amandamode/amanda-deepseek-api)](https://github.com/amandamode/amanda-deepseek-api/forks)
[![Open issues](https://img.shields.io/github/issues/amandamode/amanda-deepseek-api)](https://github.com/amandamode/amanda-deepseek-api/issues)
[![Last commit](https://img.shields.io/github/last-commit/amandamode/amanda-deepseek-api)](https://github.com/amandamode/amanda-deepseek-api/commits/main/)

适用于支持 [Agent Skills](https://agentskills.io/specification) 的工具，例如 Codex、Claude Code、Cursor。用**你自己的 DeepSeek API Key** 搜网页、以图搜图、读 PDF、识别图片文字、转写录音和生成配音。也可以直接在终端运行附带的 Python CLI。请求直连 DeepSeek 官方 API，费用由对应的 DeepSeek 账户承担。

运行环境需要 **Python 3.9 或更新版本**，能够访问 DeepSeek 官方 API，并能读取 `DEEPSEEK_API_KEY`。无需额外安装 Python 包。已验证从 GitHub 安装到 Codex，并用 Python 3.13 实测 API 调用。Python 3.9 和 3.10 已检查脚本语法。

## 快速开始

### 1. 安装 Skill

在项目目录打开终端。使用 `npx skills` 安装需要 Node.js 22.20+ 和 npm。

```bash
npx skills add amandamode/amanda-deepseek-api --skill amanda-deepseek-api
```

按提示选择你使用的 Agent。也可以用 `--agent` 指定目标，例如 `--agent codex`。查看 [安装工具支持的 Agent](https://github.com/vercel-labs/skills#supported-agents)。

手动安装时，从 [Releases](https://github.com/amandamode/amanda-deepseek-api/releases/latest) 下载 `Amanda-DeepSeek-API-v1.1.0.zip`，把解压得到的 `amanda-deepseek-api` 文件夹放进你的 Agent 所用的技能目录。例如 Codex 项目的 `.agents/skills/` 或 Claude Code 项目的 `.claude/skills/`。

### 2. 配置你自己的 Key

去 [DeepSeek 开放平台](https://platform.deepseek.com/api_keys) 获取 API Key，然后把它配置为 Agent 运行环境里的 `DEEPSEEK_API_KEY`。如果从终端启动 Agent，可以在同一个终端用下面的命令隐藏输入：

```bash
# Bash
read -r -s -p 'DeepSeek API Key: ' DEEPSEEK_API_KEY
export DEEPSEEK_API_KEY
```

```zsh
# macOS 默认的 zsh
read -rs 'DEEPSEEK_API_KEY?DeepSeek API Key: '
export DEEPSEEK_API_KEY
```

终端里的变量会随之后从该终端启动的进程传递。使用已经打开的桌面应用时，通过应用或运行环境提供的密钥配置注入。密钥保存在自己的环境里即可，勿发到对话或提交进 Git。

### 3. 给 Agent 一条指令

- 「用 `$amanda-deepseek-api` 查 DeepSeek 最近的官方发布，给我原文链接。」
- 「用 Amanda DeepSeek API 以图搜图，列出这张图的候选出处和原网页链接。」
- 「用 Amanda DeepSeek API 读这份 PDF，列出付款金额和日期，并标明出处。」
- 「用 Amanda DeepSeek API 识别这张图片上的文字，保留编号。」
- 「用 Amanda DeepSeek API 把这段 WAV 转成文字，再用 Stella 给改好的稿子配音。」

## 能力与命令

在 Skill 文件夹内运行 `python3 scripts/deepseek_tools.py <命令>`。脚本会把 JSON 结果写到标准输出，诊断写到标准错误。

| 想做什么 | 命令示例 | 返回什么 |
| --- | --- | --- |
| 找网页来源 | `search "DeepSeek 应用 API" --count 5` | 结构化搜索结果 |
| 查资料并回答 | `web "DeepSeek 最近开放了哪些 API？"` | 回答及 API 返回的搜索记录和引用 |
| 深入查证 | `web "对照 DeepSeek 的 ASR 和 TTS 文档" --thinking` | 开启深度思考后的回答与工具记录 |
| 找图片出处 | `image-search photo.jpg "找这张图的出处"` | 图片搜索调用记录、候选网页和图片地址 |
| 获取网页正文 | `fetch "https://example.com/"` | 网页标题和 Markdown |
| 对指定链接提问 | `read "https://example.com/" "总结网页用途"` | 阅读工具记录和模型回答 |
| 对 PDF 或 Office 文件提问 | `document report.pdf "列出文件里的关键日期"` | 回答及临时上传的清理状态 |
| 提取图片文字 | `ocr invoice.png` | 逐页识别结果 |
| 把文字变成配音 | `tts "你好，欢迎收听。" --voice stella --output narration.wav` | WAV 文件、时长和音色 |
| 把录音转成文字 | `asr recording.wav` | 转写文字和音频时长 |
| 普通问答 | `chat "把这段话改成口语" --safety-high` | Flash 回答，可开启高级内容审核 |

扫描版或带图表的 PDF 可给 `document` 加 `--layout`。若模型报告 PDF 内容不可读，Skill 会尝试 OCR 后再回答，结果中的 `source: "ocr"` 表示回答基于识别出的文字，本次调用也会增加 OCR 与模型用量。每个命令都支持 `--help`，更多说明见 [接口与结果核对](references/api.md)。

## 配音试听

同一句普通话由 DeepSeek 的两款音色合成。

> 今天阳光正好，我们来测试一下中文语音合成和语音识别。

[海星 Stella 女声（WAV，4.92 秒）](assets/deepseek-stella-zh.wav?raw=true) · [暗潮 Tide 男声（WAV，5.44 秒）](assets/deepseek-tide-zh.wav?raw=true)

## 实测记录

| 测试项 | 结果 |
| --- | --- |
| 普通联网和深度思考搜索 | 两种模式均实际调用了搜索工具，答对公告里的五个独立接口，并返回了 DeepSeek 官方引用。 |
| 以图搜图 | 用 Grace Hopper 的公开样图实测，返回已完成的 `image_search` 调用及 8 条带图片地址的候选结果。 |
| PDF 文件问答 | v1.1.0 的 CLI 从带文字层 PDF 和扫描 PDF 中读出了测试编号 `FIR-CC1CB8D`。两次上传均返回 `deleted: true`。 |
| 独立 Search、Fetch 和 OCR | Search 返回 5 条结果。Fetch 抓到官方公告正文。OCR 读出了测试图中的编号 `ORCHID-5837`。 |
| Stella 配音和 ASR | 生成了 4.92 秒的中文 WAV。把它交给 ASR 后，转写与原文逐字一致，包含标点。 |
| 阅读链接 | 成功抓取官方公告，模型答错了 Demo 仓库名。原文链接指向 `deepseek-ai/chat-demo`。 |
| 内容审核 | 高级审核参数可随普通问答提交并正常返回。拦截效果未测试。 |

以上为 2026 年 11 月 14 日至 15 日的 DeepSeek 官方 API 实测。以图搜图和更新后的 PDF 问答通过本仓库的 CLI 运行。 [DeepSeek 官方发布公告](https://api-docs.deepseek.com/zh-cn/news/news261113/)

## 常见问题

| 现象 | 怎么处理 |
| --- | --- |
| 提示缺少 Key 或返回 `401` | 确认 Agent 或脚本所在的进程读到了有效的 `DEEPSEEK_API_KEY`。 |
| 返回 `402` 或 `429` | 分别检查 DeepSeek 账户余额或调用限速。 |
| 搜索回答没有来源 | 查看工具调用和引用字段。需要读原文时，可以用独立 Fetch。 |
| PDF 图表没有识别完整 | 用 `--layout` 后，再和原文件核对数字、标注和单位。 |
| MP3 转写失败 | 先转换为 16 位 PCM WAV 或 Ogg Opus。ASR 单文件最大 8 MiB、最长 120 秒。 |
| WAV 输出路径报错 | 先建好目标目录，并使用新文件名。脚本要求 `.wav` 扩展名。 |

提交的查询、网页地址或文件会发送给 DeepSeek。文件问答结束后，脚本会尝试删除本次上传的文件，上传时也会请求一小时有效期。用量按 DeepSeek 账户计费。 [官方价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)

由 **Amanda Mode** 维护，按 [MIT 许可证](LICENSE) 发布。使用 DeepSeek 公开 API。
