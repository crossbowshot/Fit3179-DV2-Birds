"""
City of Melbourne side story: tree canopy (2021) and iNaturalist bird records (one calendar year).

Only iNaturalist records are used: their locations are accurate to about 10 m, while eBird pins records to shared
hotspot points (often +-1 km), which says nothing about whether a bird was under a tree.

Inputs (outside the repo, see CLAUDE.md):
  ../raw_data/com_canopy_2021/canopy_2021_{west,east}.zip   City of Melbourne Tree Canopies 2021, downloaded in two
                                                            halves because the shapefile export stops at 50,000 shapes
  ../raw_data/abs_g01_vic/G01_VIC_GDA2020.gpkg              City of Melbourne boundary (LGA24600) and suburbs (SAL)
  ../raw_data/ala_<year>_birds_vic/*.csv                    ALA download
  ../raw_data/work_<year>/species_common_names.csv          written by build_data.py
Run from the project root:
  .venv/bin/python processing_scripts/build_canopy.py --year 2024
Writes to data/:
  com_canopy_grid_2021.csv              tree cover (%) of every ~55 m grid cell that has trees (bin map layer)
  com_outline.geojson                   City of Melbourne suburbs, clipped to the City boundary
  com_inat_points_<year>.csv            one row per iNaturalist bird record inside the City (dot map layer)
  com_suburb_canopy_records_<year>.csv  each suburb's share of the City's canopy and of its records (dot plot)
"""
import argparse, glob, json, os
import numpy as np, pandas as pd, geopandas as gpd, shapely
from shapely.geometry import mapping
from shapely.geometry.polygon import orient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.normpath(os.path.join(ROOT, '..', 'raw_data'))
GPKG = os.path.join(RAW, 'abs_g01_vic', 'G01_VIC_GDA2020.gpkg')
METRIC = 7855            # GDA2020 / MGA zone 55: metres, for areas and the grid
MAX_UNCERTAINTY = 100    # drop records whose location is blurred by more than this (m), e.g. hidden threatened species
MIN_PART_KM2 = 0.05      # drop slivers where a suburb boundary only just crosses the City boundary


def log(*a):
    print(*a, flush=True)


def polygons(g):
    """Only the area parts of a geometry. Cutting a suburb at the City boundary can also leave stray lines and points
    where the two boundaries touch; those can't be drawn as areas."""
    return [p for p in shapely.get_parts(g) if p.geom_type == 'Polygon' and not p.is_empty]


def load_canopy():
    parts = [gpd.read_file(os.path.join(RAW, 'com_canopy_2021', f'canopy_2021_{h}.zip')) for h in ('west', 'east')]
    c = pd.concat(parts, ignore_index=True)
    log(f'canopy shapes: {len(c):,} (should be 57,980)')
    c = c.to_crs(METRIC)
    c['geometry'] = c.geometry.make_valid()
    return gpd.GeoDataFrame(geometry=gpd.GeoSeries([shapely.union_all(c.geometry.values)], crs=METRIC)
                            .explode(index_parts=False).values, crs=METRIC)


def load_city():
    lga = gpd.read_file(GPKG, layer='G01_LGA_2021_VIC').set_crs(4326, allow_override=True)
    city = lga[lga.LGA_CODE_2021 == 'LGA24600'].to_crs(METRIC).geometry.iloc[0]
    sal = gpd.read_file(GPKG, layer='G01_SAL_2021_VIC', columns=['SAL_CODE_2021', 'SAL_NAME_2021']).set_crs(4326, allow_override=True)
    sal = sal.to_crs(METRIC)
    sal['geometry'] = [shapely.MultiPolygon(polygons(g)) for g in sal.geometry.intersection(city)]
    sal = sal[sal.area >= MIN_PART_KM2 * 1e6].copy()
    sal['suburb'] = sal.SAL_NAME_2021.str.replace(r' \(Vic\.\)$', '', regex=True)
    log(f'City of Melbourne: {city.area / 1e6:.2f} km2, {len(sal)} suburb parts:', ', '.join(sal.suburb))
    return city, sal[['SAL_CODE_2021', 'suburb', 'geometry']].rename(columns={'SAL_CODE_2021': 'sal_code'})


