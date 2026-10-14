import geopandas as gpd, pandas as pd, numpy as np
melb = gpd.read_file('melb_tmp.gpkg')[['SAL_CODE_2021','geometry']]
cols=['dataResourceName','recordedBy','eventDate','eventTime','verbatimEventDate','month',
      'decimalLatitude','decimalLongitude','vernacularName','individualCount','species','taxonRank']
obs={}
def anon(s):
    if pd.isna(s) or s.strip().lower() in ('unknown','birds australia') or s.startswith('<a '): return np.nan
    if s not in obs: obs[s]=f'obs{len(obs)+1:05d}'
    return obs[s]
parts=[]
for ch in pd.read_csv('full/Birds_occurencerecordFit3179.csv', usecols=cols, chunksize=300000, dtype=str, low_memory=False):
    pts=gpd.GeoDataFrame(ch, geometry=gpd.points_from_xy(pd.to_numeric(ch.decimalLongitude), pd.to_numeric(ch.decimalLatitude)), crs=4326)
    j=gpd.sjoin(pts, melb, how='inner', predicate='within'); j=j[~j.index.duplicated()]
    j['observer_id']=[anon(x) for x in j.recordedBy]
    parts.append(pd.DataFrame(j.drop(columns=['geometry','index_right','recordedBy'])))
d=pd.concat(parts, ignore_index=True)
d.to_csv('melb_records_full.csv', index=False)
print(len(d)); print(d.dataResourceName.value_counts().head(4))
i=d[d.dataResourceName=='iNaturalist Australia']
print('iNat', len(i), 'observers', i.observer_id.nunique())
print(i[['eventDate','eventTime','verbatimEventDate']].head(5).to_string())
print('month present', d.month.notna().mean())
