from pathlib import Path
import sys
import hashlib,json,geopandas as gpd,numpy as np,pandas as pd,statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial,Poisson
from statsmodels.stats.outliers_influence import variance_inflation_factor
INPUT=Path(sys.argv[1] if len(sys.argv)>1 else 'input');O=Path('investigation/results');g=gpd.read_file(O/'audit_cells.gpkg');d=g[g.complete].copy();cols=['veg_pct','shadow_pct','infrastructure_index','high_income','streetlight','schools_r500m','transport_hubs_r500m','police_station_r500m','private_parking_r500m','paid_parking_distance','moradores','distancia_marco_zero'];d['log_road_m']=np.log1p(d.road_m);cols+=['log_road_m']
for c in ['class_ARTERIAL','class_COLETORA','class_RODOVIA','class_VIA DE PEDESTRES','class_VTR']:
 d[c+'_share']=d[c]/d.road_m;cols.append(c+'_share')
X=sm.add_constant((d[cols]-d[cols].mean())/d[cols].std(ddof=0));y=d.veiculo_n
pd.DataFrame({'variable':X.columns,'VIF':[variance_inflation_factor(X.to_numpy(),i) for i in range(X.shape[1])]}).to_csv(O/'vif_road_model.csv',index=False);d[cols].corr().to_csv(O/'correlations.csv')
p=Poisson(y,X).fit(method='bfgs',disp=False,maxiter=300);r=NegativeBinomial(y,X).fit(start_params=np.r_[p.params,1.],method='bfgs',disp=False,maxiter=600,gtol=1e-7)
old=pd.read_csv(O/'models.csv').set_index('model').loc['nb_roads'];hashes=json.load(open(O/'input_sha256.json'));checks={'originals_unchanged':all(hashlib.sha256((INPUT/f).read_bytes()).hexdigest()==h for f,h in hashes.items()),'all_counts_integer_nonnegative':all(((g[c]>=0)&(g[c]%1==0)).all() for c in ['veiculo_n','celular_n']),'design_full_rank':bool(np.linalg.matrix_rank(X)==X.shape[1]),'condition_number_standardized':float(np.linalg.cond(X)),'second_start_converged':bool(r.mle_retvals['converged']),'second_start_AIC':float(r.aic),'AIC_difference_starts':float(r.aic-old.AIC),'alpha_second_start':float(r.params.iloc[-1])}
assert checks['originals_unchanged'] and checks['all_counts_integer_nonnegative'] and checks['design_full_rank'] and checks['second_start_converged'] and abs(checks['AIC_difference_starts'])<.001
json.dump(checks,open(O/'final_checks.json','w'),indent=2);print(checks)