def write_grid(canopy, city, dlon, dlat, out):
    """Bin map layer: a grid of cells dlon x dlat degrees (0.0006 x 0.0005 is about 53 m x 56 m here).
    The CSV holds each cell's south-west corner and tree cover; the spec adds dlon/dlat to draw the cell.
    Cells with no trees are left out (the map's background shows through)."""
    xmin, ymin, xmax, ymax = gpd.GeoSeries([city], crs=METRIC).to_crs(4326).total_bounds
    x0, y0 = np.floor(xmin / dlon) * dlon, np.floor(ymin / dlat) * dlat
    xs = np.round(x0 + dlon * np.arange(int(np.ceil((xmax - x0) / dlon))), 4)
    ys = np.round(y0 + dlat * np.arange(int(np.ceil((ymax - y0) / dlat))), 4)
    gx, gy = (a.ravel() for a in np.meshgrid(xs, ys))
    grid = gpd.GeoDataFrame({'lon': gx, 'lat': gy}, geometry=shapely.box(gx, gy, gx + dlon, gy + dlat), crs=4326)
    grid = grid.to_crs(METRIC)
    grid['cell_area'] = grid.area
    grid['land'] = grid.geometry.intersection(city).area
    grid = grid[grid.land >= 0.5 * grid.cell_area].reset_index(drop=True)   # keep cells at least half inside the City
    grid['cell'] = grid.index
    pieces = gpd.overlay(grid[['cell', 'geometry']], canopy, how='intersection', keep_geom_type=True)
    tree = pieces.assign(a=pieces.area).groupby('cell').a.sum()
    grid['tree_pct'] = (grid.cell.map(tree).fillna(0) / grid.land * 100).clip(upper=100).round(0).astype(int)
    log(f'grid {dlon} x {dlat} deg (~{grid.cell_area.mean() ** 0.5:.0f} m): {len(grid):,} cells in the City;'
        f' by tree cover {pd.cut(grid.tree_pct, [-1, 0, 10, 25, 50, 100]).value_counts().sort_index().to_dict()}')
    path = f'{out}/com_canopy_grid_2021.csv'
    grid.loc[grid.tree_pct > 0, ['lon', 'lat', 'tree_pct']].to_csv(path, index=False)
    log(f'  wrote {path} ({os.path.getsize(path) / 1e3:.0f} KB, {(grid.tree_pct > 0).sum():,} cells with trees)')


def write_outline(sal, out):
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 4), round(c[1], 4)]
    feats = []
    for row in sal.to_crs(4326).itertuples():
        polys = [orient(p, sign=-1.0) for p in polygons(row.geometry.simplify(0.0001, preserve_topology=True))]  # clockwise for d3
        geom = json.loads(json.dumps(mapping(shapely.MultiPolygon(polys))))
        label = row.geometry.representative_point()   # a point inside the suburb, for its name label
        feats.append({'type': 'Feature', 'properties': {'sal_code': row.sal_code, 'suburb': row.suburb,
                                                        'label_lon': round(label.x, 4), 'label_lat': round(label.y, 4)},
                      'geometry': {'type': 'MultiPolygon', 'coordinates': rnd(geom['coordinates'])}})
    path = f'{out}/com_outline.geojson'
    with open(path, 'w') as f:
        json.dump({'type': 'FeatureCollection', 'features': feats}, f, separators=(',', ':'))
    log(f'  wrote {path} ({os.path.getsize(path) / 1e3:.0f} KB)')


