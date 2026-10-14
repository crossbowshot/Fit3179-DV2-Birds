"""
Build every Melbourne chart data file from the raw downloads in ../raw_data.

Inputs (outside the repo, see CLAUDE.md):
  ../raw_data/ala_<year>_birds_vic/*.csv          ALA occurrence download, Victoria, one calendar year
  ../raw_data/abs_g01_vic/G01_VIC_GDA2020.gpkg    ABS 2021 Census G01: suburb (SAL) boundaries, population,
                                                  Greater Melbourne (GCCSA 2GMEL) boundary
Run from the project root:
  .venv/bin/python processing_scripts/build_data.py --year 2024
  .venv/bin/python processing_scripts/build_data.py --year 2024 --skip-join   # reuse the cached record table
Options --ala and --out override the input CSV and output folder (default data/).

Steps
  1. Greater Melbourne suburbs: every Victorian SAL whose representative point lies inside 2GMEL.
  2. Join every bird record to the suburb it falls in (point in polygon). Anonymise observers.
     The joined table is cached in ../raw_data/work_<year>/ so chart files can be rebuilt quickly.
  3. Write one small CSV per chart (+ the suburb GeoJSON) to data/.
State-level data comes from processing_scripts/fetch_state_data.py instead (ALA + ABS APIs).
"""
import argparse, glob, json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import mapping, MultiPolygon, Polygon
from shapely.geometry.polygon import orient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.normpath(os.path.join(ROOT, '..', 'raw_data'))
GPKG = os.path.join(RAW, 'abs_g01_vic', 'G01_VIC_GDA2020.gpkg')
COLS = ['dataResourceName', 'recordedBy', 'eventDate', 'eventTime', 'decimalLatitude', 'decimalLongitude',
        'species', 'vernacularName', 'taxonRank', 'individualCount']
INAT = 'iNaturalist Australia'

# Introduced (non-native) species, by binomial so subspecies names don't matter
INTRODUCED = {'Acridotheres tristis', 'Spilopelia chinensis', 'Streptopelia chinensis', 'Turdus merula',
              'Sturnus vulgaris', 'Passer domesticus', 'Passer montanus', 'Columba livia', 'Carduelis carduelis',
              'Chloris chloris', 'Turdus philomelos', 'Anas platyrhynchos', 'Cygnus olor', 'Pycnonotus jocosus',
              'Phasianus colchicus', 'Alauda arvensis'}
# ALA names that differ from the names Australians use
RENAME = {'Spotted Turtle-dove': 'Spotted Dove', 'Eurasian Blackbird': 'Common Blackbird'}
SQUEEZE_FROM = 30   # slope chart: ranks below this are squeezed in at the bottom so the chart stays readable


def log(*a):
    print(*a, flush=True)


# ---------- 1. suburbs ----------
def load_suburbs():
    sal = gpd.read_file(GPKG, layer='G01_SAL_2021_VIC', columns=['SAL_CODE_2021', 'SAL_NAME_2021', 'Tot_P_P'])
    gmel = gpd.read_file(GPKG, layer='G01_GCCSA_2021_VIC').query("GCCSA_CODE_2021 == '2GMEL'")
    # GDA2020 and the WGS84 coordinates used by ALA differ by under 2 m: treat them as the same
    sal = sal.set_crs(4326, allow_override=True)
    gmel = gmel.set_crs(4326, allow_override=True)
    sal = sal[sal.geometry.notna() & ~sal.geometry.is_empty]
    melb = sal[sal.representative_point().within(gmel.geometry.iloc[0])].copy()
    melb = melb.rename(columns={'SAL_CODE_2021': 'sal_code', 'Tot_P_P': 'population_2021'})
    melb['suburb'] = melb.SAL_NAME_2021.str.replace(r' \(Vic\.\)$', '', regex=True)
    log('Greater Melbourne suburbs:', len(melb), ' residents (2021):', int(melb.population_2021.sum()))
    return melb[['sal_code', 'suburb', 'population_2021', 'geometry']].reset_index(drop=True)


