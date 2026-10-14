import pandas as pd, geopandas as gpd, numpy as np, hashlib
sub = gpd.read_file('geo/suburb-10-vic.geojson')[['loc_pid','vic_loca_2','geometry']]
sub = sub.rename(columns={'loc_pid':'suburb_id','vic_loca_2':'suburb'})
sub['suburb'] = sub['suburb'].str.title()
dups = sub['suburb'].value_counts(); dups = set(dups[dups>1].index)
print('duplicate suburb names:', sorted(dups))
cols=['recordID','dataResourceName','eventDate','eventTime','month','decimalLatitude','decimalLongitude',
      'coordinateUncertaintyInMeters','scientificName','vernacularName','family','order','species','taxonRank',
      'individualCount','identificationVerificationStatus','dcterms:license','recordedBy','dataGeneralizations']
obs_map = {}
def anon(s):
    if pd.isna(s) or s.startswith('<a ') or s.strip().lower() in ('unknown','birds australia'): return np.nan
    if s not in obs_map: obs_map[s] = f'obs{len(obs_map)+1:05d}'
    return obs_map[s]
out='full/birds_vic_2025_with_suburb.csv'; first=True; n=0; nomatch=0
for ch in pd.read_csv('full/Birds_occurencerecordFit3179.csv', usecols=cols, chunksize=250000, dtype=str, low_memory=False):
    ch['lat']=pd.to_numeric(ch.decimalLatitude); ch['lon']=pd.to_numeric(ch.decimalLongitude)
    pts=gpd.GeoDataFrame(ch, geometry=gpd.points_from_xy(ch.lon, ch.lat), crs='EPSG:4326')
    j=gpd.sjoin(pts, sub, how='left', predicate='within').drop(columns=['index_right'])
    j=j[~j.index.duplicated(keep='first')]   # point exactly on a shared border -> keep one
    j['observer_id']=[anon(x) for x in j.recordedBy]
    j=j.drop(columns=['recordedBy','geometry','lat','lon']).rename(columns={'dataResourceName':'source','dcterms:license':'license'})
    nomatch+=j.suburb.isna().sum(); n+=len(j)
    j.to_csv(out, mode='w' if first else 'a', header=first, index=False); first=False
    print(n, flush=True)
print('rows',n,'no suburb',nomatch, round(nomatch/n*100,2),'%','observers',len(obs_map))
