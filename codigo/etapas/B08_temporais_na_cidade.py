"""
Picos de chamados por CEP · B08 — Como começam os temporais
Tipo: principal

O que faz:
    Para cada temporal (40+ quedas), mostra o comportamento da cidade nos dias anteriores e
    a hora em que se chega a 10 quedas.

Lê:
    ev.pkl, full.pkl, mats.npz
Grava:
    city.json
Usado em:
    Página de picos.
Script original da análise: a8.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
z=np.load('mats.npz',allow_pickle=True); ALL=z['ALL']; FALL=z['FALL']
days=pd.DatetimeIndex(z['days']); D=len(days)
print('active ceps',(ALL.sum(1)>0).sum(), 'test days',(days>=pd.Timestamp('2025-01-01')).sum())
city=ALL.sum(0).astype(int); cf=FALL.sum(0).astype(int)
storm=np.where(cf>=40)[0]
# pre-storm city behaviour: days -7..-1 relative to the first day of each storm cluster
first=[s for s in storm if not ((s-1) in storm or (s-2) in storm)]
print('storm clusters',len(first))
ks=range(-14,4)
med_cf=np.median(cf); med_city=np.median(city)
curve=[float(np.mean([cf[s+k] for s in first if 0<=s+k<D])) for k in ks]
curve_t=[float(np.mean([city[s+k] for s in first if 0<=s+k<D])) for k in ks]
print(list(zip(ks,np.round(curve,1))), med_cf)
print(list(zip(ks,np.round(curve_t,1))), med_city)
df=pd.read_pickle('full.pkl'); df['ts']=pd.to_datetime(df.data_inicio)
f=df[df.subtipo=='Retirada de árvore caída']
sd=set(days[first])
hh=[]
for s in first:
    day=days[s]; x=f[f.d==day].ts.dt.hour
    cnt=np.bincount(x,minlength=24).cumsum()
    hit=np.argmax(cnt>=10) if cnt[-1]>=10 else None
    hh.append(dict(dia=str(day.date()),quedas=int(cf[s]),total=int(city[s]),hora_10_quedas=int(hit) if hit is not None else None, quedas_dia_ant=int(cf[s-1])))
print(pd.DataFrame(hh))
# emergency events: spread within day
ev=pd.read_pickle('ev.pkl')
print('hspan median',ev.hspan.median(), (ev.hspan>=3).mean())
# daily series for chart (weekly)
ser=pd.DataFrame({'d':days,'tot':city,'queda':cf}).set_index('d').resample('W').sum()
json.dump(dict(storm=hh,pre_curve=dict(ks=list(ks),queda=curve,tot=curve_t,med_queda=float(med_cf),med_tot=float(med_city)),
  weekly=dict(d=[str(x.date()) for x in ser.index],tot=ser.tot.tolist(),queda=ser.queda.tolist())),open('city.json','w'))