# ---------- 2. join records to suburbs ----------
class Anonymiser:
    """Replaces observer names with obs00001, obs00002, ... Names never leave this script."""
    def __init__(self):
        self.ids = {}

    def __call__(self, name):
        if pd.isna(name) or name.startswith('<a ') or name.strip().lower() in ('unknown', 'birds australia'):
            return np.nan
        if name not in self.ids:
            self.ids[name] = f'obs{len(self.ids) + 1:05d}'
        return self.ids[name]


def join_records(ala_csv, melb):
    header = pd.read_csv(ala_csv, nrows=0).columns
    missing = [c for c in COLS if c not in header]
    if missing:
        sys.exit(f'ALA file is missing columns: {missing}')
    xmin, ymin, xmax, ymax = melb.total_bounds
    anon = Anonymiser()
    names, parts, n_vic = [], [], 0
    for ch in pd.read_csv(ala_csv, usecols=COLS, dtype=str, chunksize=300_000):
        n_vic += len(ch)
        # species -> vernacular name pairs from all of Victoria (used to name each species)
        sp = ch[ch.taxonRank == 'species']
        names.append(sp.groupby(['species', 'vernacularName']).size())
        lon, lat = pd.to_numeric(ch.decimalLongitude), pd.to_numeric(ch.decimalLatitude)
        ch = ch[lon.between(xmin, xmax) & lat.between(ymin, ymax)]
        pts = gpd.GeoDataFrame(ch, geometry=gpd.points_from_xy(pd.to_numeric(ch.decimalLongitude),
                                                                 pd.to_numeric(ch.decimalLatitude)), crs=4326)
        j = gpd.sjoin(pts, melb[['sal_code', 'geometry']], how='inner', predicate='within')
        j = j[~j.index.duplicated(keep='first')]   # point exactly on a shared border: keep one suburb
        j['observer_id'] = [anon(x) for x in j.recordedBy]
        parts.append(pd.DataFrame(j[['dataResourceName', 'observer_id', 'eventDate', 'eventTime', 'species',
                                     'individualCount', 'sal_code']]))
        log(f'  read {n_vic:,} Victorian records, {sum(map(len, parts)):,} in Greater Melbourne')
    d = pd.concat(parts, ignore_index=True).rename(columns={'dataResourceName': 'source'})
    d['date'] = d.eventDate.str[:10]
    d['individualCount'] = pd.to_numeric(d.individualCount, errors='coerce')
    d = d.drop(columns='eventDate')
    pairs = pd.concat(names).groupby(level=[0, 1]).sum().sort_values(ascending=False).reset_index()
    common = pairs.drop_duplicates('species').set_index('species')['vernacularName'].replace(RENAME)
    log(f'Victoria: {n_vic:,} records; Greater Melbourne: {len(d):,}; observers anonymised: {len(anon.ids):,}')
    return d, common


# ---------- 3. chart files ----------
def write_suburbs(d, melb, out, year):
    counts = d.sal_code.value_counts()
    s = melb.drop(columns='geometry').copy()
    s['bird_records'] = s.sal_code.map(counts).fillna(0).astype(int)
    s['records_per_1000_residents'] = np.where(s.population_2021 > 0,
                                               (s.bird_records / s.population_2021.where(s.population_2021 > 0) * 1000).round(1),
                                               np.nan)
    s[['sal_code', 'suburb', 'bird_records', 'population_2021', 'records_per_1000_residents']].to_csv(
        f'{out}/melb_suburb_bird_records_{year}.csv', index=False)
    # proportional symbol map: one point per suburb with at least one record, biggest first
    p = melb.copy()
    rp = p.geometry.representative_point()
    p['lon'], p['lat'] = rp.x.round(4), rp.y.round(4)
    p['bird_records'] = s.bird_records
    p = p[p.bird_records > 0].sort_values('bird_records', ascending=False)
    p[['sal_code', 'suburb', 'lon', 'lat', 'bird_records', 'population_2021']].to_csv(
        f'{out}/melb_suburb_points_{year}.csv', index=False)
    rate = s[s.population_2021 >= 1000].records_per_1000_residents
    log(f'suburbs: {len(s)}, records {s.bird_records.sum():,}, under 1,000 residents {int((s.population_2021 < 1000).sum())},'
        f' median rate {rate.median():.0f}')
    log('  highest rates (1,000+ residents):',
        s[s.population_2021 >= 1000].nlargest(5, 'records_per_1000_residents')[['suburb', 'records_per_1000_residents']].values.tolist())
    log('  most records:', s.nlargest(5, 'bird_records')[['suburb', 'bird_records', 'population_2021']].values.tolist())


