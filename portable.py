"""Windows portable entry point; no Python or Node installation required."""
import argparse
import json
import os
from pathlib import Path
import socket
import sys
import threading
import time
import urllib.request
import webbrowser

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    home = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
    os.environ['SALON_HOME'] = str(home)
    resources = Path(getattr(sys, '_MEIPASS', home))
    if (resources / 'tools/ffmpeg.exe').exists():
        os.environ['FFMPEG_PATH'] = str(resources / 'tools/ffmpeg.exe')
    config = home / '.env'
    if not config.exists():
        config.write_text('DEEPSEEK_API_KEY=\nDEEPSEEK_BASE_URL=https://api.deepseek.com\n', encoding='utf-8')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    port = args.port
    for port in range(args.port, args.port + 10):
        url = f'http://127.0.0.1:{port}'
        try:
            with opener.open(url + '/api/health', timeout=1) as response:
                existing = json.load(response)
            if existing.get('product') == 'ai-salon-commentator':
                print(f'Already running: {url}', flush=True)
                if not args.no_browser:
                    webbrowser.open(url)
                return
        except Exception:
            pass
        server_socket = socket.socket()
        try:
            server_socket.bind(('127.0.0.1', port))
            server_socket.listen(128)
            break
        except OSError:
            server_socket.close()
    else:
        raise RuntimeError('No available local port. Close older Salon windows and retry.')

    from backend.main import app
    import uvicorn
    print(f'AI Salon Commentator: {url}\nConfiguration: {config}\nKeep this window open. Press Ctrl+C to stop.', flush=True)
    if not os.getenv('DEEPSEEK_API_KEY', '').strip():
        print('Add DEEPSEEK_API_KEY to .env, then close this window and reopen the EXE.', flush=True)
    if not args.no_browser:
        def open_when_ready():
            for _ in range(60):
                try:
                    with opener.open(url + '/api/health', timeout=1):
                        webbrowser.open(url)
                        return
                except Exception:
                    time.sleep(.25)
        threading.Thread(target=open_when_ready, daemon=True).start()
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, loop='asyncio', http='h11', ws='none', log_config=None))
    try:
        server.run(sockets=[server_socket])
    finally:
        server_socket.close()

if __name__ == '__main__':
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        input('Startup failed. Press Enter to close...')
