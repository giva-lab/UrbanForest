# Auto-extracted from spatial_nb_bym_subtypes_v6_corrected.ipynb


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

print("NumPy:", np.__version__)
print("SciPy:", scipy.__version__)
print("Statsmodels:", statsmodels.__version__)
print("PyMC:", pm.__version__)
print("PyTensor:", pytensor.__version__)


# ---- notebook cell 2 ----
BASE=Path.cwd()
GPKG=BASE/"audit_cells.gpkg"
assert GPKG.exists(), f"Missing: {GPKG}"

# Accept the original filename or a Windows/download duplicate such as ...(2).csv
crime_candidates = [
    BASE/"vei_sp_2024_clean.csv",
    BASE/"vei_sp_2024_clean(2).csv",
]
crime_candidates += sorted(BASE.glob("vei_sp_2024_clean*.csv"))
CRIMES = next((p for p in crime_candidates if p.exists()), None)
assert CRIMES is not None, "Missing vei_sp_2024_clean*.csv in the notebook folder."

RESULTS=BASE/"spatial_bym_subtypes_results"
RESULTS.mkdir(exist_ok=True)

print("Grid:", GPKG)
print("Crimes:", CRIMES)
print("Results:", RESULTS)


# ---- notebook cell 4 ----
g=gpd.read_file(GPKG)

road_classes=["class_ARTERIAL","class_COLETORA","class_RODOVIA",
              "class_VIA DE PEDESTRES","class_VTR"]
for c in road_classes:
    g[c+"_share"]=g[c]/g["road_m"].replace(0,np.nan)
g["log_road_m"]=np.log1p(g["road_m"])

ENV=["veg_pct","shadow_pct"]
CONTROLS=["infrastructure_index","high_income","streetlight",
          "schools_r500m","transport_hubs_r500m","police_station_r500m",
          "private_parking_r500m","paid_parking_distance",
          "moradores","distancia_marco_zero"]
ROADS=["log_road_m","class_ARTERIAL_share","class_COLETORA_share",
       "class_RODOVIA_share","class_VIA DE PEDESTRES_share","class_VTR_share"]
PREDICTORS=ENV+CONTROLS+ROADS

# EXACT reconstruction already validated in the earlier sensitivity notebook
cr=pd.read_csv(CRIMES,sep=";",low_memory=False)
assert len(cr)==100306, f"Unexpected crime CSV size: {len(cr)}"
cr=cr[cr["RUBRICA"].isin(["Furto (art. 155)","Roubo (art. 157)"])].copy()

pts=gpd.GeoDataFrame(
    cr[["RUBRICA"]].copy(),
    geometry=gpd.points_from_xy(cr["LONGITUDE"],cr["LATITUDE"]),
    crs="EPSG:4326",
).to_crs(g.crs)

joined=gpd.sjoin(
    pts,
    g[["id","geometry"]],
    predicate="within",
    how="inner"
)

ct=pd.crosstab(joined["id"],joined["RUBRICA"])

g["theft_n"]=g["id"].map(
    ct.get("Furto (art. 155)",pd.Series(dtype=int))
).fillna(0).astype(int)

g["robbery_n"]=g["id"].map(
    ct.get("Roubo (art. 157)",pd.Series(dtype=int))
).fillna(0).astype(int)

d=g[g["complete"]==True].copy().reset_index(drop=True)

# Hard gatekeeper: MCMC cannot start unless the reconstruction is exactly the validated one.
mismatch=int(((d["theft_n"]+d["robbery_n"])!=d["veiculo_n"]).sum())
print("N =",len(d))
print("Theft =",int(d["theft_n"].sum()))
print("Robbery =",int(d["robbery_n"].sum()))
print("Aggregate =",int(d["veiculo_n"].sum()))
print("Cell-level mismatches =",mismatch)

assert len(d)==45004
assert int(d["theft_n"].sum())==12172
assert int(d["robbery_n"].sum())==2533
assert int(d["veiculo_n"].sum())==14705
assert mismatch==0
print("RECONSTRUCTION VALIDATION PASSED")

Xraw=d[PREDICTORS].astype(float)
means=Xraw.mean()
sds=Xraw.std(ddof=0)
Z=((Xraw-means)/sds).to_numpy(float)
X=np.column_stack([np.ones(len(d)),Z])