def write_geojson(melb, out):
    """Simplified suburb outlines. d3 (used by Vega) wants clockwise outer rings, the opposite of the GeoJSON
    standard, otherwise each suburb is drawn 'inside out' as a shape covering the whole globe."""
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 4), round(c[1], 4)]
    feats = []
    for row in melb.itertuples():
        g = row.geometry.simplify(0.0004, preserve_topology=True)
        polys = list(g.geoms) if isinstance(g, MultiPolygon) else [g]
        g = MultiPolygon([orient(p, sign=-1.0) for p in polys if isinstance(p, Polygon) and not p.is_empty])
        geom = mapping(g)
        feats.append({'type': 'Feature', 'properties': {'sal_code': row.sal_code, 'suburb': row.suburb},
                      'geometry': {'type': 'MultiPolygon', 'coordinates': rnd(json.loads(json.dumps(geom['coordinates'])))}})
    with open(f'{out}/melb_suburbs.geojson', 'w') as f:
        json.dump({'type': 'FeatureCollection', 'features': feats}, f, separators=(',', ':'))


def species_table(d):
    t = d.dropna(subset=['name'])
    g = t.groupby('name').agg(records=('name', 'size'), birds=('individualCount', 'sum'), species=('species', 'first'))
    g['birds'] = g.birds.astype(int)
    g['rank_records'] = g.records.rank(ascending=False, method='first').astype(int)
    g['rank_birds'] = g.birds.rank(ascending=False, method='first').astype(int)
    return g


def write_species(d, sp, out, year):
    n = len(d)
    t = sp.sort_values('records', ascending=False).head(15).reset_index()
    t.insert(0, 'rank', range(1, 16))
    t['share_pct'] = (t.records / n * 100).round(1)
    t['status'] = np.where(t.species.isin(INTRODUCED), 'Introduced', 'Native')
    t = t.rename(columns={'name': 'species', 'species': 'binomial', 'birds': 'birds_counted'})
    t[['rank', 'species', 'records', 'birds_counted', 'share_pct', 'status']].to_csv(
        f'{out}/melb_top15_species_{year}.csv', index=False)
    log(f'top 15 species (share of all {n:,} records):')
    log(t[['rank', 'species', 'records', 'share_pct', 'status']].to_string(index=False))

    # slope chart: any species in the top 8 by records or by birds counted
    e = sp[(sp.rank_records <= 8) | (sp.rank_birds <= 8)].reset_index().rename(columns={'name': 'species', 'species': 'binomial'})
    for side in ('records', 'birds'):
        y = e[f'rank_{side}'].astype(float)
        deep = e[f'rank_{side}'] > SQUEEZE_FROM
        order = e.loc[deep, f'rank_{side}'].rank(method='first')
        y[deep] = SQUEEZE_FROM + 2 * order
        e[f'y_{side}'] = y
    e['change'] = np.select([e.rank_records < e.rank_birds, e.rank_records > e.rank_birds],
                            ['Ranks higher by number of records', 'Ranks higher by number of birds counted'],
                            'Same rank both ways')
    e = e.sort_values('rank_records')
    e[['species', 'records', 'birds', 'rank_records', 'rank_birds', 'y_records', 'y_birds', 'change']].to_csv(
        f'{out}/melb_records_vs_birds_rank_{year}.csv', index=False)
    log('slope chart rows:')
    log(e[['species', 'records', 'birds', 'rank_records', 'rank_birds', 'y_records', 'y_birds']].to_string(index=False))


