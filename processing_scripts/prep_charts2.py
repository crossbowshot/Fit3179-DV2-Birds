import pandas as pd, numpy as np
d=pd.read_csv('melb_records_full.csv', low_memory=False, dtype={'observer_id':str,'eventTime':str})
name=pd.read_csv('species_common_names.csv', index_col=0).common_name.replace({'Spotted Turtle-dove':'Spotted Dove','Eurasian Blackbird':'Common Blackbird'})
d['common']=d.species.map(name)
d['individualCount']=pd.to_numeric(d.individualCount, errors='coerce')
N=len(d); out='viz/data/'
intro={'Common Myna','Spotted Dove','Common Blackbird','Common Starling','House Sparrow','Rock Dove','European Goldfinch'}
# lollipop top 15 (species level)
t=d.groupby('common').agg(records=('common','size'),birds_counted=('individualCount','sum')).sort_values('records',ascending=False).head(15).reset_index().rename(columns={'common':'species'})
t.insert(0,'rank',range(1,16)); t['share_pct']=(t.records/N*100).round(1); t['birds_counted']=t.birds_counted.astype(int)
t['status']=np.where(t.species.isin(intro),'Introduced','Native')
t.to_csv(out+'melb_top15_species_2025.csv', index=False); print(t[['rank','species','records','share_pct','status']].to_string(index=False))
# slope: rank by records vs rank by birds counted (species level)
s=d.dropna(subset=['common']).groupby('common').agg(records=('common','size'),birds=('individualCount','sum'))
s['rank_records']=s.records.rank(ascending=False,method='first').astype(int)
s['rank_birds']=s.birds.rank(ascending=False,method='first').astype(int)
E=s[(s.rank_records<=8)|(s.rank_birds<=8)].reset_index().rename(columns={'common':'species'})
E['birds']=E.birds.astype(int); E.to_csv(out+'melb_records_vs_birds_rank_2025.csv', index=False)
print(E.sort_values('rank_records').to_string(index=False))
