import os, sys
import subprocess as subp
from os import path

ROOT  = path.dirname(path.abspath(__file__))
FUNCS = path.join(ROOT, 'videos_funcs')
os.chdir(ROOT)

STEPS = [
    ('download', 'full_download.py'),     # baixa o vídeo (pede URL e TITLE)
    ('extract',  'data_extract.py'),      # metadados + ffprobe
    ('cut',      'cut_clean.py'),         # corte inicial
    ('frames',   'frames_generate.py'),   # frames a cada N segundos
    ('posters',  'posters_select.py'),    # escolha do poster (1 landscape / 3 portrait)
    ('trailers', 'trailers_maker.py'),    # trailer
    ('hls',      'hls_split.py'),         # segmentos HLS
    ('delete',   'full_delete.py'),       # apaga o vídeo completo
    ('cutdel',   'cut_delete.py'),        # apaga o corte (só se frames/poster/trailer/hls existem)
]

# uso: python videos_funcs_new.py            -> pipeline inteiro
#      python videos_funcs_new.py cut frames -> só esses passos
want = sys.argv[1:] or [n for n, _ in STEPS]
bad  = [w for w in want if w not in dict(STEPS)]
if bad:
    raise SystemExit(f'Passo inválido: {bad}. Opções: {[n for n, _ in STEPS]}')

for name, file in STEPS:
    if name not in want:
        continue
    print(f'\n=== {name} ({file})')
    if subp.run([sys.executable, path.join(FUNCS, file)]).returncode:
        raise SystemExit(f'Parou em: {name}')

print('\nPipeline concluído.')
