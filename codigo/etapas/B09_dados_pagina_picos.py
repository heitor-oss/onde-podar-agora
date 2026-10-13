"""
Picos de chamados por CEP · B09 — Dados da página "Picos de chamados por CEP"
Tipo: principal

O que faz:
    Reúne os resultados anteriores num JSON para a página.

Lê:
    cepday.pkl, city.json, ev.pkl, full.pkl, mats.npz, model_lr.json, prof.json,
    selfctl.json, vol.pkl
Grava:
    data.json
Usado em:
    Página de picos.
Script original da análise: a9.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
ev=pd.read_pickle('ev.pkl'); vol=pd.read_pickle('vol.pkl'); g=pd.read_pickle('cepday.pkl')
prof=json.load(open('prof.json')); selfc=json.load(open('selfctl.json')); lr=json.load(open('model_lr.json')); city=json.load(open('city.json'))
z=np.load('mats.npz',allow_pickle=True); ALL=z['ALL']; days=pd.DatetimeIndex(z['days'])
peaks=[]
for E,cl in [(ev,'Emergencial'),(vol[vol.tipo=='Mutirão'],'Mutirão'),(vol[vol.tipo=='Lote'],'Lote')]:
    for r in E.itertuples():
        di=r.di; pre30=int(ALL[r.ci,max(0,di-30):max(0,di-2)].sum()); pre365=int(ALL[r.ci,max(0,di-365):di].sum())
        peaks.append(dict(c=cl,cep=f'{int(r.cep):08d}',d=str(r.d.date()),n=int(r.n),p=int(r.pts),q=int(r.fall),b=r.bairro,r=r.rua,
                          la=round(float(r.lat),4) if pd.notna(r.lat) else None,lo=round(float(r.lon),4) if pd.notna(r.lon) else None,pre30=pre30,pre365=pre365))
df=pd.read_pickle('full.pkl')
bg=df[['latitude_usada','longitude_usada']].dropna()
bg=bg[(bg.latitude_usada.between(-23.1,-22.73))&(bg.longitude_usada.between(-43.8,-43.09))]
bg=bg.sample(9000,random_state=0).round(4).values.tolist()
def wk(res):
    ks=np.array(res['ks']); cur=np.array(res['cur']); ctl=np.array(res['ctl'])
    out=[]
    for a in range(-63,0,7): m=(ks>=a)&(ks<a+7); out.append(dict(w=a//7,ev=cur[m].mean(),ct=ctl[m].mean()))
    d0=float(cur[ks==0][0])
    for a in range(1,57,7): m=(ks>=a)&(ks<a+7); out.append(dict(w=(a+6)//7,ev=cur[m].mean(),ct=ctl[m].mean()))
    return out,d0
curves={k:dict(zip(['w','d0'],wk(v))) for k,v in prof.items()}
for k in curves: curves[k]['self']=selfc[k]['selfbase']/28; curves[k]['n']=prof[k]['n']
out=dict(peaks=peaks,bg=bg,curves=curves,selfc=selfc,prof={k:v['win'] for k,v in prof.items()},lr=lr,city=city,
  kpi=dict(chamados=int(len(df)),ceps=int(df.cep.nunique()),cepdays=int(len(g)),one=float((g.n==1).mean()),n5=int((g.n>=5).sum()),n10=int((g.n>=10).sum()),n20=int((g.n>=20).sum()),
           ini=str(days[0].date()),fim=str(days[-1].date()),test_days=628,active=15967))
json.dump(out,open('data.json','w'),ensure_ascii=False,separators=(',',':'),default=float)
import os; print(os.path.getsize('data.json'))
print(json.dumps(curves,default=float)[:1500])
