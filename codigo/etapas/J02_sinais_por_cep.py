"""
Ranking "Onde podar agora" · J02 — Ranking: sinais por CEP
Tipo: principal

O que faz:
    Calcula por CEP: poda aberta na COMLURB (até 2 anos), pedidos Pendentes, chamados de
    risco e queda em 12 meses, espera e maior previsão do modelo.

Lê:
    df.pkl, prob_now.pkl
Grava:
    cepg.pkl
Usado em:
    Nota por CEP.
Script original da análise: light/rank2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
END=pd.Timestamp('2026-09-21')
df=pd.read_pickle('df.pkl'); df=df[df.cep.notna()].copy(); df['cep']=df.cep.astype('int64')
df['ini']=pd.to_datetime(df.data_inicio); df['age']=(END-df.ini).dt.days
poda=df.subtipo.str.contains('Poda'); opn=df.status.isin(['Aberto','Em Andamento'])
riskq=df.subtipo.isin(['Avaliação de risco de queda da árvore','Retirada de árvore caída'])|df.subtipo.str.contains('Remoção')
g=pd.DataFrame(index=df.cep.unique())
g['comlurb']=df[poda&opn&(df.age<=730)].groupby('cep').size()
g['light']=df[poda&df.status.eq('Pendente')].groupby('cep').size()
g['light_rec']=df[poda&df.status.eq('Pendente')&(df.age<=365)].groupby('cep').size()
g['risco12']=df[riskq&(df.age<=365)].groupby('cep').size()
g['queda12']=df[df.subtipo.eq('Retirada de árvore caída')&(df.age<=365)].groupby('cep').size()
g=g.fillna(0)
ab=df[poda&((opn&(df.age<=730))|df.status.eq('Pendente'))]
g['espera']=ab.groupby('cep').age.max(); g['espera_com']=df[poda&opn&(df.age<=730)].groupby('cep').age.max()
pr=pd.read_pickle('prob_now.pkl').dropna(); pr['cep']=pr.cep.astype('int64')
g['prob']=pr.groupby('cep').prob.max()
g=g.fillna(0)
act=g[(g.comlurb+g.light+g.risco12)>0]
print(len(g),len(act))
for c in ['comlurb','light','light_rec','risco12','queda12','espera','espera_com','prob']:
    v=act[c][act[c]>0]; print(c,len(v),v.quantile([.5,.9,.95,.99]).round(2).tolist(),v.max())
g.to_pickle('cepg.pkl')
