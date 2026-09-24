#!/bin/sh
# Task 1: run the mapper over every day of 2020.
#
# Each map.py call can take up to a day, so we launch them all in parallel:
#   nohup  -> keep running after you log out of the lambda server
#   &      -> background the process so the loop continues immediately
#
# Run it (itself backgrounded) with:
#   $ nohup sh run_maps.sh &
# (or ./run_maps.sh if the execute bit is set)
#
# The glob restricts input to 2020 tweets (geoTwitter20-*) rather than all years.

# Invoke via python3 explicitly rather than relying on the execute bit and
# shebang.  If a virtualenv is active, this picks up that interpreter.
for file in /data/Twitter\ dataset/geoTwitter20-*.zip; do
    echo "launching map.py on $file"
    nohup python3 ./src/map.py --input_path="$file" &
done

# wait so that a wrapping `nohup sh run_maps.sh &` stays alive until every
# backgrounded map.py has finished.
wait
echo "all map.py jobs launched"
