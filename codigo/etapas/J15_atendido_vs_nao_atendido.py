"""
Ranking "Onde podar agora" · J15 — Atender a tempo reduz as quedas?
Tipo: principal

O que faz:
    Compara, na mesma faixa de nota, lugares onde a maior parte dos pedidos foi atendida em
    até 3 meses com lugares sem atendimento.

Lê:
    df.pkl, pri_roll.pkl
Grava:
    nada (só imprime resultados)
Usado em:
    Página: "Atender a tempo reduz as quedas".
Script original da análise: light/served.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle
O=pickle.load(open('pri_roll.pkl','rb'))
L=lambda v,cap: np.clip(np.log1p(v)/np.log1p(cap),0,1)
w=np.array([25,15,40,10,10])
def sc(g): return pd.Series(np.stack([L(g.risco+g.queda12,12),L(g.com,8),L(g.light,12),np.clip((g.prob-0.07)/0.48,0,1),np.clip(g.esp/365,0,1)],1)@w,index=g.index)
A=pd.read_pickle('df.pkl'); A=A[A.cep.notna()].copy(); A['cep']=A.cep.astype('int64')
A['ini']=pd.to_datetime(A.data_inicio); A['fim']=pd.to_datetime(A.data_fim,errors='coerce')
poda=A.subtipo.str.contains('Poda'); queda=A.subtipo.eq('Retirada de árvore caída')
servedst=A.status.isin(['Fechado com solução','Fechado com providências'])
rows=[]
for T in ['2024-07-01','2024-10-01','2025-01-01','2025-04-01']:
    Tt=pd.Timestamp(T); g=O[T]; s=sc(g)
    op=A[poda&(A.ini<Tt)&((A.fim.isna())|(A.fim>Tt))&((Tt-A.ini).dt.days<=730)&~A.status.eq('Pendente')]
    op=op.assign(sv=servedst[op.index]&(op.fim<=Tt+pd.Timedelta(days=90)))
    G=op.groupby('cep').agg(n=('sv','size'),sv=('sv','mean'))
    G=G[G.n>=2]
    f=A[queda&(A.ini>Tt+pd.Timedelta(days=90))&(A.ini<=Tt+pd.Timedelta(days=365))].groupby('cep').size()
    G['q']=f.reindex(G.index,fill_value=0)>0; G['s']=s.reindex(G.index); G['T']=T
    rows.append(G)
G=pd.concat(rows); G['grp']=np.select([G.sv>=0.5,G.sv==0],['atendido (≥50% em 90 dias)','nada atendido em 90 dias'],'parcial')
G['b']=pd.cut(G.s,[0,20,40,60,101],right=False)
print(G.groupby(['b','grp'],observed=True).q.agg(['mean','size']).unstack().round(3))
print(G.groupby('grp').q.agg(['mean','size']).round(3))
