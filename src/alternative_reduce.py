#!/usr/bin/env python3
'''
Alternative reduce (Task 4).

Scans every per-day .lang file in the outputs folder and, for each hashtag
given on the command line, plots how its total usage changed over the year.

    python3 src/alternative_reduce.py --hashtags '#coronavirus' '#corona' '#COVID19'

Produces a line plot where:
    - there is one line per input hashtag,
    - the x-axis is the day of the year (1-366),
    - the y-axis is the number of tweets using that hashtag that day.

The per-day totals are obtained by summing a hashtag's counts across all
languages within a single day's .lang file.  (Any per-day file works since the
totals match across .lang and .country; .lang is used by default.)
'''

# command line args
import argparse
parser = argparse.ArgumentParser(description='alternative reduce: hashtag usage over the year')
parser.add_argument('--hashtags', nargs='+', required=True, help='hashtags to plot')
parser.add_argument('--input_folder', default='outputs', help='folder of per-day map outputs')
parser.add_argument('--suffix', default='.lang', choices=['.lang', '.country'],
                    help='which per-day files to sum over (default .lang)')
parser.add_argument('--output_path', default='alternative_reduce.png')
args = parser.parse_args()

# imports
import os
import json
import glob
import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Prefer a CJK-capable font for hashtags like #코로나바이러스; fall back silently.
for _f in ['Noto Sans CJK JP', 'Noto Sans CJK KR', 'Noto Sans CJK',
           'NanumGothic', 'AppleGothic', 'Arial Unicode MS']:
    if any(_f == f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams['font.family'] = _f
        break


def day_of_year(filename):
    '''
    Extract the day-of-year (1-366) from a filename like
    "geoTwitter20-03-14.lang".  Returns None if it can't be parsed.
    '''
    base = os.path.basename(filename)
    # strip a leading prefix and the suffix to isolate YY-MM-DD
    # expected shape: geoTwitterYY-MM-DD<suffix>
    try:
        stamp = base.replace('geoTwitter', '').split('.')[0]  # e.g. "20-03-14"
        yy, mm, dd = stamp.split('-')
        date = datetime.date(2000 + int(yy), int(mm), int(dd))
        return date.timetuple().tm_yday
    except (ValueError, IndexError):
        return None


# data[hashtag] = { day_of_year: total_count }
data = {hashtag: {} for hashtag in args.hashtags}

pattern = os.path.join(args.input_folder, 'geoTwitter*' + args.suffix)
paths = sorted(glob.glob(pattern))
if not paths:
    raise SystemExit(f'no files matched {pattern}')

for path in paths:
    doy = day_of_year(path)
    if doy is None:
        continue
    with open(path, 'r', encoding='utf-8') as f:
        counts = json.load(f)
    for hashtag in args.hashtags:
        # sum this hashtag's counts across every language/country for the day
        total = sum(counts.get(hashtag, {}).values())
        data[hashtag][doy] = data[hashtag].get(doy, 0) + total

# plot one line per hashtag
plt.figure(figsize=(12, 6))
for hashtag in args.hashtags:
    days = sorted(data[hashtag].keys())
    values = [data[hashtag][d] for d in days]
    plt.plot(days, values, label=hashtag, linewidth=1.5)

plt.xlabel('day of the year')
plt.ylabel('number of tweets')
plt.title('Hashtag usage over 2020')
plt.legend()
plt.tight_layout()
plt.savefig(args.output_path, dpi=150)
print('wrote', args.output_path)
