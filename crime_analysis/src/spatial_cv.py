# Audit of the historical Gaussian-basis pilot; not GWR/GWNB.
from pathlib import Path
import geopandas as gpd,numpy as np,pandas as pd
from scipy.spatial import cKDTree,distance
from scipy.optimize import minimize
from scipy.special import gammaln,expit
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial
O=Path('investigation/results');d=gpd.read_file(O/'audit_cells.gpkg');d=d[d.complete].copy();xy=d[['x','y']].to_numpy();y=d.veiculo_n.to_numpy();fold=pd.read_csv(O/'folds.csv').set_index('id').loc[d.id,'fold'].to_numpy()
cols=['veg_pct','shadow_pct','infrastructure_index','high_income','streetlight','schools_r500m','transport_hubs_r500m','police_station_r500m','private_parking_r500m','paid_parking_distance','moradores','distancia_marco_zero'];raw=d[cols].to_numpy()
def centers(coords):
 first=np.argmin(np.sum((coords-coords.mean(axis=0))**2,axis=1));idx=[first];dd=np.sum((coords-coords[first])**2,axis=1)
 for _ in range(39):
  k=np.argmax(dd);idx.append(k);dd=np.minimum(dd,np.sum((coords-coords[k])**2,axis=1))
 return coords[idx]
allcenters=centers(xy);rows=[]
for k in range(5):
 te=fold==k;tr=(~te)&(cKDTree(xy[te]).query(xy)[0]>300);m=raw[tr].mean(axis=0);s=raw[tr].std(axis=0);X=np.column_stack([np.ones(len(d)),(raw-m)/s]);res=NegativeBinomial(y[tr],X[tr],loglike_method='nb2').fit(method='bfgs',disp=False,maxiter=600,gtol=1e-7);alpha=res.params[-1];r=1/alpha;logr=np.log(r)
 for mode in ['historical_fixed_centers','training_only_centers']:
  cc=allcenters if mode=='historical_fixed_centers' else centers(xy[tr]);cc=cc[cKDTree(xy[tr]).query(cc)[0]<=1500];B=np.exp(-.5*distance.cdist(xy,cc,'sqeuclidean')/1500**2);B-=B[tr].mean(axis=0);Z=np.column_stack([B*X[:,1,None],B*X[:,2,None]]);A=np.linalg.lstsq(X[tr],Z[tr],rcond=None)[0];Z-=X@A;M=np.column_stack([X,Z]);p=X.shape[1];Mt=M[tr];yt=y[tr]
  def objective(b):
   eta=Mt@b;ld=np.logaddexp(logr,eta);val=-np.sum(r*(logr-ld)+yt*(eta-ld))+.5*100*np.sum(b[p:]**2);grad=-Mt.T@(yt-(yt+r)*expit(eta-logr));grad[p:]+=100*b[p:];return val,grad
  out=minimize(objective,np.r_[res.params[:-1],np.zeros(Z.shape[1])],jac=True,method='L-BFGS-B',options={'maxiter':500,'ftol':1e-10});eta=M[te]@out.x;ld=np.logaddexp(logr,eta);yy=y[te];ll=gammaln(yy+r)-gammaln(r)-gammaln(yy+1)+r*(logr-ld)+yy*(eta-ld)
  rows.append(dict(mode=mode,fold=k,n=int(te.sum()),centers=len(cc),converged=out.success,logscore=ll.mean(),eta_min=eta.min(),eta_max=eta.max()));print(rows[-1],flush=True)
 pd.DataFrame(rows).to_csv(O/'spatial_cv.csv',index=False)
