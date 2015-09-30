import os, re, collections
import heikou

def walk(DIR, FMT):
    for line in os.listdir(DIR):
        if line.startswith('.'): continue
        match = re.fullmatch(FMT, line)
        n, fn = int(match.group(1)), os.path.join(DIR, match.group(0))
        yield n, fn


LIST = collections.defaultdict(list)

MKV_DIR = './Neon Genesis Evangelion/mkv'
MKV_FMT = r'NGE-(\d+).mkv'
for n, fn in walk(MKV_DIR, MKV_FMT):
    LIST[n].append(fn)

SUB_DIR = './Neon Genesis Evangelion/jpn'
SUB_FMT = r'Neon Genesis Evangelion (\d+).ass'
for n, fn in walk(SUB_DIR, SUB_FMT):
    LIST[n].append(fn)

OUT_DIR = './Neon Genesis Evangelion'
OUT_FMT = 'NGN-s{:0>2}e{:0>2}.mkv'
for n, (mkv, sub) in LIST.items():
    out = OUT_FMT.format(1, n)
    heikou.merge(mkv, sub, out)
