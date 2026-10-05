#!/usr/bin/env python3
'''
Visualize phase.

Loads a reduced .lang or .country file, selects the counts for a single
hashtag (--key), and saves a bar graph of the top 10 keys as a png.

    python3 src/visualize.py --input_path reduced/reduced.country --key '#coronavirus'
    python3 src/visualize.py --input_path reduced/reduced.lang    --key '#코로나바이러스' \
                             --output_path plots/korean_coronavirus_by_language.png

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
parser.add_argument('--top', type=int, default=10, help='how many keys to show')
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
from matplotlib.ticker import FuncFormatter


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

# grab the top N keys for this hashtag, then order them low -> high for the plot
counter = Counter(counts[args.key])
top = counter.most_common(args.top)      # highest first
top = list(reversed(top))                # now lowest first (low -> high)

labels = [k for k, v in top]
values = [v for k, v in top]

# is this the language file or the country file?  used for titles/labels
dimension = 'language' if args.input_path.endswith('.lang') else 'country'

# build the title, then make sure a font exists that can actually draw it
title = args.title or f'{args.key} by {dimension} in 2020 (top {len(labels)})'

chosen = font_supporting(title)
if chosen:
    # keep DejaVu Sans for Latin text/numbers; only the CJK font is a fallback
    plt.rcParams['font.family'] = ['DejaVu Sans', chosen]
elif any(ord(ch) > 0x024F for ch in title):
    # No installed font covers these characters; they would silently render
    # as empty boxes.  Say so clearly and fall back to an ASCII title.
    ascii_key = args.key.encode('unicode_escape').decode('ascii')
    print(f'WARNING: no installed font can render {args.key!r}; the title '
          f'would appear as empty boxes.\n'
          f'         Install a CJK font, or rerun with '
          f'--title "{ascii_key} by {dimension}".', file=sys.stderr)
    title = f'{ascii_key} by {dimension} in 2020 (top {len(labels)})'

# build the bar graph
fig, ax = plt.subplots(figsize=(11, 6))
bars = ax.bar(range(len(values)), values, color='#2b7bba', zorder=3)

ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=45, ha='right')
ax.set_xlabel(f'{dimension} code')
ax.set_ylabel('number of tweets')
ax.set_title(title, fontsize=14, pad=14)

# thousands separators, light horizontal grid, no top/right box lines
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x):,}'))
ax.grid(axis='y', color='#dddddd', zorder=0)
ax.set_axisbelow(True)
for side in ('top', 'right'):
    ax.spines[side].set_visible(False)

# exact count printed above each bar
for bar, v in zip(bars, values):
    ax.annotate(f'{v:,}',
                xy=(bar.get_x() + bar.get_width() / 2, v),
                xytext=(0, 3), textcoords='offset points',
                ha='center', va='bottom', fontsize=9)
if values:
    ax.set_ylim(0, max(values) * 1.10)   # leave room for the labels

fig.tight_layout()

# decide where to save
if args.output_path:
    output_path = args.output_path
else:
    safe_key = args.key.replace('#', '').replace('/', '_')
    output_path = f'{args.input_path}.{safe_key}.png'

os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
fig.savefig(output_path, dpi=150)
print('wrote', output_path)
