import os, glob
import subprocess as subp
from os import path

CUT = 'videos_cut'
HLS = 'videos_hls'
SEG = 15

for mp4 in sorted(glob.glob(f'{CUT}/[0-9]*.mp4')):
    vid = path.splitext(path.basename(mp4))[0]
    out = f'{HLS}/{vid}'
    if path.exists(f'{out}/index.m3u8'):
        print('PULOU', vid); continue
    os.makedirs(out, exist_ok=True)
    subp.run(f'ffmpeg -y -v error -i "{mp4}" -c copy -f hls -hls_time {SEG} -hls_list_size 0 '
             f'-hls_segment_filename "{out}/vid_%03d.ts" "{out}/index.m3u8"', shell=True)
    print('OK', vid, f'{len(glob.glob(f"{out}/vid_*.ts"))} segmentos')