THEFT_COL="theft_n"
ROBBERY_COL="robbery_n"


# ---- notebook cell 6 ----
print("Theft outcome:", THEFT_COL, "|", int(d[THEFT_COL].sum()))
print("Robbery outcome:", ROBBERY_COL, "|", int(d[ROBBERY_COL].sum()))
print("Subtype outcomes ready for MCMC.")


# ---- notebook cell 8 ----
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
assert B==204, f"Expected 204 blocks, got {B}"

coords_block=np.array(unique_keys)
W=np.zeros((B,B),dtype="int8")
for i in range(B):
    dx=np.abs(coords_block[:,0]-coords_block[i,0])
    dy=np.abs(coords_block[:,1]-coords_block[i,1])
    neigh=(dx<=1)&(dy<=1)&~((dx==0)&(dy==0))
    W[i,neigh]=1
W=np.maximum(W,W.T)
assert (W.sum(axis=1)==0).sum()==0
print("Blocks:",B,"edges:",int(W.sum()//2))


# ---- notebook cell 10 ----
def split_rhat(a):
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

xy=np.column_stack([xx,yy])
pairs=cKDTree(xy).query_pairs(70.72,output_type="ndarray")
ii=np.r_[pairs[:,0],pairs[:,1]]
jj=np.r_[pairs[:,1],pairs[:,0]]
Ws=sp.csr_matrix((np.ones(len(ii)),(ii,jj)),shape=(len(d),len(d)))
deg=np.asarray(Ws.sum(axis=1)).ravel()
Wr=sp.diags(1/np.maximum(deg,1))@Ws

def moran_i(z):
    z=np.asarray(z,float)
    z=z-z.mean()
    return len(z)/float(Wr.sum())*(z@(Wr@z))/(z@z)

def qrow(label,a):
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


# ---- notebook cell 11 ----
def run_subtype(label,outcome_col,seed):
    y=d[outcome_col].to_numpy(int)
    print("\n"+"="*72)
    print(label.upper(), "| events =",int(y.sum()))

    pois=Poisson(y,X).fit(method="bfgs",disp=False,maxiter=150)
    start=np.r_[pois.params,5.0]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        nb=NegativeBinomial(y,X,loglike_method="nb2").fit(
            start_params=start,method="bfgs",maxiter=350,gtol=2e-6,disp=False)

    assert nb.mle_retvals.get("converged",False), f"{label}: NB2 failed."
    bveg=float(nb.params[1]/sds["veg_pct"])
    bsha=float(nb.params[2]/sds["shadow_pct"])
    alpha_freq=float(nb.params[-1])
    print("NB2 vegetation =",bveg)
    print("NB2 shadow =",bsha)
    print("NB2 alpha =",alpha_freq," AIC =",float(nb.aic))

    coords={"obs":np.arange(len(d)),"predictor":PREDICTORS,"block":np.arange(B)}
    beta_start=nb.params[1:-1].copy()
    intercept_start=float(nb.params[0])

    with pm.Model(coords=coords) as model:
        X_data=pm.Data("X",Z,dims=("obs","predictor"))
        block_data=pm.Data("block_idx",block_idx,dims="obs")
        intercept=pm.Normal("intercept",mu=intercept_start,sigma=1.0)
        beta=pm.Normal("beta",mu=beta_start,sigma=0.5,dims="predictor")
        sigma_spatial=pm.HalfNormal("sigma_spatial",sigma=0.5)
        sigma_iid=pm.HalfNormal("sigma_iid",sigma=0.5)
        phi_raw=pm.ICAR("phi_raw",W=W,sigma=1.0,dims="block")
        phi=pm.Deterministic("phi",sigma_spatial*phi_raw,dims="block")
        theta_raw=pm.Normal("theta_raw",0,1,dims="block")
        theta=pm.Deterministic("theta",sigma_iid*theta_raw,dims="block")
        log_alpha=pm.Normal("log_alpha",mu=np.log(1/alpha_freq),sigma=.75)
        alpha_pymc=pm.Deterministic("alpha_pymc",pm.math.exp(log_alpha))
        eta=intercept+pm.math.dot(X_data,beta)+phi[block_data]+theta[block_data]
        pm.NegativeBinomial("obs_count",mu=pm.math.exp(eta),alpha=alpha_pymc,
                            observed=y,dims="obs")

    t0=time.time()
    with model:
        idata=pm.sample(
            draws=1000,tune=1000,chains=2,cores=1,
            random_seed=[seed,seed+1000],
            target_accept=.95,
            init="jitter+adapt_diag",
            return_inferencedata=True,
            progressbar=False,
            compute_convergence_checks=False,
            idata_kwargs={"log_likelihood":False},
        )
    elapsed=(time.time()-t0)/60
    print(f"MCMC completed in {elapsed:.1f} min")

    post=idata.posterior
    rows=[]
    for name in ["intercept","sigma_spatial","sigma_iid","alpha_pymc"]:
        rows.append(qrow(name,post[name].values))
    for j,name in enumerate(PREDICTORS):
        rows.append(qrow(f"beta[{name}]",post["beta"].isel(predictor=j).values))
    diag=pd.DataFrame(rows)

    veg=np.asarray(post["beta"].isel(predictor=PREDICTORS.index("veg_pct")).values,float)/float(sds["veg_pct"])
    sha=np.asarray(post["beta"].isel(predictor=PREDICTORS.index("shadow_pct")).values,float)/float(sds["shadow_pct"])
    env=pd.DataFrame([qrow("vegetation",veg),qrow("shadow",sha)])
    env["nonspatial_beta"]=[bveg,bsha]
    env["effect_per_10pp_pct"]=100*(np.exp(10*env["mean"])-1)

    # posterior mean fitted values without storing observation-level draws
    inter=np.asarray(post["intercept"].values,float)
    bd=np.asarray(post["beta"].values,float)
    ph=np.asarray(post["phi"].values,float)
    th=np.asarray(post["theta"].values,float)
    ap=np.asarray(post["alpha_pymc"].values,float)
    mu_acc=np.zeros(len(d),float); ns=0
    for c in range(inter.shape[0]):
        for q in range(inter.shape[1]):
            eta=inter[c,q]+Z@bd[c,q]+ph[c,q,block_idx]+th[c,q,block_idx]
            mu_acc+=np.exp(eta); ns+=1
    mu_mean=mu_acc/ns
    alpha_mean=float(ap.mean())
    pearson=(y-mu_mean)/np.sqrt(mu_mean+mu_mean**2/alpha_mean)
    moran=float(moran_i(pearson))

    divergences=int(np.asarray(idata.sample_stats["diverging"]).sum())
    report={
        "outcome":label,
        "outcome_column":outcome_col,
        "events":int(y.sum()),
        "elapsed_minutes":float(elapsed),
        "divergences":divergences,
        "max_split_rhat_fixed_and_scale":float(diag["split_rhat"].max()),
        "residual_moran_70_72m":moran,
        "nb2_vegetation":bveg,
        "nb2_shadow":bsha,
        "spatial_vegetation":float(veg.mean()),
        "spatial_shadow":float(sha.mean()),
    }

    diag.to_csv(RESULTS/f"{label}_diagnostics.csv",index=False)
    env.to_csv(RESULTS/f"{label}_environmental.csv",index=False)
    with open(RESULTS/f"{label}_report.json","w",encoding="utf-8") as f:
        json.dump(report,f,indent=2)

    print(env)
    print("Residual Moran I =",moran)
    print("Divergences =",divergences,
          "| max split R-hat =",float(diag["split_rhat"].max()))
    return report,env,diag


# ---- notebook cell 13 ----
theft_report,theft_env,theft_diag=run_subtype("theft",THEFT_COL,12345)


# ---- notebook cell 15 ----
robbery_report,robbery_env,robbery_diag=run_subtype("robbery",ROBBERY_COL,54321)


# ---- notebook cell 17 ----
comparison=pd.concat([
    theft_env.assign(outcome="vehicle theft"),
    robbery_env.assign(outcome="vehicle robbery")
],ignore_index=True)

comparison=comparison[
    ["outcome","parameter","nonspatial_beta","mean","sd",
     "q2.5","median","q97.5","effect_per_10pp_pct","split_rhat"]
]
print(comparison)
comparison.to_csv(RESULTS/"subtype_spatial_comparison.csv",index=False)

reports=pd.DataFrame([theft_report,robbery_report])
print(reports)
reports.to_csv(RESULTS/"subtype_model_reports.csv",index=False)

print("\nDONE.")
print("Results folder:",RESULTS)
print("Compress the entire folder and upload the ZIP.")
