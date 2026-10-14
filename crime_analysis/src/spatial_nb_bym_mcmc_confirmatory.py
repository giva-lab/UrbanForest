# Auto-extracted from spatial_nb_bym_mcmc_confirmatory_v4.ipynb


# ---- notebook cell 1 ----
from pathlib import Path
import warnings, time, json
import numpy as np
import pandas as pd
import geopandas as gpd
import scipy
import scipy.sparse as sp
from scipy.spatial import cKDTree
from statsmodels.discrete.discrete_model import NegativeBinomial, Poisson
import statsmodels
import pymc as pm
import pytensor
import arviz as az

print("NumPy:", np.__version__)
print("SciPy:", scipy.__version__)
print("Statsmodels:", statsmodels.__version__)
print("PyMC:", pm.__version__)
print("PyTensor:", pytensor.__version__)
print("ArviZ:", az.__version__)


# ---- notebook cell 2 ----
BASE = Path.cwd()
GPKG = BASE / "audit_cells.gpkg"
assert GPKG.exists(), f"Missing file: {GPKG}"
RESULTS = BASE / "spatial_bym_mcmc_results"
RESULTS.mkdir(exist_ok=True)


# ---- notebook cell 4 ----
g = gpd.read_file(GPKG)

road_classes = ["class_ARTERIAL","class_COLETORA","class_RODOVIA",
                "class_VIA DE PEDESTRES","class_VTR"]
for c in road_classes:
    g[c+"_share"] = g[c] / g["road_m"].replace(0, np.nan)
g["log_road_m"] = np.log1p(g["road_m"])

ENV = ["veg_pct","shadow_pct"]
CONTROLS = ["infrastructure_index","high_income","streetlight",
            "schools_r500m","transport_hubs_r500m","police_station_r500m",
            "private_parking_r500m","paid_parking_distance",
            "moradores","distancia_marco_zero"]
ROADS = ["log_road_m","class_ARTERIAL_share","class_COLETORA_share",
         "class_RODOVIA_share","class_VIA DE PEDESTRES_share","class_VTR_share"]
PREDICTORS = ENV + CONTROLS + ROADS

d = g[g["complete"] == True].copy().reset_index(drop=True)
assert len(d) == 45004

Xraw = d[PREDICTORS].astype(float)
means = Xraw.mean()
sds = Xraw.std(ddof=0)
Z = ((Xraw-means)/sds).to_numpy(float)
X = np.column_stack([np.ones(len(d)),Z])
y = d["veiculo_n"].to_numpy(int)

pois = Poisson(y,X).fit(method="bfgs",disp=False,maxiter=150)
start=np.r_[pois.params,5.0]
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    nb=NegativeBinomial(y,X,loglike_method="nb2").fit(
        start_params=start,method="bfgs",maxiter=350,gtol=2e-6,disp=False)

bveg=float(nb.params[1]/sds["veg_pct"])
bsha=float(nb.params[2]/sds["shadow_pct"])
alpha_freq=float(nb.params[-1])

print("N =",len(d)," crimes =",int(y.sum()))
print("vegetation =",bveg)
print("shadow =",bsha)
print("alpha =",alpha_freq)
print("AIC =",float(nb.aic))
print("converged =",nb.mle_retvals.get("converged"))

assert nb.mle_retvals.get("converged",False)
assert abs(bveg+0.0032843)<5e-5
assert abs(bsha-0.0045083)<5e-5
assert abs(alpha_freq-4.3284)<0.02
assert abs(float(nb.aic)-58786.04)<2.0
print("GATEKEEPER PASSED")


# ---- notebook cell 6 ----
if {"x","y"}.issubset(d.columns):
    xx=d["x"].to_numpy(float); yy=d["y"].to_numpy(float)
else:
    cent=d.geometry.centroid
    xx=cent.x.to_numpy(); yy=cent.y.to_numpy()

bx=np.floor(xx/1000).astype(int)
by=np.floor(yy/1000).astype(int)
keys=list(zip(bx,by))
unique_keys=sorted(set(keys))
key_to_idx={k:i for i,k in enumerate(unique_keys)}
block_idx=np.array([key_to_idx[k] for k in keys],dtype="int32")
B=len(unique_keys)
assert B==204, f"Expected 204 blocks, found {B}"

coords_block=np.array(unique_keys)
W=np.zeros((B,B),dtype="int8")
for i in range(B):
    dx=np.abs(coords_block[:,0]-coords_block[i,0])
    dy=np.abs(coords_block[:,1]-coords_block[i,1])
    neigh=(dx<=1)&(dy<=1)&~((dx==0)&(dy==0))
    W[i,neigh]=1
W=np.maximum(W,W.T)
degree=W.sum(axis=1)