def load_inat(year, city):
    ala = sorted(glob.glob(os.path.join(RAW, f'ala_{year}_birds_vic', '*.csv')))[0]
    cols = ['dataResourceName', 'eventDate', 'decimalLatitude', 'decimalLongitude', 'coordinateUncertaintyInMeters', 'species']
    box = gpd.GeoSeries([city], crs=METRIC).to_crs(4326).total_bounds
    parts = []
    for ch in pd.read_csv(ala, usecols=cols, dtype={'eventDate': str, 'species': str}, chunksize=500_000):
        ch = ch[(ch.dataResourceName == 'iNaturalist Australia') & ch.decimalLongitude.between(box[0], box[2])
                & ch.decimalLatitude.between(box[1], box[3])]
        parts.append(ch)
    d = pd.concat(parts)
    p = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.decimalLongitude, d.decimalLatitude), crs=4326).to_crs(METRIC)
    p = p[p.within(city)].copy()
    blurred = p.coordinateUncertaintyInMeters > MAX_UNCERTAINTY
    log(f'iNaturalist records in the City: {len(p):,}; dropped {blurred.sum():,} with location blurred by over'
        f' {MAX_UNCERTAINTY} m; unknown accuracy {p.coordinateUncertaintyInMeters.isna().sum():,} (kept)')
    return p[~blurred]


def write_points(p, canopy, sal, year, out):
    names = pd.read_csv(os.path.join(RAW, f'work_{year}', 'species_common_names.csv'), index_col=0).common_name
    p = p.copy()
    p['bird'] = p.species.map(names).fillna(p.species).fillna('Bird (species not identified)')
    p['date'] = p.eventDate.str[:10]
    under = gpd.sjoin(p[['geometry']], canopy, predicate='within', how='inner').index
    p['under_trees'] = p.index.isin(under).astype(int)   # 1 = the record's location is inside a tree canopy outline
    s = gpd.sjoin(p[['geometry']], sal[['suburb', 'geometry']], predicate='within', how='left')
    p['suburb'] = s[~s.index.duplicated()].suburb
    ll = p.to_crs(4326).geometry
    df = pd.DataFrame({'lon': ll.x.round(5), 'lat': ll.y.round(5), 'bird': p.bird, 'date': p.date,
                       'under_trees': p.under_trees})
    path = f'{out}/com_inat_points_{year}.csv'
    df.to_csv(path, index=False)
    log(f'  wrote {path} ({os.path.getsize(path) / 1e3:.0f} KB): {len(df):,} records;'
        f' under a tree canopy {p.index.isin(under).mean() * 100:.1f}%')
    return p


def write_suburbs(p, canopy, sal, city, year, out):
    tree = gpd.overlay(sal, canopy, how='intersection', keep_geom_type=True)
    t = tree.assign(a=tree.area).groupby('suburb').a.sum()
    s = sal.drop(columns='geometry').copy()
    s['area_km2'] = sal.area.values / 1e6
    s['tree_km2'] = s.suburb.map(t).fillna(0).values / 1e6
    s['records'] = s.suburb.map(p.suburb.value_counts()).fillna(0).astype(int)
    s['tree_cover_pct'] = (s.tree_km2 / s.area_km2 * 100).round(1)
    s['share_of_trees_pct'] = (s.tree_km2 / s.tree_km2.sum() * 100).round(1)
    s['share_of_records_pct'] = (s.records / s.records.sum() * 100).round(1)
    s['share_of_land_pct'] = (s.area_km2 / s.area_km2.sum() * 100).round(1)
    s = s.sort_values('share_of_trees_pct', ascending=False)
    s['area_km2'], s['tree_km2'] = s.area_km2.round(2), s.tree_km2.round(3)
    path = f'{out}/com_suburb_canopy_records_{year}.csv'
    s.to_csv(path, index=False)
    log(f'  wrote {path}'); log(s.drop(columns='sal_code').to_string(index=False))
    log(f'City tree cover {s.tree_km2.sum() / (city.area / 1e6) * 100:.1f}%; records outside any listed suburb part:'
        f' {p.suburb.isna().sum()}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--year', type=int, required=True)
    ap.add_argument('--cell-lon', type=float, default=0.0006, help='grid cell width in degrees')
    ap.add_argument('--cell-lat', type=float, default=0.0005, help='grid cell height in degrees')
    ap.add_argument('--out', default=os.path.join(ROOT, 'data'))
    a = ap.parse_args()
    city, sal = load_city()
    canopy = load_canopy()
    write_grid(canopy, city, a.cell_lon, a.cell_lat, a.out)
    write_outline(sal, a.out)
    p = write_points(load_inat(a.year, city), canopy, sal, a.year, a.out)
    write_suburbs(p, canopy, sal, city, a.year, a.out)


if __name__ == '__main__':
    main()
