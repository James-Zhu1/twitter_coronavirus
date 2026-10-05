# Coronavirus Twitter Analysis (2020)

A MapReduce-style analysis of every geotagged tweet sent in 2020 — about 1.1 billion tweets across 366 daily archives — to track how coronavirus-related hashtags spread across languages, countries, and time.

## Approach

The dataset is far too large to load into memory, so the work is split into independent per-day jobs that run in parallel and are combined afterward.

| Step | File | What it does |
|---|---|---|
| **Map** | `src/map.py` | Reads one day of tweets. For each tweet matching a tracked hashtag, increments two nested counters: one keyed by language (`lang`) and one by country (`place.country_code`). Handles tweets with missing location data without failing. Writes a `.lang` and a `.country` file to `outputs/`. |
| **Run** | `run_maps.sh` | Launches one `map.py` process per day of 2020 with `nohup` and `&`, so all 366 jobs run concurrently and keep running after the SSH session closes. |
| **Reduce** | `src/reduce.py` | Element-wise sums the 366 daily counters into yearly totals: `reduced/reduced.lang` and `reduced/reduced.country`. |
| **Visualize** | `src/visualize.py` | Plots the top 10 languages or countries for a given hashtag as a sorted bar chart. |
| **Time series** | `src/alternative_reduce.py` | Takes any list of hashtags, scans the daily outputs directly, and plots tweets per day over the year, one line per hashtag. |

## Results

### `#coronavirus` — top languages and countries

![#coronavirus by language](plots/coronavirus_by_language.png)

![#coronavirus by country](plots/coronavirus_by_country.png)

### `#코로나바이러스` (Korean: "coronavirus") — top languages and countries

![#코로나바이러스 by language](plots/korean_coronavirus_by_language.png)

![#코로나바이러스 by country](plots/korean_coronavirus_by_country.png)

### Daily hashtag volume over 2020

Daily tweet counts for `#coronavirus`, `#covid19`, and `#corona`.

![Daily hashtag usage over 2020](plots/hashtag_usage_over_2020.png)

What the plot shows:

- **`#coronavirus`** has a small first bump around day 30 (late January, WHO global health emergency), then surges to ~15,000 tweets/day around day 72 — the week the WHO declared a pandemic (March 11).
- **`#covid19`** is essentially absent until day ~42, when the WHO named the disease. It overtakes `#coronavirus` by day ~80 and stays dominant for the rest of the year at 1,500–2,500 tweets/day, while `#coronavirus` fades to a few hundred.
- **`#corona`** peaks near 4,000 tweets/day around day 70 and declines steadily.
- A sharp one-day spike in `#covid19` near day 276 (early October) coincides with the announcement that the U.S. president had tested positive.

Matching is by substring, so a tweet tagged `#coronavirus` is also counted under `#corona`.

## Repository layout

```
src/            map.py, reduce.py, visualize.py, alternative_reduce.py
run_maps.sh     launches one map.py job per day of 2020 in parallel
hashtags        the hashtags tracked by the mapper
outputs/        per-day mapper output (.lang / .country), all 366 days
reduced/        yearly totals after the reduce step
plots/          all generated figures
```

## Reproducing the results

```sh
./run_maps.sh
./src/reduce.py --input_paths outputs/*.lang    --output_path reduced/reduced.lang
./src/reduce.py --input_paths outputs/*.country --output_path reduced/reduced.country
./src/visualize.py --input_path reduced/reduced.lang    --key '#coronavirus'
./src/visualize.py --input_path reduced/reduced.country --key '#coronavirus'
./src/visualize.py --input_path reduced/reduced.lang    --key '#코로나바이러스'
./src/visualize.py --input_path reduced/reduced.country --key '#코로나바이러스'
./src/alternative_reduce.py '#coronavirus' '#covid19' '#corona'
```