def write_inat(d, out, year):
    i = d[d.source == INAT]
    # heatmap: weekday x hour (local time); every cell present, including zeros
    h = i.dropna(subset=['eventTime', 'date']).copy()
    h = h[h.eventTime.str.match(r'^\d{2}:')]
    h['hour'] = h.eventTime.str[:2].astype(int)
    h['weekday_num'] = pd.to_datetime(h.date).dt.dayofweek
    grid = pd.MultiIndex.from_product([range(7), range(24)], names=['weekday_num', 'hour'])
    a = h.groupby(['weekday_num', 'hour']).size().reindex(grid, fill_value=0).rename('records').reset_index()
    a.insert(1, 'weekday', a.weekday_num.map(dict(enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']))))
    a.to_csv(f'{out}/inat_weekday_hour_{year}.csv', index=False)
    by_day = a.groupby('weekday', sort=False).records.sum()
    log(f'iNaturalist: {len(i):,} records, {len(h):,} with a time; by weekday {by_day.to_dict()}')
    top = a.nlargest(3, 'records')[['weekday', 'hour', 'records']].values.tolist()
    log(f'  busiest cells {top}, median cell {a.records.median():.0f}')

    # jitter: records per observer
    b = i.groupby('observer_id').size().rename('records').sort_values(ascending=False).reset_index()
    b.to_csv(f'{out}/inat_observer_records_{year}.csv', index=False)
    n, tot = len(b), b.records.sum()
    log(f'  observers {n:,}; top observer {b.records.iloc[0]:,} ({b.records.iloc[0] / tot * 100:.1f}%);'
        f' top 1% ({max(1, n // 100)} people) {b.records.head(max(1, n // 100)).sum() / tot * 100:.1f}%;'
        f' top 10% {b.records.head(n // 10).sum() / tot * 100:.1f}%; one-record observers {(b.records == 1).sum():,};'
        f' records without an observer {i.observer_id.isna().sum():,}')


def write_months(d, sp, out, year):
    m = d.copy()
    m['month'] = pd.to_numeric(m.date.str[5:7], errors='coerce')
    m['src'] = m.source.map({'eBird Australia': 'eBird', 'BirdLife Australia, Birdata': 'BirdLife Australia',
                             INAT: 'iNaturalist'}).fillna('Other')
    s = m.groupby(['month', 'src']).size().rename('records').reset_index().rename(columns={'src': 'source'})
    s.to_csv(f'{out}/melb_source_month_{year}.csv', index=False)
    log('records by source and month:'); log(s.pivot(index='source', columns='month', values='records').to_string())
    # bump chart: monthly rank of the 10 most reported species of the year, ranked against each other (rank, 1-10)
    # and against every species reported that month (rank_all, shown in the tooltip)
    t = m.dropna(subset=['name'])
    r = t.groupby(['month', 'name']).size().rename('records').reset_index()
    r['rank_all'] = r.groupby('month').records.rank(ascending=False, method='first').astype(int)
    top10 = sp.nsmallest(10, 'rank_records').index
    r = r[r.name.isin(top10)].rename(columns={'name': 'species'}).copy()
    r['rank'] = r.groupby('month').records.rank(ascending=False, method='first').astype(int)
    r = r[['month', 'species', 'records', 'rank', 'rank_all']].sort_values(['species', 'month'])
    r.to_csv(f'{out}/melb_species_month_rank_{year}.csv', index=False)
    log('monthly ranks of the top 10:'); log(r.pivot(index='species', columns='month', values='rank').to_string())


SEASON = {12: 'Summer', 1: 'Summer', 2: 'Summer', 3: 'Autumn', 4: 'Autumn', 5: 'Autumn',
          6: 'Winter', 7: 'Winter', 8: 'Winter', 9: 'Spring', 10: 'Spring', 11: 'Spring'}


def write_seasonal(d, out, year, per_season=3, min_records=500):
    """Ridgeline: birds that come and go. More people go birding in some months (October has ~1.8x July's records),
    so each bird is measured by its share of each month's records, not its raw count. Its 12 monthly shares are then
    scaled to add up to 100%: the profile shows when in the year the bird is reported. For each season, the
    per_season birds (with at least min_records) whose profile peaks highest in that season are kept."""
    m = d.copy()
    m['month'] = pd.to_numeric(m.date.str[5:7], errors='coerce')
    total = m.groupby('month').size()
    c = m.dropna(subset=['name']).groupby(['name', 'month']).size().unstack(fill_value=0).reindex(columns=range(1, 13), fill_value=0)
    c = c[c.sum(axis=1) >= min_records]
    rate = c.div(total, axis=1)
    profile = rate.div(rate.sum(axis=1), axis=0)
    peak_month, peak = profile.idxmax(axis=1), profile.max(axis=1)
    season = peak_month.map(SEASON)
    pick = peak.groupby(season).nlargest(per_season).index.get_level_values(-1)
    r = []
    for name in pick:
        for month in range(1, 13):
            r.append({'species': name, 'month': month, 'records': int(c.loc[name, month]),
                      'share_of_month_pct': round(rate.loc[name, month] * 100, 3),
                      'profile_pct': round(profile.loc[name, month] * 100, 1),
                      'peak_month': int(peak_month[name]), 'season': season[name]})
    t = pd.DataFrame(r).sort_values(['peak_month', 'species', 'month'])
    t.to_csv(f'{out}/melb_seasonal_species_{year}.csv', index=False)
    log(f'seasonal birds ({per_season} per season, {min_records}+ records, of {len(c)} eligible):')
    for name in t.species.unique():
        x = t[t.species == name]
        log(f'  {name:28} {x.season.iloc[0]:6} peak month {x.peak_month.iloc[0]:>2} ({x.profile_pct.max():.0f}% of its year),'
            f' months under 1%: {(x.profile_pct < 1).sum():>2}, records {x.records.sum():,}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--year', type=int, required=True)
    ap.add_argument('--ala', help='ALA occurrence CSV (default: the CSV in ../raw_data/ala_<year>_birds_vic/)')
    ap.add_argument('--out', default=os.path.join(ROOT, 'data'))
    ap.add_argument('--skip-join', action='store_true', help='reuse the cached joined records')
    a = ap.parse_args()
    work = os.path.join(RAW, f'work_{a.year}')
    os.makedirs(work, exist_ok=True)
    os.makedirs(a.out, exist_ok=True)
    cache = os.path.join(work, 'melb_records.pkl')

    melb = load_suburbs()
    if a.skip_join:
        d, common = pd.read_pickle(cache), pd.read_pickle(os.path.join(work, 'common_names.pkl'))
    else:
        ala = a.ala or next(iter(sorted(glob.glob(os.path.join(RAW, f'ala_{a.year}_birds_vic', '*.csv')))), None)
        if not ala:
            sys.exit(f'no ALA CSV found for {a.year}; pass --ala')
        log('reading', ala)
        d, common = join_records(ala, melb)
        d.to_pickle(cache)
        common.to_pickle(os.path.join(work, 'common_names.pkl'))
        common.rename('common_name').to_csv(os.path.join(work, 'species_common_names.csv'))

    years = pd.to_numeric(d.date.str[:4], errors='coerce').value_counts().to_dict()
    log('records by year (should be one year only):', years)
    log('records by source:', d.source.value_counts().to_dict())

    # one display name per species (records not identified to species level get none)
    d['name'] = d.species.map(common).fillna(d.species)

    write_suburbs(d, melb, a.out, a.year)
    write_geojson(melb, a.out)
    sp = species_table(d)
    write_species(d, sp, a.out, a.year)
    write_inat(d, a.out, a.year)
    write_months(d, sp, a.out, a.year)
    write_seasonal(d, a.out, a.year)
    log('wrote chart files to', a.out)


if __name__ == '__main__':
    main()
