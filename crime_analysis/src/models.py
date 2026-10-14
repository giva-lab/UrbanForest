# Run from the parent directory: OPENBLAS_NUM_THREADS=1 python investigation/models.py
from pathlib import Path
import geopandas as gpd,pandas as pd,numpy as np,json,warnings
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial,Poisson
from statsmodels.stats.sandwich_covariance import cov_cluster
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix,diags
from scipy.special import gammaln
from sklearn.cluster import KMeans
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path('investigation/results');g=gpd.read_file(O/'audit_cells.gpkg')
E=['veg_pct','shadow_pct'];C=['infrastructure_index','high_income','streetlight','schools_r500m','transport_hubs_r500m','police_station_r500m','private_parking_r500m','paid_parking_distance','moradores','distancia_marco_zero'];F=E+C
# Measures are geometric proxies, not numbers of vehicles or person-time. No offset imposed.
g['log_road_m']=np.log1p(g.road_m);g['log_motor_m']=np.log1p(g.motor_m)
for c in ['class_ARTERIAL','class_COLETORA','class_RODOVIA','class_VIA DE PEDESTRES','class_VTR']:g[c+'_share']=g[c]/g.road_m.replace(0,np.nan)
R=['log_road_m','class_ARTERIAL_share','class_COLETORA_share','class_RODOVIA_share','class_VIA DE PEDESTRES_share','class_VTR_share']
S={'parent':np.ones(len(g),bool),'complete':g.complete,'roads_all':g.road_m>0,'no_roads':g.road_m==0,'roads_incomplete':(g.road_m>0)&~g.complete,'motor_complete':g.complete&(g.motor_m>0),'motor10_complete':g.complete&(g.motor_m>=10),'motor25_complete':g.complete&(g.motor_m>=25)}
rows=[]
for name,m in S.items():
 d=g[m];row=dict(sample=name,n=len(d),area_km2=d.area.sum()/1e6,veg_mean=d.veg_pct.mean(),shadow_mean=d.shadow_pct.mean(),veg_median=d.veg_pct.median(),shadow_median=d.shadow_pct.median(),road_mean=d.road_m.mean(),veg_gt50_pct=100*(d.veg_pct>50).mean())
 for y in ['veiculo_n','celular_n']:row.update({y+'_sum':d[y].sum(),y+'_mean':d[y].mean(),y+'_zero_pct':100*(d[y]==0).mean(),y+'_variance_mean':d[y].var()/d[y].mean()})
 rows.append(row)
pd.DataFrame(rows).to_csv(O/'selections.csv',index=False)
modelrows=[];coefrows=[];moranrows=[];cache={}
def fit(d,cols,y='veiculo_n',family='NB2'):
 raw=d[cols].astype(float);means=raw.mean();scales=raw.std(ddof=0).replace(0,1);X=sm.add_constant((raw-means)/scales,has_constant='add');yy=d[y].to_numpy();model=NegativeBinomial(yy,X,loglike_method='nb2') if family=='NB2' else Poisson(yy,X)
 with warnings.catch_warnings(record=True) as ws:
  start=None
  if family=='NB2':
   pr=Poisson(yy,X).fit(method='bfgs',disp=False,maxiter=300)
   start=np.r_[pr.params,5.0]
  res=model.fit(start_params=start,method='bfgs',maxiter=600,disp=False,gtol=1e-7)
 if not res.mle_retvals['converged'] or not np.all(np.isfinite(res.bse)): raise RuntimeError('nonconvergence or invalid Hessian')
 return res,means,scales,X,[str(x.message) for x in ws]
def moran(d,z,name,rad):
 xy=d[['x','y']].to_numpy();pairs=cKDTree(xy).query_pairs(rad,output_type='ndarray');ii=np.r_[pairs[:,0],pairs[:,1]];jj=np.r_[pairs[:,1],pairs[:,0]];W=csr_matrix((np.ones(len(ii)),(ii,jj)),shape=(len(d),len(d)));deg=np.asarray(W.sum(axis=1)).ravel();W=diags(1/np.maximum(deg,1))@W;s0=W.sum();v=z-z.mean();den=v@v;I=len(v)/s0*(v@(W@v))/den;rng=np.random.default_rng(42);null=[]
 for _ in range(999):
  p=rng.permutation(v);null.append(len(v)/s0*(p@(W@p))/den)
 p=(1+np.sum(np.abs(np.asarray(null)+1/(len(v)-1))>=abs(I+1/(len(v)-1))))/1000
 moranrows.append(dict(model=name,radius=rad,I=I,p_two_sided=p,islands=int((deg==0).sum())))