assert (degree==0).sum()==0
print("Blocks:",B," edges:",int(W.sum()//2),
      " degree:",int(degree.min()),"to",int(degree.max()))


# ---- notebook cell 8 ----
coords={"obs":np.arange(len(d)),"predictor":PREDICTORS,"block":np.arange(B)}
beta_start=nb.params[1:-1].copy()
intercept_start=float(nb.params[0])
alpha_pymc_start=1.0/alpha_freq

with pm.Model(coords=coords) as spatial_model:
    X_data=pm.Data("X",Z,dims=("obs","predictor"))
    block_data=pm.Data("block_idx",block_idx,dims="obs")

    intercept=pm.Normal("intercept",mu=intercept_start,sigma=1.0)
    beta=pm.Normal("beta",mu=beta_start,sigma=0.5,dims="predictor")

    sigma_spatial=pm.HalfNormal("sigma_spatial",sigma=0.5)
    sigma_iid=pm.HalfNormal("sigma_iid",sigma=0.5)

    phi_raw=pm.ICAR("phi_raw",W=W,sigma=1.0,dims="block")
    phi=pm.Deterministic("phi",sigma_spatial*phi_raw,dims="block")
    theta_raw=pm.Normal("theta_raw",0.0,1.0,dims="block")
    theta=pm.Deterministic("theta",sigma_iid*theta_raw,dims="block")

    log_alpha=pm.Normal("log_alpha",mu=np.log(alpha_pymc_start),sigma=0.75)
    alpha_pymc=pm.Deterministic("alpha_pymc",pm.math.exp(log_alpha))

    eta=intercept+pm.math.dot(X_data,beta)+phi[block_data]+theta[block_data]
    mu=pm.Deterministic("mu",pm.math.exp(eta),dims="obs")

    pm.NegativeBinomial("obs_count",mu=mu,alpha=alpha_pymc,
                        observed=y,dims="obs")


# ---- notebook cell 9 ----
SEED=42
DRAWS=1000
TUNE=1000

t0=time.time()
with spatial_model:
    idata=pm.sample(
        draws=DRAWS,
        tune=TUNE,
        chains=2,
        cores=1,
        random_seed=[42,31415],
        target_accept=0.95,
        init="jitter+adapt_diag",
        return_inferencedata=True,
        progressbar=True,
        compute_convergence_checks=False,
        idata_kwargs={"log_likelihood":False},
    )
elapsed=(time.time()-t0)/60
print(f"Sampling completed in {elapsed:.1f} minutes")


# ---- notebook cell 11 ----
post=idata.posterior

def scalar_draws(name):
    return np.asarray(post[name].values,float)

def split_rhat(a):
    # a: chains x draws; split each chain in half
    a=np.asarray(a,float)
    c,n=a.shape
    n2=n//2
    a=a[:,:2*n2].reshape(c,2,n2).reshape(c*2,n2)
    m=a.mean(axis=1)
    s2=a.var(axis=1,ddof=1)
    Wv=s2.mean()
    Bv=n2*m.var(ddof=1)
    varhat=(n2-1)/n2*Wv+Bv/n2
    return float(np.sqrt(varhat/Wv))

def basic_row(label,a):
    x=np.asarray(a,float)
    flat=x.ravel()
    return {
        "parameter":label,
        "mean":float(flat.mean()),
        "sd":float(flat.std(ddof=1)),
        "q2.5":float(np.quantile(flat,.025)),
        "median":float(np.quantile(flat,.5)),
        "q97.5":float(np.quantile(flat,.975)),
        "split_rhat":split_rhat(x),
    }

rows=[]
for name in ["intercept","sigma_spatial","sigma_iid","alpha_pymc"]:
    rows.append(basic_row(name,scalar_draws(name)))

for j,name in enumerate(PREDICTORS):
    a=np.asarray(post["beta"].isel(predictor=j).values,float)
    rows.append(basic_row(f"beta[{name}]",a))

diag=pd.DataFrame(rows)
print(diag)
diag.to_csv(RESULTS/"mcmc_parameter_diagnostics.csv",index=False)

print("Maximum split R-hat:",diag["split_rhat"].max())


# ---- notebook cell 12 ----
# ArviZ ESS can still be calculated variable-by-variable; if the local
# ArviZ/xarray combination rejects it, this diagnostic is recorded as unavailable.
ess_rows=[]
try:
    for name in ["intercept","sigma_spatial","sigma_iid","alpha_pymc"]:
        val=float(np.asarray(az.ess(post[name],method="bulk")).squeeze())
        ess_rows.append({"parameter":name,"ess_bulk":val})
    for j,name in enumerate(PREDICTORS):
        da=post["beta"].isel(predictor=j)
        val=float(np.asarray(az.ess(da,method="bulk")).squeeze())
        ess_rows.append({"parameter":f"beta[{name}]","ess_bulk":val})
    ess_df=pd.DataFrame(ess_rows)
    print(ess_df)
    ess_df.to_csv(RESULTS/"mcmc_ess.csv",index=False)
except Exception as e:
    print("ESS unavailable because of local ArviZ compatibility:",repr(e))


# ---- notebook cell 14 ----
beta=post["beta"]

def original_draws(name):
    j=PREDICTORS.index(name)
    return np.asarray(beta.isel(predictor=j).values,float)/float(sds[name])

veg=original_draws("veg_pct")
sha=original_draws("shadow_pct")

env=pd.DataFrame([
    basic_row("vegetation",veg),
    basic_row("shadow",sha),
])
env["nonspatial_beta"]=[bveg,bsha]
env["effect_per_10pp_pct"]=100*(np.exp(10*env["mean"])-1)
env["change_vs_nonspatial_pct"]=(env["mean"]-env["nonspatial_beta"])/env["nonspatial_beta"].abs()*100
print(env)
env.to_csv(RESULTS/"environmental_mcmc_comparison.csv",index=False)


# ---- notebook cell 16 ----
# Avoid storing/processing all 45,004 fitted-value draws at once.
inter=np.asarray(post["intercept"].values,float)
bd=np.asarray(post["beta"].values,float)
ph=np.asarray(post["phi"].values,float)
th=np.asarray(post["theta"].values,float)
ap=np.asarray(post["alpha_pymc"].values,float)

mu_acc=np.zeros(len(d),float)
ns=0
for c in range(inter.shape[0]):
    for q in range(inter.shape[1]):
        eta=(inter[c,q] + Z@bd[c,q] +
             ph[c,q,block_idx] + th[c,q,block_idx])
        mu_acc += np.exp(eta)
        ns += 1
mu_mean=mu_acc/ns
alpha_mean=float(ap.mean())

pearson=(y-mu_mean)/np.sqrt(mu_mean+mu_mean**2/alpha_mean)

xy=np.column_stack([xx,yy])
pairs=cKDTree(xy).query_pairs(70.72,output_type="ndarray")
ii=np.r_[pairs[:,0],pairs[:,1]]
jj=np.r_[pairs[:,1],pairs[:,0]]
Ws=sp.csr_matrix((np.ones(len(ii)),(ii,jj)),shape=(len(d),len(d)))
deg=np.asarray(Ws.sum(axis=1)).ravel()
Wr=sp.diags(1/np.maximum(deg,1))@Ws

def moran_i(z):
    z=np.asarray(z,float); z=z-z.mean()
    return len(z)/float(Wr.sum())*(z@(Wr@z))/(z@z)

moran=float(moran_i(pearson))
print("MCMC spatial-model residual Moran I:",moran)
print("Non-spatial reference:",0.05260)
print("ADVI V3 reference: approximately 0.0297")


# ---- notebook cell 18 ----
# Sampler diagnostics exposed by PyMC
sample_stats=idata.sample_stats
divergences=int(np.asarray(sample_stats["diverging"]).sum()) if "diverging" in sample_stats else -1
max_rhat=float(diag["split_rhat"].max())

report={
    "n_cells":int(len(d)),
    "vehicle_crimes":int(y.sum()),
    "blocks_1km":int(B),
    "block_edges":int(W.sum()//2),
    "draws_per_chain":DRAWS,
    "tune_per_chain":TUNE,
    "chains":2,
    "elapsed_minutes":float(elapsed),
    "divergences":divergences,
    "max_split_rhat_fixed_and_scale_parameters":max_rhat,
    "residual_moran_70_72m":moran,
    "nonspatial_moran_reference":0.05260,
    "advi_moran_reference_approx":0.0297,
}
with open(RESULTS/"mcmc_diagnostics.json","w",encoding="utf-8") as f:
    json.dump(report,f,indent=2)

# Save posterior only; omit mu to keep the NetCDF much smaller.
# xarray Dataset.to_netcdf is used directly for compatibility with recent
# ArviZ/xarray DataTree APIs. This serialization step does not affect inference.
keep=["intercept","beta","sigma_spatial","sigma_iid","alpha_pymc"]
try:
    post[keep].to_netcdf(RESULTS/"posterior_fixed_scale.nc")
    print("Saved posterior_fixed_scale.nc")
except Exception as e:
    print("NetCDF save skipped (posterior summaries remain saved):",repr(e))

print("\nDONE.")
print("Results folder:",RESULTS)
print("Compress this folder as ZIP and upload it.")
