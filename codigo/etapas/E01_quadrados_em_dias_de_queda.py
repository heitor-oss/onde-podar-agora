"""
Dado um temporal, onde caem as árvores · E01 — Dias de queda por quadrado de 1 km
Tipo: principal

O que faz:
    Monta, para cada dia com 20+ quedas, as variáveis de cada quadrado de 1 km (histórico,
    pedidos recentes, chuva das estações próximas).

Lê:
    estacoes_diario.pkl, full.pkl
Grava:
    q2_rows.pkl
Usado em:
    Pergunta "dado um temporal, onde caem as árvores".
Script original da análise: q2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle
from sklearn.linear_model import PoissonRegressor
df=pd.read_pickle('full.pkl'); df=df[df.latitude_usada.notna()].copy()
df['ini']=pd.to_datetime(df.data_inicio); df['d']=df.ini.dt.normalize(); df['fim']=pd.to_datetime(df.data_fim,errors='coerce')
df=df[(df.latitude_usada.between(-23.1,-22.73))&(df.longitude_usada.between(-43.8,-43.09))]
df['gx']=((df.longitude_usada+43.8)*102.5).astype(int); df['gy']=((df.latitude_usada+23.1)*110.6).astype(int)
df['cell']=df.gx*100+df.gy
df['queda']=df.subtipo=='Retirada de árvore caída'
cells=np.sort(df.cell.unique()); cidx={c:i for i,c in enumerate(cells)}; df['ci']=df.cell.map(cidx); NC=len(cells)
days=pd.date_range(df.d.min(),df.d.max()); D=len(days); df['di']=(df.d-days[0]).dt.days
def mat(m):
    M=np.zeros((NC,D),np.int32); np.add.at(M,(df.ci.values[m],df.di.values[m]),1); return M
A=mat(np.ones(len(df),bool)); Qm=mat(df.queda.values); PR=A-Qm
cf=Qm.sum(0)
EV=[d for d in np.where(cf>=20)[0] if d>=120]
print('event days',len(EV),'quedas',cf[EV].sum(), 'cells',NC)
cA=np.cumsum(A,1); cQ=np.cumsum(Qm,1); cP=np.cumsum(PR,1)
evmask=np.zeros(D,bool); evmask[np.where(cf>=20)[0]]=True
Qev=Qm*evmask[None,:]; cQev=np.cumsum(Qev,1)
# backlog: preventive requests not resolved: open at s OR not attended (closed without service) in previous 365 days
pv=df[~df.queda]
pv_ini=pv.di.values; pv_fimd=((pv.fim.dt.normalize()-days[0]).dt.days).fillna(10**6).values
pv_na=pv.tipo_situacao.isin(['Não atendido']).values; pv_ci=pv.ci.values
# station rain
st=pd.read_pickle('estacoes_diario.pkl')
cx=(cells//100+0.5)/102.5-43.8; cy=(cells%100+0.5)/110.6-23.1
def rain_cells(dt):
    s=st[st.data.isin([dt,dt-pd.Timedelta(days=1)])].groupby('sid').agg(m=('max1h','max'),la=('latitude','first'),lo=('longitude','first'))
    if len(s)<15: return None
    dx=(cx[:,None]-s.lo.values[None,:])*102.5; dy=(cy[:,None]-s.la.values[None,:])*110.6
    d2=dx**2+dy**2+0.25; w=1/d2
    k=np.argsort(d2,1)[:,:4]; ww=np.take_along_axis(w,k,1)
    return (np.take_along_axis(np.broadcast_to(s.m.values,(NC,len(s))),k,1)*ww).sum(1)/ww.sum(1)
rows=[]
for s in EV:
    act=cA[:,s-1]>0
    hist_all=cA[:,s-1]; hist_q=cQ[:,s-1]; hist_qev=cQev[:,s-1]
    rec30=cP[:,s-1]-cP[:,s-31]; rec7=cP[:,s-1]-cP[:,s-8]
    m=(pv_ini<s)&(((pv_fimd>=s))|(pv_na&(pv_ini>=s-365)))
    back=np.bincount(pv_ci[m],minlength=NC)
    r=rain_cells(days[s])
    y=Qm[:,s]
    rows.append(dict(s=s,act=act,X=np.c_[hist_all,hist_q,hist_qev,rec30,rec7,back],rain=r,y=y))
pickle.dump(dict(rows=rows,cells=cells,days=days,cx=cx,cy=cy,NC=NC),open('q2_rows.pkl','wb'))
print('events with station rain',sum(r['rain'] is not None for r in rows))
