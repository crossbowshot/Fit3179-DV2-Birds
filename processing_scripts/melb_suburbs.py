import geopandas as gpd, pandas as pd, numpy as np
gp = 'abs/G01_VIC_GDA2020.gpkg'
sal = gpd.read_file(gp, layer='G01_SAL_2021_VIC', columns=['SAL_CODE_2021','SAL_NAME_2021','Tot_P_P']).set_crs(4326, allow_override=True)
gmel = gpd.read_file(gp, layer='G01_GCCSA_2021_VIC').query("GCCSA_CODE_2021=='2GMEL'").set_crs(4326, allow_override=True)
sal = sal[sal.geometry.notna() & ~sal.geometry.is_empty]
inside = sal.representative_point().within(gmel.geometry.iloc[0])
melb = sal[inside].copy()
melb['suburb'] = melb.SAL_NAME_2021.str.replace(r' \(Vic\.\)$', '', regex=True)
print('Greater Melbourne suburbs:', len(melb), 'population:', melb.Tot_P_P.sum())

# join every 2025 record to the official 2021 suburb boundaries
counts = pd.Series(0, index=melb.SAL_CODE_2021)
for ch in pd.read_csv('full/birds_vic_2025_with_suburb.csv', usecols=['decimalLatitude','decimalLongitude'], chunksize=400000):
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(ch.decimalLongitude, ch.decimalLatitude), crs=4326)
    j = gpd.sjoin(pts, melb[['SAL_CODE_2021','geometry']], how='inner', predicate='within')
    j = j[~j.index.duplicated()]
    counts = counts.add(j.SAL_CODE_2021.value_counts(), fill_value=0)
melb['bird_records'] = melb.SAL_CODE_2021.map(counts).fillna(0).astype(int)
melb['records_per_1000_residents'] = np.where(melb.Tot_P_P > 0, melb.bird_records / melb.Tot_P_P * 1000, np.nan).round(1)
melb.to_file('melb_tmp.gpkg', driver='GPKG')
print('records in Greater Melbourne:', melb.bird_records.sum())
