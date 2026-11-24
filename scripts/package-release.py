"""Create a clean distributable without local credentials or test audio."""
import importlib.metadata
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import argparse
from dotenv import dotenv_values

parser = argparse.ArgumentParser()
parser.add_argument('--include-key', action='store_true', help='Explicitly include the local DeepSeek key in the distributable .env')
args = parser.parse_args()

root = Path(__file__).resolve().parents[1]
folder = root / 'release/AI-Salon-Commentator'
notices = folder / 'LICENSES'
notices.mkdir(exist_ok=True)
for distribution in importlib.metadata.distributions():
    for entry in distribution.files or []:
        if Path(str(entry)).name.lower().startswith(('license', 'copying', 'notice')):
            source = distribution.locate_file(entry)
            if source.is_file():
                destination = notices / distribution.metadata['Name'] / Path(str(entry)).name
                destination.parent.mkdir(exist_ok=True, parents=True)
                shutil.copyfile(source, destination)
python_license = Path(sys.base_prefix) / 'LICENSE.txt'
if python_license.exists():
    shutil.copyfile(python_license, notices / 'Python-LICENSE.txt')
for package in ('react', 'react-dom', 'scheduler', 'lucide-react'):
    source = root / 'frontend/node_modules' / package / 'LICENSE'
    if source.exists():
        shutil.copyfile(source, notices / f'{package}-LICENSE.txt')
ffmpeg = folder / '_internal/tools/ffmpeg.exe'
info = subprocess.run([str(ffmpeg), '-L'], capture_output=True, text=True)
(notices / 'FFmpeg-build-license.txt').write_text(info.stdout + info.stderr, encoding='utf-8')
if args.include_key:
    config = dotenv_values(root / '.env')
    key = config.get('DEEPSEEK_API_KEY', '').strip()
    if not key:
        raise SystemExit('Cannot package: DEEPSEEK_API_KEY is empty.')
    base = config.get('DEEPSEEK_BASE_URL') or 'https://api.deepseek.com'
    (folder / '.env').write_text(f'DEEPSEEK_API_KEY={key}\nDEEPSEEK_BASE_URL={base}\n', encoding='utf-8')
else:
    shutil.copyfile(root / '.env.example', folder / '.env')
readme = (root / 'PORTABLE-README.txt').read_text(encoding='utf-8')
if args.include_key:
    readme = readme.replace('2. Open .env in Notepad and fill in DEEPSEEK_API_KEY after the equals sign.\n   File names starting with a dot are valid on Windows. Do not rename it .env.txt.', '2. The API key is already configured. No installation or configuration is required.\n   This package contains a private API key. Share it only with intended recipients.')
(folder / 'PORTABLE-README.txt').write_text(readme, encoding='utf-8')
archive = root / 'release/AI-Salon-Commentator-Windows-x64.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as out:
    for path in folder.rglob('*'):
        relative = path.relative_to(folder)
        if path.is_file() and (relative.parts[0] in ('_internal', 'LICENSES') or str(relative) in ('AI-Salon-Commentator.exe', '.env', 'PORTABLE-README.txt')):
            out.write(path, Path('AI-Salon-Commentator') / relative)
print(f'Created {archive} ({archive.stat().st_size / 1024**2:.1f} MiB)')
