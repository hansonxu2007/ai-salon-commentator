# AI Salon Commentator

A local web console for intercultural architecture salons at SJTU Global College. Record a speaker, generate English commentary with DeepSeek, and play it through the venue's sound system.

Built for **Resonance & Rebirth: A Polyphony of Architecture**, the app combines React, TypeScript and FastAPI with DeepSeek speech recognition, `deepseek-flash`, and text-to-speech.

## Features

- Browser microphone recording with a recording timer.
- Automatic transcription of long speeches using 60-second audio segments.
- Warm, context-aware English commentary targeting 80–120 words.
- Editable transcripts and commentary, with regeneration and audio updates.
- Stella and Tide voices, with manual playback and stop controls.
- Visible processing stages and retries that preserve completed work.
- One-click Windows startup and a portable Windows x64 build.

## Quick start on Windows

Install [Python 3.11+](https://www.python.org/downloads/) with **Add Python to PATH** enabled, and [Node.js LTS](https://nodejs.org/) version 22.12 or newer.

1. Clone the repository.
2. Copy `.env.example` to `.env` and set `DEEPSEEK_API_KEY`.
3. Double-click `start.bat`.
4. Allow microphone access in Chrome or Edge.

The launcher installs dependencies, starts both services, and opens the default browser at [http://127.0.0.1:5173](http://127.0.0.1:5173). Running it again reuses existing services. Logs are saved in `.tmp`.

FFmpeg is included through `imageio-ffmpeg`. To use another installation, add it to `PATH` or set `FFMPEG_PATH` in `.env`.

### Manual startup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
Copy-Item .env.example .env
# Set DEEPSEEK_API_KEY in .env before starting the backend.
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
npm ci
npm run dev -- --port 5173 --strictPort
```

## Using the console

Choose a speaker number, click **Start Recording**, and click **Stop Recording** when the speaker finishes. The app automatically transcribes the recording, generates commentary, and synthesizes audio. Click **Play Commentary** when ready to broadcast it.

Edit the transcript and click **Regenerate Commentary** to respond to the revised text. After editing commentary or changing the voice, click **Update Audio** to create matching speech. **Stop Audio** stops playback, and **Reset Session** clears the current session and advances the speaker number.

The Notice area displays progress and offers a retry when a processing step fails. Recordings and text remain in browser memory during the session; synthesized WAV files are saved in `backend/data`.

## Portable Windows build

Build the portable edition on your development computer:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-portable.ps1
```

The resulting archive is written to:

```text
release/AI-Salon-Commentator-Windows-x64.zip
```

Extract the entire archive, configure `.env`, and double-click `AI-Salon-Commentator.exe`. The portable edition includes Python, the compiled frontend, and FFmpeg, so recipients do not need to install development tools. Keep the `_internal` folder beside the executable.

The app opens the default browser automatically and normally uses port `8765`, selecting a nearby port when needed. Keep the console window open while using the app; close it or press **Ctrl+C** to stop. Restart the app after changing `.env`.

## Configuration

| Setting | Purpose |
| --- | --- |
| `DEEPSEEK_API_KEY` | DeepSeek API credentials |
| `DEEPSEEK_BASE_URL` | API base URL; defaults to `https://api.deepseek.com` |
| `FFMPEG_PATH` | Optional path to a custom FFmpeg executable |

Edit `backend/prompts/commentary_prompt.txt` to customize the commentary style, length, and event context.

## How it works

The browser collects microphone audio using `MediaRecorder`. FastAPI receives the recording, and FFmpeg converts it into 16 kHz mono PCM16 WAV. The backend splits it into 60-second segments, including the final partial segment, transcribes each segment in order, and combines the results.

The transcript is sent to `deepseek-flash` with thinking disabled. The resulting English commentary is synthesized through DeepSeek TTS, normalized into a playable WAV file, and made available for manual playback.

## API

| Method | Endpoint | Input | Response |
| --- | --- | --- | --- |
| GET | `/api/health` | — | Service, configuration, and FFmpeg status |
| POST | `/api/transcribe` | Multipart `file` | `{text, segments}` |
| POST | `/api/commentary` | `{text}` | `{text}` |
| POST | `/api/synthesize` | `{text, voice}` | `{audio_url}` |
| GET | `/api/audio/{id}.wav` | — | WAV audio |

Interactive API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) during development. Vite proxies `/api` requests to the backend.

DeepSeek documentation: [Speech to Text](https://api-docs.deepseek.com/guides/asr/), [Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/), and [Text to Speech](https://api-docs.deepseek.com/guides/tts/).

## Development checks

```powershell
cd frontend
npm run build
cd ..
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

Tests cover long-recording segmentation, tail preservation, API request parameters, endpoint behavior, and WAV validation, including streamed WAV headers. GitHub Actions runs the frontend build and backend tests on Windows.

## Contributing

Issues and pull requests are welcome. Run the development checks before submitting changes.

## License

[MIT](LICENSE). Third-party license notices for the portable build are included in its `LICENSES` folder.
