# Amanda DeepSeek API

在 Codex 或 Claude Code 里，用**你自己的 DeepSeek API Key** 搜网页、读 PDF、识别图片文字、转写录音和生成配音。请求直连 DeepSeek 官方 API，费用由对应的 DeepSeek 账户承担。

## 快速开始

### 1. 安装 Skill

在项目目录打开终端。安装需要 Node.js 22.20+ 和 npm，运行脚本需要 Python 3.9+，无需安装 Python 包。

```bash
npx skills add amandamode/amanda-deepseek-api --skill amanda-deepseek-api
```

按提示选择 Codex 或 Claude Code。想明确安装到 Codex，可以在命令末尾加 `--agent codex`。手动安装时，把本仓库文件放入项目的 `.agents/skills/amanda-deepseek-api/`（Codex）或 `.claude/skills/amanda-deepseek-api/`（Claude Code），保留目录结构。

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
| 获取网页正文 | `fetch "https://example.com/"` | 网页标题和 Markdown |
| 对指定链接提问 | `read "https://example.com/" "总结网页用途"` | 阅读工具记录和模型回答 |
| 对 PDF 或 Office 文件提问 | `document report.pdf "列出文件里的关键日期"` | 回答及临时上传的清理状态 |
| 提取图片文字 | `ocr invoice.png` | 逐页识别结果 |
| 把文字变成配音 | `tts "你好，欢迎收听。" --voice stella --output narration.wav` | WAV 文件、时长和音色 |
| 把录音转成文字 | `asr recording.wav` | 转写文字和音频时长 |
| 普通问答 | `chat "把这段话改成口语" --safety-high` | Flash 回答，可开启高级内容审核 |

带图表的 PDF 可给 `document` 加 `--layout`。TTS 提供 **Stella 女声**和 **Tide 男声**。每个命令都支持 `--help`，更多说明见 [接口与结果核对](references/api.md)。

## 实测记录

| 测试项 | 结果 |
| --- | --- |
| 普通联网和深度思考搜索 | 两种模式均实际调用了搜索工具，答对公告里的五个独立接口，并返回了 DeepSeek 官方引用。 |
| PDF 文件问答 | 正确读出只写在一页测试 PDF 里的随机编号 `CEDAR-FEEE8FFA`。测试结束后，文件删除接口返回 `deleted: true`。 |
| 独立 Search、Fetch 和 OCR | Search 返回 5 条结果。Fetch 抓到官方公告正文。OCR 读出了测试图中的编号 `ORCHID-5837`。 |
| Stella 配音和 ASR | 生成了 4.92 秒的中文 WAV。把它交给 ASR 后，转写与原文逐字一致，包含标点。 |
| 阅读链接 | 成功抓取官方公告，模型答错了 Demo 仓库名。原文链接指向 `deepseek-ai/chat-demo`。 |
| 内容审核 | 高级审核参数可随普通问答提交并正常返回。拦截效果未测试。 |

以上为 2026 年 11 月 14 日的 DeepSeek 官方 API 实测。仓库的 CLI 另外用模拟响应验证了请求格式和文件清理，并从 GitHub 安装到干净的 Codex 项目验证了包结构。 [DeepSeek 官方发布公告](https://api-docs.deepseek.com/zh-cn/news/news261113/)

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

由 **Amanda Mode** 维护。使用 DeepSeek 公开 API。
