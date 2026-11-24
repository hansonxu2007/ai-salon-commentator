AI Salon Commentator - Windows x64 portable edition

1. Extract the ENTIRE folder to a writable local folder (e.g. Desktop).
   Do not run inside the ZIP, and do not move the EXE away from _internal.
2. Open .env in Notepad and fill in DEEPSEEK_API_KEY after the equals sign.
   File names starting with a dot are valid on Windows. Do not rename it .env.txt.
3. Double-click AI-Salon-Commentator.exe. The default browser opens automatically.
   Keep the console window open while using the app. Ctrl+C stops the server.
4. Use Chrome or Edge, allow microphone access, and select the Windows audio output.

Python, Node.js and FFmpeg installation are NOT required on the target computer.
Internet access and a valid DeepSeek API key are required for all AI services.
The program binds only to 127.0.0.1, normally port 8765 (or a nearby free port).
If you edit .env, close the running console and reopen the EXE to reload it.
Recordings/transcripts remain in browser memory; synthesized WAV files are stored
in backend/data next to the EXE. After the event, close the app before cleaning up.

The EXE is unsigned. Organizational policies or antivirus may block unsigned apps;
ask your IT administrator for approval instead of disabling security software.
Windows x64 is the build target. This is not a macOS / Linux / Windows ARM package.

Bundled components include Python, FastAPI, Uvicorn, React, Vite build output,
imageio-ffmpeg and FFmpeg. Third-party license notices are included under _internal.
FFmpeg project and corresponding source/build information:
https://ffmpeg.org/  https://github.com/imageio/imageio-ffmpeg
