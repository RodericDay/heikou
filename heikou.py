import re, os
import subprocess
import collections

def merge(mkv, sub, out):
    # Explore MKV file structure, if sub track is not known
    _ = subprocess.check_output(["mkvmerge", "-i", mkv]).decode()
    #   There's probably a way to extract this integer directly from `re`,
    #   instead of doing all of this
    track_n = re.findall(r'Track ID (\d): subtitles \(SubRip/SRT\)', _)
    if len(track_n) != 1:
        raise RuntimeError("Ambiguous number of subs found:\track_n\track_n"+_)
    track_n = int(track_n[0])

    # Extract english subtitles
    which_where = "{}:{}".format(track_n, '_tmp.srt')
    subprocess.call(["mkvextract", "tracks", mkv, which_where])

    # Read japanese subtitle file in ASS format
    PRELUDE = []
    EVENTS = []
    ASS = collections.namedtuple("ASS", "Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")
    with open(sub) as jpn:

        for line in jpn:

            if line.startswith("Dialogue:"):
                _, data = line.split(": ", 1)
                ass_tuple = ASS(*data.split(',', 9))
                EVENTS.append(ass_tuple)
            else:
                PRELUDE.append(line)

    # Add a style called "Top" to avoid cramming subtitles
    #   The fifth-from-last setting is Alignment. Default is 2 (bottom middle),
    #   we change it to 8 (top middle)
    PRELUDE.insert(-3, "Style: Top,Arial Unicode MS,34,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,8,10,10,10,0\n")

    # Inspect an event to figure out what the defaults are
    defaults = dict(Layer='0', Style='Top', Name='',
                    MarginL='0000', MarginR='0000', MarginV='0000',
                    Effect='')

    # Read english subtitle file, and coerce contents into ASS format
    with open('_tmp.srt') as fp:
        for line_group in fp.read().strip().split('\n\n'):

            # remove weird character 0
            line_group = line_group.replace(b'\xef\xbb\xbf'.decode(), '')
            n, start, end, *text = line_group.replace('\n', '@').replace(' --> ', '@').split('@')

            # time is slightly different format
            # SRT: HH:MM:SS,XXX --> ASS: H:MM:SS.XX
            start = start[1:-1].replace(',', '.')
            end = end[1:-1].replace(',', '.')

            # text seems to be joined with a specific break \N
            text = '\t'+'\\N'.join(text)+'\n'

            ass_tuple = ASS(Start=start, End=end, Text=text, **defaults)

            EVENTS.append(ass_tuple)

    # Write lines back
    # (It may not be necessary to sort files, but it's good for debugging)
    with open('_tmp-dbl.ass', 'w') as dbl:

        for line in PRELUDE:
            dbl.writelines(line)

        for event in sorted(EVENTS, key=lambda e: e.Start):
            line = 'Dialogue: '+','.join(event)
            if not line.endswith('\n'): line += '\n'
            dbl.writelines(line)

    # Inject subs back into MKV file
    subprocess.call(["mkvmerge", "-o", os.path.join('out/', out), mkv,
                    "--language", "0:jpn", sub,
                    "--default-track", "0",
                    "--language", "0:mis", "_tmp-dbl.ass"])

    subprocess.call(["rm", "_tmp.srt", "_tmp-dbl.ass"])
