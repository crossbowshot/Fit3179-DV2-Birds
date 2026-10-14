import pandas as pd, numpy as np
d = pd.read_csv('melb_records_full.csv', dtype={'observer_id':str})
d['individualCount']=pd.to_numeric(d.individualCount, errors='coerce')
d['month']=pd.to_numeric(d.month, errors='coerce')
i = d[d.dataResourceName=='iNaturalist Australia'].copy()
out='viz/data/'
# A. heatmap: iNat weekday x hour (local)
h = i.dropna(subset=['eventTime']).copy()
h['hour']=h.eventTime.str[:2].astype(int)
h['date']=pd.to_datetime(h.eventDate.str[:10])
h['weekday_num']=h.date.dt.dayofweek
h['weekday']=h.date.dt.day_name().str[:3]
A=h.groupby(['weekday_num','weekday','hour']).size().rename('records').reset_index()
A.to_csv(out+'inat_weekday_hour_2025.csv', index=False)
print('A rows',len(A),'records',A.records.sum()); print(A.groupby('weekday').records.sum().to_dict())
print(A.groupby('hour').records.sum().to_dict())
# B. jitter: records per iNat observer
B=i.groupby('observer_id').size().rename('records').reset_index().sort_values('records',ascending=False)
B.to_csv(out+'inat_observer_records_2025.csv', index=False)
n=len(B); tot=B.records.sum()
print('B observers',n,'top1',B.records.iloc[0],'share top1%',round(B.records.head(max(1,n//100)).sum()/tot*100,1),
      'share top10%',round(B.records.head(n//10).sum()/tot*100,1),'one-record obs',(B.records==1).sum(),'median',B.records.median())
# C. butterfly: keen = top 10% observers
keen=set(B.observer_id.head(n//10))
i['group']=np.where(i.observer_id.isin(keen),'Keen observers (top 10%)','Everyone else')
top=i.vernacularName.value_counts().head(10).index
C=(i[i.vernacularName.isin(top)].groupby(['group','vernacularName']).size()
   / i.groupby('group').size()).rename('share').mul(100).round(2).reset_index()
C.to_csv(out+'inat_keen_vs_casual_species_2025.csv', index=False)
print(C.pivot(index='vernacularName',columns='group',values='share').sort_values('Everyone else',ascending=False))
print('group sizes', i.group.value_counts().to_dict())
# D. bump: season ranks for top 8 species (all sources)
season={12:'Summer',1:'Summer',2:'Summer',3:'Autumn',4:'Autumn',5:'Autumn',6:'Winter',7:'Winter',8:'Winter',9:'Spring',10:'Spring',11:'Spring'}
d['season']=d.month.map(season)
r=d.dropna(subset=['season']).groupby(['season','vernacularName']).size().rename('records').reset_index()
r['rank']=r.groupby('season').records.rank(ascending=False, method='first').astype(int)
top8=d.vernacularName.value_counts().head(8).index
D=r[r.vernacularName.isin(top8)].copy()
order={'Summer':1,'Autumn':2,'Winter':3,'Spring':4}; D['season_order']=D.season.map(order)
D.sort_values(['vernacularName','season_order']).to_csv(out+'melb_species_season_rank_2025.csv', index=False)
print(D.pivot(index='vernacularName',columns='season',values='rank')[['Summer','Autumn','Winter','Spring']])
# E. slope: rank by records vs rank by birds counted
s=d.groupby('vernacularName').agg(records=('vernacularName','size'),birds=('individualCount','sum'))
s['rank_records']=s.records.rank(ascending=False,method='first').astype(int)
s['rank_birds']=s.birds.rank(ascending=False,method='first').astype(int)
E=s[(s.rank_records<=10)|(s.rank_birds<=10)].reset_index()
E.to_csv(out+'melb_records_vs_birds_rank_2025.csv', index=False)
print(E.sort_values('rank_records').to_string(index=False))
