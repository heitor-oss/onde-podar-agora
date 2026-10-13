"""
Cobertura de árvores · G01 — Setores censitários em dias de queda
Tipo: principal

O que faz:
    Monta matrizes por setor censitário e as variáveis de árvore e ocupação de cada setor.

Lê:
    full.pkl, setor censitário (dados_entrada)
Grava:
    t1_mats.npz, t1_rows.pkl
Usado em:
    Pergunta sobre cobertura de árvores.
Script original da análise: t1.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json, pickle
from sklearn.linear_model import PoissonRegressor
S=pd.read_csv(SETOR)
S=S.sort_values('cd_setor').reset_index(drop=True); NS=len(S); sidx={c:i for i,c in enumerate(S.cd_setor)}
df=pd.read_pickle('full.pkl'); df=df[df.cd_setor.notna()].copy(); df['si']=df.cd_setor.astype('int64').map(sidx); df=df[df.si.notna()]; df['si']=df.si.astype(int)
df['d']=pd.to_datetime(df.data_inicio).dt.normalize(); days=pd.date_range('2022-09-01','2026-09-20'); D=len(days); df['di']=(df.d-days[0]).dt.days
q=(df.subtipo=='Retirada de árvore caída').values
def mat(m):
    M=np.zeros((NS,D),np.float32); np.add.at(M,(df.si.values[m],df.di.values[m]),1); return M
A=mat(np.ones(len(df),bool)); Q=mat(q)
cA=np.concatenate([np.zeros((NS,1),np.float32),A.cumsum(1)],1); cQ=np.concatenate([np.zeros((NS,1),np.float32),Q.cumsum(1)],1)
static=np.c_[S.arvore_urbana, S.arvore, S.construido, S.peso_urbano, np.log(S.area_km2.clip(lower=1e-4)), S.log_pop]
static_names=['arvore_urbana','arvore','construido','peso_urbano','log_area','log_pop']
cf=Q.sum(0); EV=[d for d in np.where(cf>=20)[0] if d>=120]
print('setores',NS,'eventos',len(EV),'quedas em eventos',cf[EV].sum())
rows=[]
for s in EV:
    X=np.c_[cA[:,s],cQ[:,s],cA[:,s]-cA[:,max(s-30,0)],cA[:,s]-cA[:,max(s-365,0)]]
    rows.append(dict(s=s,X=X,y=Q[:,s]))
pickle.dump(dict(rows=rows,static=static,S=S[['cd_setor','bairro','regiao_adm','area_km2','total_de_p','arvore_urbana','arvore','construido']]),open('t1_rows.pkl','wb'))
# also total-period matrices for later
np.savez_compressed('t1_mats.npz',A=A,Q=Q)
