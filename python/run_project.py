from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'/'india_ecommerce_market.csv'
REPORT=ROOT/'reports'; FIG=REPORT/'figures'; TABLES=REPORT/'tables'
for p in (FIG,TABLES): p.mkdir(parents=True,exist_ok=True)
df=pd.read_csv(DATA)
total=df[df.market_scope.eq('India total e-commerce')].sort_values('year').copy()
total['yoy_growth_percent']=total.market_value_usd_bn.pct_change()*100
total.to_csv(TABLES/'india_market_growth.csv',index=False)
scenarios=[]
for label,cagr in [('Conservative',.08),('Base',.12),('Optimistic',.16)]:
 for year in range(2024,2036):
  tam=27*(1+cagr)**(year-2024)
  scenarios.append({'year':year,'scenario':label,'assumed_cagr_percent':cagr*100,'tam_usd_bn':tam,'illustrative_sam_usd_bn':tam*.30})
sc=pd.DataFrame(scenarios); sc.to_csv(TABLES/'tam_sam_scenarios.csv',index=False)
sens=[]
for rate in [.06,.08,.10,.12,.14,.16,.18]:
 for share in [.20,.25,.30,.35,.40]:
  tam=27*(1+rate)**6; sens.append({'growth_percent':rate*100,'sam_reachability_percent':share*100,'tam_2030_usd_bn':tam,'sam_2030_usd_bn':tam*share})
pd.DataFrame(sens).to_csv(TABLES/'sensitivity_2030.csv',index=False)

def save(name,title,xlabel,ylabel):
 plt.title(title); plt.xlabel(xlabel); plt.ylabel(ylabel); plt.grid(alpha=.25); plt.tight_layout(); plt.savefig(FIG/name,dpi=180); plt.close()
fig,ax=plt.subplots(figsize=(9,5)); h=total[total.status.eq('Reported')]; f=total[total.status.eq('Forecast')]
ax.plot(h.year,h.market_value_usd_bn,'o-',label='Reported'); ax.plot(f.year,f.market_value_usd_bn,'o--',label='Published forecast'); ax.legend(); save('01_market_growth.png','India e-commerce market: reported and forecast','Year','USD billion')
fig,ax=plt.subplots(figsize=(9,5)); g=total.dropna(subset=['yoy_growth_percent']); ax.bar(g.year.astype(str),g.yoy_growth_percent); save('02_annual_growth.png','Year-on-year growth between available observations','Year','Growth (%)')
cat=df[(df.year.eq(2024)) & (~df.market_scope.eq('India total e-commerce'))]
fig,ax=plt.subplots(figsize=(9,5)); ax.bar(cat.market_scope,cat.market_value_usd_bn); ax.tick_params(axis='x',rotation=18); save('03_category_benchmarks.png','2024 online category benchmarks','Category','USD billion')
fig,ax=plt.subplots(figsize=(9,5))
for label,group in sc.groupby('scenario'): ax.plot(group.year,group.tam_usd_bn,label=label)
ax.legend(); save('04_tam_scenarios.png','Electronics and appliances TAM scenarios','Year','USD billion')
base=sc[sc.scenario.eq('Base')]
fig,ax=plt.subplots(figsize=(9,5)); ax.plot(base.year,base.tam_usd_bn,label='TAM'); ax.plot(base.year,base.illustrative_sam_usd_bn,label='Illustrative SAM'); ax.legend(); save('05_tam_sam.png','Base-case TAM and illustrative SAM','Year','USD billion')
piv=pd.DataFrame(sens).pivot(index='growth_percent',columns='sam_reachability_percent',values='sam_2030_usd_bn')
fig,ax=plt.subplots(figsize=(8,5)); im=ax.imshow(piv,aspect='auto'); ax.set_xticks(range(len(piv.columns)),piv.columns); ax.set_yticks(range(len(piv.index)),piv.index); ax.set_xlabel('SAM reachability (%)'); ax.set_ylabel('Annual growth (%)'); ax.set_title('2030 SAM sensitivity (USD bn)'); fig.colorbar(im,ax=ax); fig.tight_layout(); fig.savefig(FIG/'06_sensitivity_heatmap.png',dpi=180); plt.close(fig)
print(f'Created {len(list(FIG.glob("*.png")))} PNG charts and {len(list(TABLES.glob("*.csv")))} CSV tables in {REPORT}')
print('No transaction histogram or consumer segmentation is generated without real observations.')
