import os, glob
from os import path

CUT      = 'videos_cut'
FRAMES   = 'videos_frames'
POSTERS  = 'videos_posters'
TRAILERS = 'videos_trailers'
HLS      = 'videos_hls'

freed = 0
for mp4 in sorted(glob.glob(f'{CUT}/[0-9]*.mp4')):
    vid = path.splitext(path.basename(mp4))[0]
    falta = []
    if not glob.glob(f'{FRAMES}/{vid}/*.jpg'):                      falta.append('frames')
    if not path.exists(f'{POSTERS}/{vid}.jpg'):                     falta.append('poster')
    if not (path.exists(f'{TRAILERS}/{vid}.mp4')
            and path.getsize(f'{TRAILERS}/{vid}.mp4') > 0):         falta.append('trailer')
    if not path.exists(f'{HLS}/{vid}/index.m3u8'):                  falta.append('hls')
    if falta:
        print('PULOU', vid, '(falta:', ', '.join(falta) + ')')
        continue
    freed += path.getsize(mp4)
    os.remove(mp4)
    print('APAGOU', mp4)

print(f'{freed / 1024**3:.2f} GB liberados')
