"""
Prontidão em dias de temporal (modelo 3) · F01 — Matrizes quadrado × dia
Tipo: principal

O que faz:
    Conta, para cada quadrado de 1 km e dia, todos os chamados, as quedas, os pedidos e os
    pedidos ainda abertos.

Lê:
    full.pkl, q2_rows.pkl
Grava:
    q7mats.npz
Usado em:
    Modelo 3.
Script original da análise: q7prep.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle
df=pd.read_pickle('full.pkl'); df=df[df.latitude_usada.notna()].copy()
df=df[(df.latitude_usada.between(-23.1,-22.73))&(df.longitude_usada.between(-43.8,-43.09))]
df['ini']=pd.to_datetime(df.data_inicio); df['d']=df.ini.dt.normalize(); df['fim']=pd.to_datetime(df.data_fim,errors='coerce')
df['cell']=((df.longitude_usada+43.8)*102.5).astype(int)*100+((df.latitude_usada+23.1)*110.6).astype(int)
Z=pickle.load(open('q2_rows.pkl','rb')); cells=Z['cells']; NC=len(cells); cidx={c:i for i,c in enumerate(cells)}
df['ci']=df.cell.map(cidx)
days=pd.date_range('2022-09-01','2026-09-20'); D=len(days); df['di']=(df.d-days[0]).dt.days
def mat(m):
    M=np.zeros((NC,D),np.float32); np.add.at(M,(df.ci.values[m],df.di.values[m]),1); return M
Q=df.subtipo.eq('Retirada de árvore caída').values
A=mat(np.ones(len(df),bool)); QM=mat(Q); PR=A-QM; RK=mat(df.subtipo.eq('Avaliação de risco de queda da árvore').values)
# backlog: preventive requests active (not resolved) for up to 365 days
pv=df[~Q]; endd=np.where(pv.tipo_situacao.isin(['Atendido','Atendido parcialmente']).values & pv.fim.notna().values,
                       ((pv.fim.dt.normalize()-days[0]).dt.days).fillna(0).values, pv.di.values+365)
endd=np.minimum(np.maximum(endd,pv.di.values+1),pv.di.values+365).astype(int)
B=np.zeros((NC,D+400),np.float32); np.add.at(B,(pv.ci.values,pv.di.values),1); np.add.at(B,(pv.ci.values,endd),-1)
BK=np.cumsum(B,1)[:,:D]
np.savez_compressed('q7mats.npz',A=A,QM=QM,PR=PR,RK=RK,BK=BK)
print(NC,D,QM.sum(),BK.max())
