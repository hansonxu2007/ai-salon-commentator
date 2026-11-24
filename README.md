# AI Salon Commentator

SJTU Global College 建筑文化沙龙本地控制台。React / TypeScript / Vite + FastAPI，使用真实 DeepSeek ASR、deepseek-flash（非思考模式）和 TTS；没有模拟 AI 响应。

面向 Windows 桌面浏览器的活动 Demo，支持录音计时、长音频切分、英文点评、Stella / Tide 语音、文本编辑、失败重试及一键启动。此仓库是活动工具源码，不代表学校官方发布。

开源仓库不提供 API Key、学生录音或含密钥的活动分发包。请使用自己的 DeepSeek Key；默认打包仅复制空白配置。`--include-key` 仅用于明确授权的私下分发，生成的 ZIP 和 `.env` 不得上传到公开仓库或 GitHub Releases。

## 无需安装依赖的 Windows 便携版

将 `release/AI-Salon-Commentator-Windows-x64.zip` 发给对方。完整解压到可写文件夹，填写其中 `.env` 的 Key，再双击 `AI-Salon-Commentator.exe`。自动打开默认浏览器，保留控制台窗口，关闭窗口或 Ctrl+C 停止。对方无需安装 Python、Node.js、FFmpeg，也不需要运行 `start.bat`。需要联网调用 DeepSeek，并使用 Chrome / Edge。必须保留 `_internal`，不能只发送 EXE。默认端口 8765，遇到占用会复用 Salon 服务或尝试附近空闲端口。目标为 Windows x64；尚未在另一台干净电脑上验收。

开发机重新打包：`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-portable.ps1`。程序使用 PyInstaller onedir 打包；真实 `.env` 不会复制或写入 EXE，ZIP 仅包含空白配置、程序、资源与许可说明，排除运行时录音。

## Windows 运行

1. 安装 Python 3.11+（python.org，勾选 Add Python to PATH），安装 Node.js LTS（nodejs.org，建议 22.12+）。
2. 将 `.env.example` 复制为 `.env`，填写 `DEEPSEEK_API_KEY`。密钥只由 Python 后端读取。不要提交 `.env`。
3. 双击 `start.bat`，首次运行需要网络安装依赖。脚本检查 Python / Node.js 版本，使用锁定版本安装后端依赖，并在前后端均就绪后自动调用 Windows 默认浏览器打开 http://127.0.0.1:5173/ 。默认浏览器建议设为 Chrome 或 Edge；如果未自动打开，可手动访问该地址。后续运行优先使用本地 npm 缓存，但缺包时仍需要联网。脚本会创建虚拟环境并在后台启动服务，日志保存在 `.tmp`。重复运行会复用已启动的本项目服务；其他程序占用端口时会提示，不会强制结束进程。
4. Chrome / Edge 允许麦克风权限。Windows 设置中允许桌面应用访问麦克风，并确认现场音响是默认输出设备。

FFmpeg：依赖中的 `imageio-ffmpeg` 带有本地 FFmpeg 可执行文件，默认无需另行安装。也可从 ffmpeg.org 的 Windows 构建入口下载并将 bin 加入 PATH，或在 `.env` 设置 `FFMPEG_PATH=C:\tools\ffmpeg\bin\ffmpeg.exe`。优先级：环境变量、PATH、内置版本。

手动安装 / 启动（项目根目录）：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
# 编辑 .env 填写密钥
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
# 另开终端
cd frontend
npm install
npm run dev -- --port 5173 --strictPort
```

## 使用

选择 Speaker → Start Recording → Stop Recording → 自动转写、点评、合成 → 手动 Play Commentary。合成完成不会自动播放。Stop Audio 停止播放。Reset Session 清空本轮并递增 Speaker 编号。

Transcript 可直接编辑，Regenerate Commentary 始终读取最新文本。Commentary 编辑或切换音色会使旧音频失效，点击 Update Audio 合成当前文本。处理和播放期间锁定编辑，避免异步结果覆盖修改。失败后 Notice 提供当前阶段的 Retry，保留已有文本；转写失败保留浏览器内录音，可重试。刷新页面会丢失录音和文本。可手动输入 Transcript，直接验证点评和合成。

录音由 MediaRecorder 在内存中收集；上传限制 200 MiB。FFmpeg 转成 16kHz 单声道 PCM16 WAV，再按样本精确切为 60 秒，包含尾段，顺序调用 ASR。每段约 1.83 MiB，符合官方 8 MiB / 120 秒限制。处理是同步接口，无数据库或任务队列；长发言请耐心等待。原始上传和切片在请求结束清理，合成音频存放在 `backend/data`，请在活动后关闭服务并删除该目录内音频以清理存储。仅绑定本机，不应直接暴露到公网。

## 接口和配置

- GET `/api/health`：后端、密钥配置与 FFmpeg 检查（不验证密钥有效性）。
- POST `/api/transcribe`：multipart `file` → `{text, segments}`。
- POST `/api/commentary`：`{text}` → `{text}`。
- POST `/api/synthesize`：`{text, voice: "stella" | "tide"}` → `{audio_url}`。
- GET `/api/audio/{id}.wav`：音频二进制。
- API 文档：http://127.0.0.1:8000/docs 。前端 Vite 将 `/api` 代理到 8000。
- `backend/prompts/commentary_prompt.txt`：独立英文点评规则，可编辑，无需改前端。
- `.env`：`DEEPSEEK_API_KEY`、可选 `FFMPEG_PATH`、`DEEPSEEK_BASE_URL`。

官方文档：[ASR](https://api-docs.deepseek.com/guides/asr/)、[Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)、[TTS](https://api-docs.deepseek.com/guides/tts/)。生成长度由 Prompt 引导；模型实际措辞及朗读时长需要活动前用真实语音测试。

## 检查

```powershell
cd frontend
npm run build
cd ..
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

自动测试覆盖超过 120 秒音频切分及尾段、请求参数、阶段接口和 WAV 完整性；使用隔离的 HTTP mock，不会产生真实 API 费用。真正的麦克风权限、现场音响、密钥权限与三项 AI 服务效果必须在主办电脑上实测。

GitHub Actions 会在 Windows 上执行前端构建和后端测试，不需要真实 API Key。

## 贡献和许可证

欢迎提交 Issue 或 Pull Request。提交前运行上述检查；请勿附带个人录音、真实密钥或本地 `.env`。源码使用 [MIT License](LICENSE)。第三方依赖及打包的 FFmpeg 使用各自许可证，便携包中的 `LICENSES` 包含相应说明；源码许可不替代第三方许可。