for sample,cols,family,y,label in [
 ('complete',E,'Poisson','veiculo_n','poisson_simple'),('complete',E,'NB2','veiculo_n','nb_simple'),('complete',F,'NB2','veiculo_n','nb_full'),
 ('complete',F+R,'NB2','veiculo_n','nb_roads'),('complete',E+R,'NB2','veiculo_n','nb_roadsonly'),
 ('parent',E,'NB2','veiculo_n','parent_simple'),('roads_all',E,'NB2','veiculo_n','roads_simple'),('no_roads',E,'NB2','veiculo_n','noroad_simple'),
 ('motor_complete',F,'NB2','veiculo_n','motor_full'),('motor10_complete',F,'NB2','veiculo_n','motor10_full'),('motor25_complete',F,'NB2','veiculo_n','motor25_full'),
 ('complete',E,'Poisson','celular_n','cell_poisson'),('complete',E,'NB2','celular_n','cell_simple'),('complete',F,'NB2','celular_n','cell_full')]:
 d=g[S[sample]].copy();res,means,scales,X,warns=fit(d,cols,y,family);mu=np.asarray(res.predict());alpha=float(res.params.iloc[-1]) if family=='NB2' else 0;var=mu+alpha*mu**2;z=(d[y].to_numpy()-mu)/np.sqrt(var)
 modelrows.append(dict(model=label,sample=sample,outcome=y,n=len(d),AIC=res.aic,loglik=res.llf,alpha=alpha,zero_observed=(d[y]==0).mean(),zero_predicted=np.mean((1+alpha*mu)**(-1/alpha)) if alpha else np.exp(-mu).mean(),pearson_dispersion=np.sum(z*z)/(len(d)-X.shape[1]),converged=res.mle_retvals['converged'],max_gradient=float(np.max(abs(res.mle_retvals['gopt']))),warnings=';'.join(warns)))
 for block in [0,500,1000,2000]:
  if block:
   groups=pd.factorize(pd.MultiIndex.from_arrays([np.floor(d.x/block).astype(int),np.floor(d.y/block).astype(int)]))[0];cov=cov_cluster(res,groups);se=np.sqrt(np.maximum(np.diag(cov),0));ng=len(np.unique(groups))
  else:se=np.asarray(res.bse);ng=0
  for k,c in enumerate(cols,1):
   b=res.params.iloc[k]/scales[c];err=se[k]/scales[c];coefrows.append(dict(model=label,variable=c,block_m=block,clusters=ng,beta=b,se=err,lo=b-1.96*err,hi=b+1.96*err,IRR10=np.exp(10*b)))
 if label in ['nb_full','nb_roads','motor25_full','cell_full']:
  for rad in [70.72,100.01]:moran(d,z,label,rad)
  if label=='nb_full':g.loc[d.index,'resid_full']=z
 cache[label]=(res,means,scales);print(label,len(d),'AIC',round(res.aic,3),'veg',res.params.iloc[1]/scales.iloc[0],'shadow',res.params.iloc[2]/scales.iloc[1],flush=True)
 pd.DataFrame(modelrows).to_csv(O/'models.csv',index=False);pd.DataFrame(coefrows).to_csv(O/'coefficients.csv',index=False);pd.DataFrame(moranrows).to_csv(O/'moran.csv',index=False)
