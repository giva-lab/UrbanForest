from pathlib import Path
import geopandas as gpd, pandas as pd,numpy as np,shapely,json,hashlib,sys,sqlite3,xml.etree.ElementTree as ET,zipfile
P=Path(sys.argv[1] if len(sys.argv)>1 else 'upload'); O=Path('investigation/results');O.mkdir(parents=True,exist_ok=True)
files=list(P.glob('*'));json.dump({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},open(O/'input_sha256.json','w'),indent=2)
g=gpd.read_file(P/'grid_50_analysis_controls_v2.gpkg');a=gpd.read_file(P/'grid_50_model_complete_cases_v2.gpkg');w=gpd.read_file(P/'grid_cells_without_street.gpkg');r=gpd.read_file(P/'landuse_grid50_final.gpkg');r0=gpd.read_file(P/'landuse.gpkg')
C=['infrastructure_index','high_income','streetlight','schools_r500m','transport_hubs_r500m','police_station_r500m','private_parking_r500m','paid_parking_distance','moradores','distancia_marco_zero']
rows=[]
for name,d in [('parent',g),('complete',a),('without',w),('roads',r),('roads_original',r0)]:
 d.drop(columns='geometry').describe(include='all').T.to_csv(O/f'{name}_distributions.csv')
 for c in d.columns:
  if c!='geometry':rows.append(dict(file=name,column=c,dtype=str(d[c].dtype),missing=int(d[c].isna().sum()),unique=d[c].nunique()))
 print(name,len(d),d.crs,'invalid',(~d.is_valid).sum(),'duplicates',d.geometry.to_wkb().duplicated().sum(),flush=True)
pd.DataFrame(rows).to_csv(O/'columns.csv',index=False)
assert not g.id.duplicated().any() and not a.id.duplicated().any()
print('complete exact',set(g.dropna(subset=C).id)==set(a.id));print('without exact',set(g[g.streetlight.isna()].id)==set(w.id))
common=[c for c in a if c!='geometry'];diff=(g.set_index('id').loc[a.id, [c for c in common if c!='id']].reset_index().to_numpy()!=a[common].to_numpy()).sum();print('attributes differences',diff)
print('road original ids',r.edge_id.nunique(),r0.edge_id.nunique(), 'classes',r.filter(like='class_').sum().to_dict())
# spatial join exact line intersections, union per cell to prevent directed edge double counting
idx=r.sindex.query(g.geometry,predicate='intersects');ci,ri=idx
parts=shapely.intersection(g.geometry.values[ci],r.geometry.values[ri]);lens=shapely.length(parts)
j=pd.DataFrame({'cell':ci,'road':ri,'part':parts,'len':lens});j=j[j.len>1e-6].copy()
lengths=j.groupby('cell').part.apply(lambda x:shapely.length(shapely.union_all(x.to_numpy())))
g['road_m']=0.;g.loc[lengths.index,'road_m']=lengths
motorcols=['class_ARTERIAL','class_COLETORA','class_LOCAL','class_RODOVIA'];motor=r[motorcols].fillna(0).gt(0).any(axis=1).to_numpy()
jm=j[motor[j.road.to_numpy()]];ml=jm.groupby('cell').part.apply(lambda x:shapely.length(shapely.union_all(x.to_numpy())))
g['motor_m']=0.;g.loc[ml.index,'motor_m']=ml
for c in r.filter(like='class_').columns:
 jj=j[r[c].fillna(0).to_numpy()[j.road.to_numpy()]>0]; ll=jj.groupby('cell').part.apply(lambda x:shapely.length(shapely.union_all(x.to_numpy())))
 g[c]=0.;g.loc[ll.index,c]=ll
# compare network availability by positive intersection, not arbitrary proximity
for name,net in [('original',r0)]:
 ci,ri=net.sindex.query(g.geometry,predicate='intersects'); le=shapely.length(shapely.intersection(g.geometry.values[ci],net.geometry.values[ri]));g['road_original']=False;g.loc[np.unique(ci[le>1e-6]),'road_original']=True
print('geometry road positive',int((g.road_m>0).sum()),'original',g.road_original.sum());print(pd.crosstab(g.streetlight.notna(),g.road_m>0))
print('withouts intersect',int(w.id.isin(g.loc[g.road_m>0,'id']).sum()))
g['complete']=g.id.isin(a.id);g['without_flag']=g.id.isin(w.id);g['x']=g.geometry.centroid.x;g['y']=g.geometry.centroid.y
checks={'parent_n':len(g),'complete_equals_dropna':set(g.dropna(subset=C).id)==set(a.id),'without_equals_null_streetlight':set(g[g.streetlight.isna()].id)==set(w.id),'shared_attribute_differences':int(diff),'invalid_parent':int((~g.is_valid).sum()),'geometry_area_min':float(g.area.min()),'geometry_area_max':float(g.area.max()),'area_error_max':float(abs(g.area-g.cell_area).max()),'road_positive':int((g.road_m>0).sum()),'road_original_positive':int(g.road_original.sum()),'complete_no_road':int((g.complete & (g.road_m==0)).sum()),'missing_controls_on_road':int(((g.road_m>0)&~g.complete).sum()),'veg_plus_shadow_over100':int((g.veg_pct+g.shadow_pct>100.001).sum()),'veg_area_over_cell':int((g.veg_area>g.cell_area).sum()),'shadow_area_over_cell':int((g.shadow_area>g.cell_area).sum()),'veg_pct_formula_maxdiff':float(abs(g.veg_pct-np.clip(g.veg_area/g.cell_area*100,0,100)).max()),'shadow_pct_formula_maxdiff':float(abs(g.shadow_pct-np.clip(g.shadow_area/g.cell_area*100,0,100)).max())}
json.dump(checks,open(O/'geometry_checks.json','w'),indent=2);print(checks)
# Does grid inherit an entire segment's values? weighted-mean / first / nearest are audited, not asserted.
inherit=[]
for c in C:
 tmp=j[['cell','road','len']].copy();tmp['value']=r[c].to_numpy()[tmp.road];tmp=tmp.dropna();stats=tmp.groupby('cell').value.agg(['min','max','mean','first']);v=g.loc[stats.index,c];valid=v.notna()
 inherit.append(dict(variable=c,n=int(valid.sum()),within_segment_range=float(((v>=stats['min']-1e-8)&(v<=stats['max']+1e-8))[valid].mean()),matches_first=float(np.isclose(v[valid],stats['first'][valid]).mean()),matches_mean=float(np.isclose(v[valid],stats['mean'][valid]).mean())))
pd.DataFrame(inherit).to_csv(O/'control_inheritance.csv',index=False)
g.to_file(O/'audit_cells.gpkg',driver='GPKG');g.drop(columns='geometry').to_csv(O/'audit_cells.csv',index=False)
# metadata exactly as supplied
with zipfile.ZipFile(P/'fase9.qgz') as z:
 root=ET.fromstring(z.read('fase9.qgs')); json.dump([dict(name=l.findtext('layername'),source=l.findtext('datasource'),abstract=l.findtext('.//abstract')) for l in root.findall('.//projectlayers/maplayer')],open(O/'qgis_sources.json','w'),ensure_ascii=False,indent=2)
