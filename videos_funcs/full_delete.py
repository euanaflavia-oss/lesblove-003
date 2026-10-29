import os, glob
from os import path

FULL = 'videos_full'
CUT  = 'videos_cut'

freed = 0
for mp4 in sorted(glob.glob(f'{FULL}/[0-9]*.mp4')):
    cut = f'{CUT}/{path.basename(mp4)}'
    if not (path.exists(cut) and path.getsize(cut) > 0):
        print('PULOU (sem corte)', mp4)
        continue
    freed += path.getsize(mp4)
    os.remove(mp4)
    print('APAGOU', mp4)

print(f'{freed / 1024**3:.2f} GB liberados')
