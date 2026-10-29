import os, re, glob, shutil
from os import path

ROOT = path.dirname(path.abspath(__file__))
os.chdir(ROOT)

DIRS = ['videos', 'videos_full', 'videos_cut', 'videos_data', 'videos_frames',
        'videos_hls', 'videos_posters', 'videos_trailers']

files = []
for d in DIRS:
    # só o que começa com número (001_..., 002...); placeholders como __ ficam
    items = [f for f in sorted(glob.glob(f'{d}/*')) if re.match(r'\d+', path.basename(f))]
    files += items
    print(f'{d:18s} {len(items)} item(ns)')

if not files:
    raise SystemExit('\nNada para apagar')

if input(f'\nApagar TODOS os {len(files)} item(ns) de todas as pastas? (s/N): ').strip().lower() != 's':
    raise SystemExit('Cancelado')

for f in files:
    shutil.rmtree(f) if path.isdir(f) else os.remove(f)
    print('APAGOU', f)

print(f'\nOK: {len(files)} item(ns) apagados (as pastas foram mantidas)')
