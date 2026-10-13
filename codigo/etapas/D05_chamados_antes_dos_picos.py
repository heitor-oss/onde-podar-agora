"""
Em quanto tempo um pedido vira emergência · D05 — Pedidos no CEP antes dos picos emergenciais
Tipo: principal

O que faz:
    Fração dos picos com pedido não emergencial no CEP 3, 7, 30 e 90 dias antes, comparada
    com o ano anterior.

Lê:
    ev.pkl, mats.npz
Grava:
    nada (só imprime resultados)
Usado em:
    Mesma pergunta.
Script original da análise: q1e.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
z=np.load('mats.npz',allow_pickle=True); ALL=z['ALL'].astype(np.int32); FALL=z['FALL'].astype(np.int32); D=ALL.shape[1]
NONQ=ALL-FALL
ev=pd.read_pickle('ev.pkl'); ev=ev[ev.di>=730]
cum=np.concatenate([np.zeros((NONQ.shape[0],1),np.int32),NONQ.cumsum(1)],1)
for a,b in [(1,3),(1,7),(1,30),(1,90)]:
    real=(cum[ev.ci,ev.di-a+1]-cum[ev.ci,ev.di-b]>0).mean()
    pl=(cum[ev.ci,ev.di-365-a+1]-cum[ev.ci,ev.di-365-b]>0).mean()
    print((a,b),round(real,3),round(pl,3))
# lag to most recent non-queda request in CEP
lags=[]
for ci,di in zip(ev.ci,ev.di):
    r=np.nonzero(NONQ[ci,:di])[0]
    lags.append(di-r[-1] if len(r) else np.nan)
print(pd.Series(lags).describe(percentiles=[.25,.5,.75]))
