#!/usr/bin/env python3
'''
Visualize phase.

Loads a reduced .lang or .country file, selects the counts for a single
hashtag (--key), and saves a bar graph of the top 10 keys as a png.

    python3 src/visualize.py --input_path reduced.country --key '#coronavirus'
    python3 src/visualize.py --input_path reduced.lang    --key '#코로나바이러스'

The x-axis is the keys (language or country codes) and the y-axis is the
number of tweets.  Bars are sorted from low to high and only the top 10 are
shown.
'''

# command line args
import argparse
parser = argparse.ArgumentParser(description='visualize phase: bar graph of top-10 keys for a hashtag')
parser.add_argument('--input_path', required=True, help='a reduced .lang or .country file')
parser.add_argument('--key', required=True, help='the hashtag to plot, e.g. "#coronavirus"')
parser.add_argument('--output_path', default=None, help='png path (default: derived from input + key)')
parser.add_argument('--title', default=None,
                    help='override the plot title (useful if no CJK font is installed)')
args = parser.parse_args()

# imports
import os
import sys
import json
from collections import Counter

import matplotlib
matplotlib.use('Agg')  # headless backend: no display needed on the server
import matplotlib.pyplot as plt
from matplotlib import font_manager


def font_supporting(text):
    '''
    Return the name of an installed font whose character map covers every
    character in `text`, or None if no installed font does.

    Titles contain the hashtag itself, which may be Korean/Japanese/Chinese
    (e.g. #코로나바이러스).  The default matplotlib font (DejaVu Sans) has no
    CJK glyphs, so those characters render as empty boxes.  Rather than guess
    at font names, inspect each font's actual cmap via fontTools (which ships
    as a matplotlib dependency).
    '''
    needed = {ord(ch) for ch in text if ord(ch) > 0x024F}  # beyond Latin
    if not needed:
        return None
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return None

    # try the usual CJK fonts first so we don't scan everything unnecessarily
    def rank(f):
        name = f.name.lower()
        return 0 if ('cjk' in name or 'nanum' in name or 'noto' in name
                     or 'baekmuk' in name or name.startswith('un')
                     or 'gothic' in name or 'unifont' in name
                     or 'unicode' in name) else 1

    for entry in sorted(font_manager.fontManager.ttflist, key=rank):
        try:
            ttf = TTFont(entry.fname, fontNumber=0, lazy=True)
            covered = set()
            for table in ttf['cmap'].tables:
                covered.update(table.cmap.keys())
            ttf.close()
        except Exception:
            continue
        if needed <= covered:
            return entry.name
    return None

# load the reduced data
with open(args.input_path, 'r', encoding='utf-8') as f:
    counts = json.load(f)

if args.key not in counts:
    raise SystemExit(f'key {args.key!r} not found in {args.input_path}; '
                     f'available keys: {list(counts.keys())}')

# grab the top 10 keys for this hashtag, then order them low -> high for the plot
counter = Counter(counts[args.key])
top10 = counter.most_common(10)          # highest first
top10 = list(reversed(top10))            # now lowest first (low -> high)

labels = [k for k, v in top10]
values = [v for k, v in top10]

# build the title, then make sure a font exists that can actually draw it
title = args.title or (f'Top {len(labels)} for {args.key}\n'
                       f'({os.path.basename(args.input_path)})')

chosen = font_supporting(title)
if chosen:
    plt.rcParams['font.family'] = chosen
elif any(ord(ch) > 0x024F for ch in title):
    # No installed font covers these characters; they would silently render
    # as empty boxes.  Say so clearly and fall back to an ASCII title.
    ascii_key = args.key.encode('unicode_escape').decode('ascii')
    print(f'WARNING: no installed font can render {args.key!r}; the title '
          f'would appear as empty boxes.\n'
          f'         Install a CJK font, or rerun with '
          f'--title "Top 10 for {ascii_key}".', file=sys.stderr)
    title = (f'Top {len(labels)} for {ascii_key}\n'
             f'({os.path.basename(args.input_path)})')

# build the bar graph
plt.figure(figsize=(10, 6))
plt.bar(range(len(values)), values, color='#1f77b4')
plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
plt.ylabel('number of tweets')
plt.xlabel('language / country code')
plt.title(title)
plt.tight_layout()

# decide where to save
if args.output_path:
    output_path = args.output_path
else:
    safe_key = args.key.replace('#', '').replace('/', '_')
    output_path = f'{args.input_path}.{safe_key}.png'

plt.savefig(output_path, dpi=150)
print('wrote', output_path)
