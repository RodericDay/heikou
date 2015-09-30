import os
import collections

# Explore MKV file structure
# os.system("mkvmerge -i s01e11.mkv")

# Extract english subtitles
# os.system("mkvextract tracks s01e11.mkv 3:sub-eng.srt")

# Read japanese subtitle file in ASS format
PRELUDE = []
EVENTS = []
ASS = collections.namedtuple("ASS", "Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")
with open('sub-jap.ass') as jpn:

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
with open('sub-eng.srt') as fp:
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
with open('sub-dbl.ass', 'w') as dbl:

    for line in PRELUDE:
        dbl.writelines(line)

    for event in sorted(EVENTS, key=lambda e: e.Start):
        line = 'Dialogue: '+','.join(event)
        if not line.endswith('\n'): line += '\n'
        dbl.writelines(line)


# Inject subs back into MKV file
os.system("mkvmerge -o new.mkv s01e11.mkv --language 1:jpn sub-jap.ass --default-track 0 --language 4:mis sub-dbl.ass")
os.system("mkvmerge -i new.mkv")
