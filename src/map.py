#!/usr/bin/env python3
'''
Map phase of the MapReduce pipeline.

Processes a single day's zip file of geotagged tweets and, for every hashtag
listed in the ./hashtags file, counts how many matching tweets were sent in
each language and in each country.

Matching is on whole hashtag tokens and is case-insensitive: a tweet counts
toward #coronavirus only if it contains "#coronavirus" as a complete hashtag
(in any capitalization), not merely as a substring.  So #corona is not
credited for #coronavirus tweets.

Two output files are written to the output folder:
    <inputname>.lang     JSON: { hashtag: { lang_code: count, ... }, ... }
    <inputname>.country  JSON: { hashtag: { country_code: count, ... }, ... }
'''

# command line args
import argparse
parser = argparse.ArgumentParser(description='map phase: count hashtag usage by language and country')
parser.add_argument('--input_path', required=True, help='path to a geoTwitterYY-MM-DD.zip file')
parser.add_argument('--output_folder', default='outputs', help='folder to write .lang/.country results into')
args = parser.parse_args()

# imports
import os
import re
import sys
import json
import zipfile
import datetime
from collections import Counter

# load the hashtags we are searching for
with open('hashtags', 'r', encoding='utf-8') as f:
    hashtags = [line.strip() for line in f if line.strip()]

# Hashtag tokenizer.  A hashtag token is '#' followed by word characters;
# \w is unicode-aware in python3, so this also handles non-Latin scripts
# such as #코로나바이러스.  Hyphens are included so that forms people actually
# type, like '#covid-19', can be recognized as written.
hashtag_re = re.compile(r'#[\w-]+', re.UNICODE)


def tokenize(text):
    '''
    Return the set of lowercased hashtag tokens in `text`.

    Hyphenated hashtags are recorded under BOTH readings, because the two are
    both legitimate:
      - '#covid-19' as literally written (the hashtags file lists this form), and
      - '#covid', which is what Twitter actually turns into a clickable link,
        since a hashtag link terminates at the hyphen.
    So the text '#covid-19' counts toward both '#covid-19' and '#covid'.
    '''
    tokens = set()
    for raw in hashtag_re.findall(text):
        token = raw.rstrip('-').lower()     # drop any trailing hyphens
        if len(token) <= 1:                 # a bare '#' is not a hashtag
            continue
        tokens.add(token)
        if '-' in token:
            head = token.split('-', 1)[0]   # the part Twitter actually links
            if len(head) > 1:
                tokens.add(head)
    return tokens

# Case-insensitive lookup: lowercased hashtag -> the original spelling(s)
# from the hashtags file.  A list is used so that if the file happens to
# contain two case variants of the same tag, both counters still get updated.
hashtag_lookup = {}
for hashtag in hashtags:
    hashtag_lookup.setdefault(hashtag.lower(), []).append(hashtag)

# Sanity check: warn about any hashtag in the file that the tokenizer could
# never produce, since such an entry would silently count zero all year.
for hashtag in hashtags:
    if hashtag.lower() not in tokenize(hashtag):
        print(f'WARNING: {hashtag!r} can never match and will count zero',
              file=sys.stderr)

# initialize the counters
# each maps: hashtag -> Counter of {lang/country -> number of tweets}
counter_lang = {hashtag: Counter() for hashtag in hashtags}
counter_country = {hashtag: Counter() for hashtag in hashtags}

# open the zip file for the day; it contains 24 inner files (one per hour)
with zipfile.ZipFile(args.input_path) as archive:
    for i, filename in enumerate(archive.namelist()):
        print(datetime.datetime.now(), args.input_path,
              f'i={i} of {len(archive.namelist())}', filename)

        with archive.open(filename) as f:
            for line in f:
                # a malformed line should not crash the whole day's run
                try:
                    tweet = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue

                # the tweet text; skip tweets without it
                text = tweet.get('text')
                if not text:
                    continue

                # language of the tweet ('und' = undetermined when absent)
                lang = tweet.get('lang', 'und')

                # country code lives at tweet['place']['country_code'].
                # place may be missing/None, and country_code may be absent
                # (e.g. tweets from international waters or the ISS).
                country = None
                place = tweet.get('place')
                if isinstance(place, dict):
                    country = place.get('country_code')
                if not country:
                    country = 'none'

                # search hashtags
                #
                # Match whole hashtag tokens, case-insensitively.  We extract
                # every "#..." token from the tweet, lowercase them, and only
                # count a hashtag when it appears as its own complete token.
                # This means #corona does NOT get credit for a #coronavirus
                # tweet, and #COVID19 still matches "#covid19" / "#Covid19".
                if '#' not in text:
                    continue

                tokens = tokenize(text)
                for token in tokens:
                    for hashtag in hashtag_lookup.get(token, ()):
                        counter_lang[hashtag][lang] += 1
                        counter_country[hashtag][country] += 1

# make sure the output folder exists
os.makedirs(args.output_folder, exist_ok=True)

# write the two output files, named after the input file
base = os.path.basename(args.input_path)
lang_path = os.path.join(args.output_folder, base + '.lang')
country_path = os.path.join(args.output_folder, base + '.country')

with open(lang_path, 'w', encoding='utf-8') as f:
    json.dump(counter_lang, f, ensure_ascii=False)

with open(country_path, 'w', encoding='utf-8') as f:
    json.dump(counter_country, f, ensure_ascii=False)

print('wrote', lang_path)
print('wrote', country_path)
