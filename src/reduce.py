#!/usr/bin/env python3
'''
Reduce phase of the MapReduce pipeline.

Takes any number of map-output files (all .lang files, or all .country files)
and performs an element-wise addition of their nested counts, producing one
combined file.

Example:
    python3 src/reduce.py --input_paths outputs/geoTwitter20-*.lang    --output_path reduced.lang
    python3 src/reduce.py --input_paths outputs/geoTwitter20-*.country --output_path reduced.country
'''

# command line args
import argparse
parser = argparse.ArgumentParser(description='reduce phase: element-wise sum of map outputs')
parser.add_argument('--input_paths', nargs='+', required=True, help='list of .lang or .country files to combine')
parser.add_argument('--output_path', required=True, help='path for the combined output file')
args = parser.parse_args()

# imports
import json
from collections import Counter


def combine(total, partial):
    '''
    Add the nested dictionary `partial` into the nested dictionary `total`
    element-wise.  Both have the shape { hashtag: { key: count } }.
    Mutates and returns `total`.
    '''
    for hashtag, counts in partial.items():
        if hashtag not in total:
            total[hashtag] = Counter()
        total[hashtag].update(counts)
    return total


# accumulate all input files into a single nested dictionary
reduced = {}
for path in args.input_paths:
    with open(path, 'r', encoding='utf-8') as f:
        partial = json.load(f)
    reduced = combine(reduced, partial)

# Counter is not JSON serializable directly in older setups; cast to plain dict
serializable = {hashtag: dict(counts) for hashtag, counts in reduced.items()}

with open(args.output_path, 'w', encoding='utf-8') as f:
    json.dump(serializable, f, ensure_ascii=False)

print('wrote', args.output_path)