# Pre-specified geographic folds; same test cells for comparing full vs road-adjusted.
d=g[g.complete].copy();xy=d[['x','y']].to_numpy();fold=KMeans(n_clusters=5,random_state=42,n_init=20).fit_predict(xy);d['fold']=fold;cv=[]
for k in range(5):
 te=fold==k;distance=cKDTree(xy[te]).query(xy)[0];tr=(~te)&(distance>300)
 for label,cols in [('global',F),('road_adjusted',F+R)]:
  res,m,s,_,warn=fit(d[tr],cols);Xte=sm.add_constant((d.loc[te,cols]-m)/s,has_constant='add');eta=Xte.to_numpy()@res.params.iloc[:-1].to_numpy();alpha=res.params.iloc[-1];rr=1/alpha;y=d.loc[te,'veiculo_n'].to_numpy();den=np.logaddexp(np.log(rr),eta);ll=gammaln(y+rr)-gammaln(rr)-gammaln(y+1)+rr*(np.log(rr)-den)+y*(eta-den)
  for target,mask in [('all',np.ones(te.sum(),bool)),('motor25',d.loc[te,'motor_m'].to_numpy()>=25)]:cv.append(dict(model=label,fold=k,target=target,n_train=int(tr.sum()),n_test=int(mask.sum()),min_separation_m=float(distance[tr].min()),logscore=float(ll[mask].mean()),eta_min=float(eta.min()),eta_max=float(eta.max()),observed_mean=float(y[mask].mean()),predicted_mean=float(np.exp(eta[mask]).mean())))
  print('CV',k,label,round(ll.mean(),6),flush=True)
 pd.DataFrame(cv).to_csv(O/'cv.csv',index=False)
d[['id','fold']].to_csv(O/'folds.csv',index=False)
# fixed geographic summaries (no claim of district boundaries)
g['tile_x']=np.floor(g.x/1000).astype(int);g['tile_y']=np.floor(g.y/1000).astype(int)
g.groupby(['tile_x','tile_y']).agg(n=('id','size'),complete=('complete','sum'),road_m=('road_m','sum'),veiculo_n=('veiculo_n','sum'),veg_pct=('veg_pct','mean')).to_csv(O/'geographic_coverage_1km.csv')
# Maps preserve metric aspect, using cell centroids at 50m resolution.
fig,ax=plt.subplots(1,3,figsize=(15,6));status=np.where(g.complete,2,np.where(g.road_m>0,1,0))
for i,(vals,title,cmap) in enumerate([(status,'Seleção: cinza sem via; laranja incompleta; azul completa','viridis'),(g.veg_pct,'Vegetação (%)','YlGn'),(np.log1p(g.veiculo_n),'Crimes de veículos: log(1 + contagem)','magma')]):
 if i==0:
  from matplotlib.colors import ListedColormap
  cmap=ListedColormap(['#bbbbbb','#df9229','#22649b'])
 sc=ax[i].scatter(g.x/1000,g.y/1000,c=vals,s=.9,marker='s',cmap=cmap,rasterized=True);ax[i].set_aspect('equal');ax[i].set_title(title,fontsize=9);ax[i].set_xlabel('UTM E (km)');ax[i].set_ylabel('UTM N (km)')
 if i:fig.colorbar(sc,ax=ax[i],shrink=.7)
fig.tight_layout();fig.savefig(O/'map_selection.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(1,3,figsize=(14,5))
for i,(vals,title) in enumerate([(d.fold,'Blocos geográficos (CV)'),(g.loc[g.complete,'road_m'],'Comprimento viário único (m)'),(g.loc[g.complete,'resid_full'].clip(-2,4),'Resíduos Pearson: cor limitada a [-2,4]')]):
 sc=ax[i].scatter(d.x/1000,d.y/1000,c=vals,s=1,marker='s',cmap='viridis',rasterized=True);ax[i].set_aspect('equal');ax[i].set_title(title,fontsize=10);fig.colorbar(sc,ax=ax[i],shrink=.7)
fig.tight_layout();fig.savefig(O/'map_diagnostics.png',dpi=180);plt.close(fig)
cf=pd.DataFrame(coefrows);labels=['nb_full','nb_roads','motor_full','motor10_full','motor25_full'];fig,ax=plt.subplots(1,2,figsize=(10,4))
for i,c in enumerate(E):
 q=cf[(cf.variable==c)&(cf.block_m==1000)].set_index('model').loc[labels];ax[i].errorbar(q.beta*10,np.arange(len(q)),xerr=q.se*19.6,fmt='o');ax[i].axvline(0,color='gray',ls='--');ax[i].set_yticks(np.arange(len(q)),labels);ax[i].set_title(c+' — log razão por 10 p.p.');ax[i].set_xlabel('IC 95%: blocos de 1 km; exploratório')
fig.tight_layout();fig.savefig(O/'coefficients.png',dpi=180);plt.close(fig)
print('DONE',flush=True)
