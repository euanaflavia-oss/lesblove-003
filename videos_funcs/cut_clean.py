import os, sys, time, glob
import subprocess as subp
from os import path

FULL    = 'videos_full'
CUT     = 'videos_cut'
DEFAULT = 10
TIMEOUT = 10
os.makedirs(CUT, exist_ok=True)


def ask(prompt, timeout, default):
    print(f'{prompt} [{default}] ({timeout}s): ', end='', flush=True)
    buf = ''
    if os.name == 'nt':
        import msvcrt
        end = time.time() + timeout
        while time.time() < end:
            if msvcrt.kbhit():
                c = msvcrt.getwche()
                if c in '\r\n': print(); return buf.strip() or default
                if c == '\b':   buf = buf[:-1]
                else:           buf += c
            time.sleep(0.02)
    else:
        import select
        if select.select([sys.stdin], [], [], timeout)[0]:
            return sys.stdin.readline().strip() or default
    print()
    return default


def to_secs(x):
    x = str(x).strip().replace(',', '.')
    if ':' in x:
        t = 0.0
        for p in x.split(':'): t = t * 60 + float(p)
        return t
    return float(x)


while True:
    try:    SECS = to_secs(ask('CUT_INI (s ou mm:ss)', TIMEOUT, DEFAULT)); break
    except: print('Valor inválido')

for mp4 in sorted(glob.glob(f'{FULL}/[0-9]*.mp4')):
    out = f'{CUT}/{path.basename(mp4)}'
    if path.exists(out): continue
    subp.run(f'ffmpeg -y -v error -ss {SECS} -i "{mp4}" -c copy "{out}"', shell=True)
    print('OK', out, f'(corte inicial: {SECS:g}s)')
