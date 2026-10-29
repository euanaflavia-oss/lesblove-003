import os, re, json, glob
import subprocess as subp
from os import path

# pip install yt-dlp  |  ffmpeg no PATH
FULL = 'videos_full'
DATA = 'videos_data'
os.makedirs(FULL, exist_ok=True)
os.makedirs(DATA, exist_ok=True)

COOKIES = '--cookies cookies.txt' if path.exists('cookies.txt') else ''


DIRS = ['videos_full', 'videos_cut', 'videos_data', 'videos_frames',
        'videos_hls', 'videos_posters', 'videos_trailers']


def next_id():
    """maior id existente + 1; repositório novo pergunta o número inicial"""
    ids = set()
    for d in DIRS:
        for f in glob.glob(f'{d}/*'):
            m = re.match(r'(\d+)', path.basename(f))
            if m: ids.add(int(m.group(1)))
    if ids:
        n = max(ids) + 1
    else:
        s = input('Repositório novo. Número inicial [001]: ').strip()
        if s and not s.isdigit(): raise SystemExit('Número inválido')
        n = int(s) if s else 1
    return f'{n:03d}'


URL   = input('URL: ').strip()
TITLE = input('TITLE: ').strip()
ID    = next_id()
OUT   = f'{FULL}/{ID}'

# maior resolução + melhor áudio, mesclado em mp4
subp.run(
    f'yt-dlp {COOKIES} -i "{URL}" '
    f'-f "bestvideo+bestaudio/best" --merge-output-format mp4 '
    f'-o "{OUT}.%(ext)s"',
    shell=True,
)

if not path.exists(f'{OUT}.mp4'):
    raise SystemExit(f'Falhou: {OUT}.mp4 não foi criado')

# metadados
out  = subp.run(f'yt-dlp {COOKIES} -i "{URL}" --dump-json', capture_output=True, shell=True, text=True)
try:    meta = json.loads(out.stdout)
except: meta = {}
meta['input_url']   = URL
meta['input_title'] = TITLE
json.dump(meta, open(f'{DATA}/{ID}_download.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=4)

size = path.getsize(f'{OUT}.mp4') / 1024**3
print(f'OK: {OUT}.mp4 ({size:.2f} GB) | {DATA}/{ID}_download.json')
