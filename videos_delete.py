import os, re, json, glob, shutil
from os import path

ROOT = path.dirname(path.abspath(__file__))
os.chdir(ROOT)

DIRS = ['videos_full', 'videos_cut', 'videos_data', 'videos_frames',
        'videos_hls', 'videos_posters', 'videos_trailers']


def find(num):
    """tudo que pertence ao id, em todas as pastas"""
    out = []
    for d in DIRS:
        for f in sorted(glob.glob(f'{d}/*')):
            m = re.match(r'(\d+)', path.basename(f))
            if m and int(m.group(1)) == num:
                out.append(f)
    return out


def name_of(num):
    for suf, key in (('extract', 'title'), ('download', 'input_title')):
        for f in glob.glob(f'videos_data/*_{suf}.json'):
            m = re.match(r'(\d+)_', path.basename(f))
            if m and int(m.group(1)) == num:
                try:
                    return json.load(open(f, encoding='utf-8')).get(key) or ''
                except Exception:
                    pass
    return ''


NUM = input('NUM: ').strip()
if not NUM.isdigit():
    raise SystemExit('Número inválido')
num = int(NUM)

files = find(num)
if not files:
    raise SystemExit(f'{num:03d}: nada encontrado')

print(f'\n{num:03d}  {name_of(num)}\n')
for f in files:
    print(' -', f + ('/' if path.isdir(f) else ''))

if input(f'\nApagar {len(files)} item(ns) do {num:03d}? (s/N): ').strip().lower() != 's':
    raise SystemExit('Cancelado')

for f in files:
    shutil.rmtree(f) if path.isdir(f) else os.remove(f)
    print('APAGOU', f)