"""
Bird records per 1,000 residents for every state and territory, for one calendar year.

Bird records: Atlas of Living Australia (ALA) API, same filters as the Victorian download
(birds, Australia, human observation, ALA General data profile), counted by state.
Population: ABS estimated resident population at 30 June of the same year (ABS Data API, dataflow ERP_Q).

Run from the project root:
    .venv/bin/python processing_scripts/fetch_state_data.py --year 2024
Writes data/state_bird_records_<year>.csv
"""
import argparse, csv, io, json, os, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATES = ['New South Wales', 'Victoria', 'Queensland', 'South Australia', 'Western Australia',
          'Tasmania', 'Northern Territory', 'Australian Capital Territory']


def get(url, accept=None):
    req = urllib.request.Request(url, headers={'Accept': accept} if accept else {})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode('utf-8')


def ala_records_by_state(year):
    fq = ['speciesGroup:"Birds"', 'country:"Australia"', 'basisOfRecord:"HUMAN_OBSERVATION"',
          f'eventDate:[{year}-01-01T00:00:00Z TO {year}-12-31T23:59:59Z]']
    params = [('q', '*:*')] + [('fq', f) for f in fq] + [
        ('qualityProfile', 'ALA'), ('pageSize', '0'), ('facets', 'stateProvince'), ('flimit', '50')]
    url = 'https://biocache-ws.ala.org.au/ws/occurrences/search?' + urllib.parse.urlencode(params)
    d = json.loads(get(url))
    return {x['label']: x['count'] for x in d['facetResults'][0]['fieldResult']}


def abs_population_june(year):
    # ERP_Q has one row per measure x sex x age x region; keep ERP (measure 1), persons (sex 3), all ages
    url = f'https://data.api.abs.gov.au/rest/data/ABS,ERP_Q,1.0.0/all?startPeriod={year}-Q2&endPeriod={year}-Q2'
    rows = csv.DictReader(io.StringIO(get(url, 'application/vnd.sdmx.data+csv;labels=both')))
    pop = {}
    for r in rows:
        if (r['MEASURE: Measure'].startswith('1:') and r['SEX: Sex'].startswith('3:')
                and r['AGE: Age'].split(':')[0] == 'TOT'):
            pop[r['REGION: Region'].split(': ', 1)[1]] = int(float(r['OBS_VALUE']))
    return pop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--year', type=int, required=True)
    year = ap.parse_args().year
    records, pop = ala_records_by_state(year), abs_population_june(year)
    missing = [s for s in STATES if s not in records or s not in pop]
    if missing:
        raise SystemExit(f'missing states: {missing}')
    rows = [{'state': s, 'bird_records': records[s], 'population': pop[s],
             'records_per_1000_residents': round(records[s] / pop[s] * 1000, 1)} for s in STATES]
    rows.sort(key=lambda r: -r['records_per_1000_residents'])
    out = os.path.join(ROOT, 'data', f'state_bird_records_{year}.csv')
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"{r['state']:30} {r['bird_records']:>10,} {r['population']:>11,} {r['records_per_1000_residents']:>8}")
    print('wrote', out)


if __name__ == '__main__':
    main()
