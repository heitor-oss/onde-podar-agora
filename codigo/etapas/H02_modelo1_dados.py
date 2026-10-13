"""
Árvores e rede elétrica: trechos e modelo 1 · H02 — Modelo 1: variáveis e alvo por trecho
Tipo: principal

O que faz:
    Calcula as 22 variáveis de cada trecho em uma data (histórico de poda, pendências,
    tempos, vizinhos, rua, árvore e construção do setor) e o alvo (novo Pendente em 12
    meses). Datas: treino jul/2023 e jan/2024; teste jan/2025 e jul/2025.

Lê:
    Ptr.pkl, df.pkl, setor censitário (dados_entrada)
Grava:
    m_data.pkl
Usado em:
    Modelo 1; ranking.
Script original da análise: light/m1.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json, pickle
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
P=pd.read_pickle('Ptr.pkl')
df=pd.read_pickle('df.pkl')  # all chamados with ra/bairro
df=df[df.id_logradouro.notna()&(df.numero_logradouro>0)&(df.numero_logradouro<100000)].copy()
df['tr']=df.id_logradouro.astype('int64').astype(str)+'_'+(df.numero_logradouro//100).astype('int64').astype(str)
df['lg']=df.id_logradouro.astype('int64'); df['blk']=(df.numero_logradouro//100).astype('int64')
S=pd.read_csv(SETOR).set_index('cd_setor')
df['arv']=df.cd_setor.map(S.arvore_urbana); df['constr']=df.cd_setor.map(S.construido)
df['ispoda']=df.subtipo.str.contains('Poda'); df['pend']=df.ispoda&df.status.eq('Pendente')
df['served']=df.ispoda&df.status.isin(['Fechado com solução','Fechado com providências'])
df['risk']=df.subtipo.eq('Avaliação de risco de queda da árvore'); df['queda']=df.subtipo.eq('Retirada de árvore caída'); df['remo']=df.subtipo.str.contains('Remoção')
df['vias']=df.subtipo.eq('Poda de árvore em vias públicas')
df['ouv']=df.nome_unidade_organizacional.eq('Ouvidoria COMLURB')
meta=df.groupby('tr').agg(lg=('lg','first'),blk=('blk','first'),ra=('ra',lambda s:s.mode().iloc[0] if s.notna().any() else 'NA'),
    bairro=('bairro',lambda s:s.mode().iloc[0] if s.notna().any() else ''),rua=('cep_logradouro_ref',lambda s:s.mode().iloc[0] if s.notna().any() else ''),
    arv=('arv','mean'),constr=('constr','mean'),lat=('latitude_usada','median'),lon=('longitude_usada','median'),num=('numero_logradouro','median'))
def feats(T):
    h=df[df.ini<T]; tr=meta.index
    def cnt(mask,days=None):
        x=h[mask(h)] if mask else h
        if days: x=x[x.ini>=T-pd.Timedelta(days=days)]
        return x.groupby('tr').size().reindex(tr,fill_value=0)
    F=pd.DataFrame(index=tr)
    F['poda_all']=cnt(lambda x:x.ispoda); F['poda_365']=cnt(lambda x:x.ispoda,365); F['poda_180']=cnt(lambda x:x.ispoda,180)
    F['pend_all']=cnt(lambda x:x.pend); F['pend_365']=cnt(lambda x:x.pend,365); F['pend_180']=cnt(lambda x:x.pend,180)
    F['served_all']=cnt(lambda x:x.served); F['risk']=cnt(lambda x:x.risk); F['queda']=cnt(lambda x:x.queda); F['remo']=cnt(lambda x:x.remo)
    F['vias']=cnt(lambda x:x.vias); F['ouv']=cnt(lambda x:x.ouv)
    F['rec']=h.groupby('tr').reclamacoes.sum().reindex(tr,fill_value=0)
    ls=h[h.served].groupby('tr').fim.max().reindex(tr); F['dias_ult_atend']=(T-ls).dt.days.fillna(9999)
    lr=h[h.ispoda].groupby('tr').ini.max().reindex(tr); F['dias_ult_pedido']=(T-lr).dt.days.fillna(9999)
    lp=h[h.pend].groupby('tr').ini.max().reindex(tr); F['dias_ult_pend']=(T-lp).dt.days.fillna(9999)
    # neighbours on same street: blocks +-1, and whole street
    k=meta[['lg','blk']].copy(); k['pend']=F.pend_all.values; k['poda']=F.poda_all.values
    key=dict(zip(zip(k.lg,k.blk),zip(k.pend,k.poda)))
    F['viz_pend']=[sum(key.get((l,b+d),(0,0))[0] for d in (-1,1)) for l,b in zip(k.lg,k.blk)]
    F['viz_poda']=[sum(key.get((l,b+d),(0,0))[1] for d in (-1,1)) for l,b in zip(k.lg,k.blk)]
    lgp=k.groupby('lg').pend.transform('sum')-k.pend; lgo=k.groupby('lg').poda.transform('sum')-k.poda
    F['rua_pend']=lgp.values; F['rua_poda']=lgo.values
    F['arv']=meta.arv.fillna(meta.arv.median()); F['constr']=meta.constr.fillna(meta.constr.median())
    return F
def label(T,days=365):
    f=df[(df.ini>=T)&(df.ini<T+pd.Timedelta(days=days))&df.pend]
    return f.groupby('tr').size().reindex(meta.index,fill_value=0)
origins={'tr1':pd.Timestamp('2023-07-01'),'tr2':pd.Timestamp('2024-01-01'),'te1':pd.Timestamp('2025-01-01'),'te2':pd.Timestamp('2025-07-01')}
D={}
for k,T in origins.items():
    F=feats(T); y=label(T); 
    # RA rate encoding from data before T
    D[k]=(F,y)
    print(k,T.date(),'trechos com historico',(F.poda_all+F.risk+F.queda+F.remo>0).sum(),'positivos',(y>0).sum())
pickle.dump(dict(D=D,meta=meta,origins=origins),open('m_data.pkl','wb'))
